from decimal import Decimal
from django.conf import settings
from .models import Product


class Cart:
    """
    Управление корзиной покупок на основе серверных сессий Django.
    В сессии хранятся только JSON-сериализуемые типы данных:
    {
        '<product_id>': {
            'quantity': 2,
            'price': '4500.00'
        }
    }
    """
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, quantity=1, override_quantity=False):
        """Добавить товар в корзину или изменить его количество."""
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.price)
            }

        if override_quantity:
            self.cart[product_id]['quantity'] = max(1, quantity)
        else:
            self.cart[product_id]['quantity'] += quantity

        self.save()

    def update(self, product, quantity):
        """Обновить точное количество товара."""
        product_id = str(product.id)
        if product_id in self.cart:
            if quantity <= 0:
                self.remove(product)
            else:
                self.cart[product_id]['quantity'] = quantity
                self.save()

    def remove(self, product):
        """Удалить товар из корзины."""
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def save(self):
        """Отметить сессию как модифицированную для сохранения изменений."""
        self.session.modified = True

    def __iter__(self):
        """
        Итератор по товарам в корзине с подгрузкой объектов моделей Product из БД.
        Создает независимые копии словарей, не мутируя сессионные данные Decimal-объектами.
        """
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        product_map = {str(p.id): p for p in products}

        for product_id, item in self.cart.items():
            if product_id in product_map:
                item_copy = dict(item)
                item_copy['product'] = product_map[product_id]
                item_copy['price'] = Decimal(item['price'])
                item_copy['total_price'] = item_copy['price'] * item_copy['quantity']
                yield item_copy

    def __len__(self):
        """Общее количество товаров в корзине."""
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        """Итоговая стоимость всех товаров в корзине."""
        return sum(
            Decimal(item['price']) * item['quantity']
            for item in self.cart.values()
        )

    def clear(self):
        """Очистить корзину из сессии."""
        if settings.CART_SESSION_ID in self.session:
            del self.session[settings.CART_SESSION_ID]
            self.save()

    def to_dict(self):
        """Возвращает сериализованный словарь для AJAX/JSON ответов."""
        items_data = []
        for item in self:
            product = item['product']
            items_data.append({
                'id': product.id,
                'title': product.title,
                'price': float(item['price']),
                'quantity': item['quantity'],
                'total_price': float(item['total_price']),
                'image': product.display_image,
            })
        return {
            'items': items_data,
            'total_items': len(self),
            'total_price': float(self.get_total_price()),
        }
