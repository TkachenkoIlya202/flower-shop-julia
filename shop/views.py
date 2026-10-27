import json
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from decimal import Decimal

from .models import Category, Product, Order, OrderItem
from .forms import OrderCreateForm, CartAddProductForm
from .cart import Cart


@ensure_csrf_cookie
def catalog_view(request, category_slug=None):
    """
    Главная страница / Каталог:
    - Вывод категорий
    - Динамический вывод букетов и товаров из БД (только в наличии in_stock > 0)
    - Поиск по названию/описанию
    - Фильтрация по категориям и сортировка
    """
    category = None
    categories = Category.objects.all()
    products = Product.objects.available().select_related('category')

    # Фильтрация по категории
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    # Поиск по каталогу
    search_query = request.GET.get('q', '').strip()
    if search_query:
        products = products.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(composition__icontains=search_query)
        )

    # Сортировка
    sort_by = request.GET.get('sort', 'featured')
    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    else:
        products = products.order_by('-is_featured', '-created_at')

    context = {
        'category': category,
        'categories': categories,
        'products': products,
        'search_query': search_query,
        'sort_by': sort_by,
        'total_products': products.count(),
        'checkout_form': OrderCreateForm(),
    }
    return render(request, 'shop/index.html', context)


@ensure_csrf_cookie
def product_detail_view(request, id, slug):
    """Страница отдельного букета с полным описанием и составом."""
    product = get_object_or_404(Product, id=id, slug=slug)
    related_products = Product.objects.available().filter(
        category=product.category
    ).exclude(id=product.id)[:4]

    cart_form = CartAddProductForm()

    context = {
        'product': product,
        'related_products': related_products,
        'cart_form': cart_form,
    }
    return render(request, 'shop/product_detail.html', context)


@require_POST
def cart_add_view(request, product_id):
    """
    Добавление товара в корзину:
    Поддерживает как классический POST-запрос, так и AJAX JSON-запрос для интерактивного UI.
    """
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)

    # Проверка наличия
    if product.in_stock <= 0:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'success': False, 'error': 'Товар закончился'}, status=400)
        messages.error(request, 'К сожалению, этого букета сейчас нет в наличии.')
        return redirect('shop:catalog')

    quantity = 1
    override = False

    # Обработка JSON payload или form-data
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
            quantity = int(data.get('quantity', 1))
            override = bool(data.get('override', False))
        except (ValueError, TypeError):
            quantity = 1
    else:
        form = CartAddProductForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            quantity = cd['quantity']
            override = cd['override']

    cart.add(product=product, quantity=quantity, override_quantity=override)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({
            'success': True,
            'message': f'Букет «{product.title}» добавлен в корзину',
            'product_title': product.title,
            'total_items': len(cart),
            'total_price': float(cart.get_total_price()),
            'cart': cart.to_dict(),
        })

    messages.success(request, f'Букет «{product.title}» успешно добавлен в корзину.')
    return redirect('shop:cart_detail')


@require_POST
def cart_remove_view(request, product_id):
    """Удаление товара из корзины."""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({
            'success': True,
            'message': f'«{product.title}» удален из корзины',
            'total_items': len(cart),
            'total_price': float(cart.get_total_price()),
            'cart': cart.to_dict(),
        })

    messages.info(request, f'Товар «{product.title}» удален из корзины.')
    return redirect('shop:cart_detail')


@require_POST
def cart_update_view(request, product_id):
    """Обновление количества позиции в корзине."""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)

    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            quantity = int(data.get('quantity', 1))
        else:
            quantity = int(request.POST.get('quantity', 1))
    except (ValueError, TypeError):
        quantity = 1

    cart.update(product, quantity)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({
            'success': True,
            'total_items': len(cart),
            'total_price': float(cart.get_total_price()),
            'cart': cart.to_dict(),
        })

    return redirect('shop:cart_detail')


@ensure_csrf_cookie
def cart_detail_view(request):
    """Страница корзины и оформления заказа."""
    cart = Cart(request)
    form = OrderCreateForm()
    return render(request, 'shop/cart.html', {'cart': cart, 'form': form})


def checkout_view(request):
    """
    Оформление заказа:
    - Валидация полей «Имя» и «Телефон»
    - Сохранение заказа и позиций OrderItem в БД
    - Авто-снятие остатков
    - Очистка корзины сессии
    - Перенаправление на страницу успешного заказа
    """
    cart = Cart(request)
    if len(cart) == 0:
        messages.warning(request, 'Ваша корзина пуста. Выберите букет из каталога.')
        return redirect('shop:catalog')

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # Создаем заказ в БД
                order = form.save(commit=False)
                order.total_price = cart.get_total_price()
                order.save()

                # Создаем позиции OrderItem и списываем остаток
                for item in cart:
                    product = item['product']
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        price=item['price'],
                        quantity=item['quantity']
                    )
                    # Уменьшаем остаток на складе
                    if product.in_stock >= item['quantity']:
                        product.in_stock -= item['quantity']
                    else:
                        product.in_stock = 0
                    product.save(update_fields=['in_stock'])

            # Очищаем корзину
            cart.clear()

            # Сохраняем ID заказа в сессии для страницы благодарности
            request.session['last_order_id'] = order.id

            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({
                    'success': True,
                    'order_id': order.id,
                    'redirect_url': f'/order/success/{order.id}/',
                })

            return redirect('shop:order_success', order_id=order.id)
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    else:
        form = OrderCreateForm()

    return render(request, 'shop/checkout.html', {'cart': cart, 'form': form})


def order_success_view(request, order_id):
    """Страница подтверждения заказа."""
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'shop/order_success.html', {'order': order})


def cart_api_view(request):
    """API-эндпоинт для получения текущего состояния корзины (для динамических виджетов)."""
    cart = Cart(request)
    return JsonResponse(cart.to_dict())
