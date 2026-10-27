from django.test import TestCase, Client
from django.urls import reverse
from django.core import mail
from decimal import Decimal

from .models import Category, Product, Order, OrderItem
from .cart import Cart
from .signals import send_new_order_email


class ShopModelsTestCase(TestCase):
    """Тестирование моделей Category, Product, Order, OrderItem."""

    def setUp(self):
        self.category = Category.objects.create(
            name="Монобукеты",
            slug="monobukety",
            description="Букеты из одного вида цветов"
        )
        self.product = Product.objects.create(
            category=self.category,
            title="Букет из 25 роз Охара",
            slug="rozy-ohara-25",
            price=Decimal("6500.00"),
            in_stock=10,
            composition="25 французских роз Охара, атласная лента"
        )

    def test_category_creation_and_str(self):
        self.assertEqual(str(self.category), "Монобукеты")
        self.assertEqual(self.category.slug, "monobukety")

    def test_product_availability(self):
        self.assertTrue(self.product.is_available)
        self.assertIn(self.product, Product.objects.available())

        # Проверка авто-снятия с публикации при 0
        self.product.in_stock = 0
        self.product.save()
        self.assertFalse(self.product.is_available)
        self.assertNotIn(self.product, Product.objects.available())

    def test_order_and_order_item(self):
        order = Order.objects.create(
            customer_name="Александра",
            phone="+79991234567",
            status="Новый"
        )
        item = OrderItem.objects.create(
            order=order,
            product=self.product,
            price=self.product.price,
            quantity=2
        )
        self.assertEqual(item.get_cost(), Decimal("13000.00"))
        total = order.calculate_total()
        self.assertEqual(total, Decimal("13000.00"))
        self.assertEqual(order.total_price, Decimal("13000.00"))


class CatalogViewsTestCase(TestCase):
    """Тестирование отображения каталога и детальной страницы."""

    def setUp(self):
        self.client = Client()
        self.category_roses = Category.objects.create(name="Монобукеты", slug="monobukety")
        self.category_custom = Category.objects.create(name="Авторские композиции", slug="avtorskie-kompozicii")
        self.product1 = Product.objects.create(
            category=self.category_roses,
            title="Букет пионовидных роз",
            slug="pionovidnye-rozy",
            price=Decimal("7200.00"),
            in_stock=5
        )
        self.product2 = Product.objects.create(
            category=self.category_custom,
            title="Композиция «Шёлковый рассвет»",
            slug="shelkovyj-rassvet",
            price=Decimal("9500.00"),
            in_stock=3
        )
        # Товар с нулевым остатком (не должен отображаться в каталоге)
        self.product_out = Product.objects.create(
            category=self.category_roses,
            title="Букет тюльпанов (закончился)",
            slug="tulpany-soldout",
            price=Decimal("3000.00"),
            in_stock=0
        )

    def test_catalog_view_status_and_content(self):
        response = self.client.get(reverse('shop:catalog'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Букет пионовидных роз")
        self.assertContains(response, "Композиция «Шёлковый рассвет»")
        self.assertNotContains(response, "Букет тюльпанов (закончился)")

    def test_category_filter(self):
        response = self.client.get(reverse('shop:catalog_by_category', args=['monobukety']))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Букет пионовидных роз")
        self.assertNotContains(response, "Композиция «Шёлковый рассвет»")

    def test_product_detail_view(self):
        response = self.client.get(
            reverse('shop:product_detail', args=[self.product1.id, self.product1.slug])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product1.title)
        self.assertContains(response, "7200")


class CartAndCheckoutTestCase(TestCase):
    """Тестирование корзины сессий и процесса оформления заказа."""

    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Монобукеты", slug="monobukety")
        self.product = Product.objects.create(
            category=self.category,
            title="Белые французские розы",
            slug="belye-rozy",
            price=Decimal("5000.00"),
            in_stock=8
        )

    def test_cart_add_and_session(self):
        response = self.client.post(
            reverse('shop:cart_add', args=[self.product.id]),
            {'quantity': 2, 'override': False}
        )
        self.assertEqual(response.status_code, 302)  # Редирект в корзину

        # Проверяем страницу корзины
        response = self.client.get(reverse('shop:cart_detail'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Белые французские розы")
        self.assertContains(response, "10000")

    def test_cart_add_ajax(self):
        response = self.client.post(
            reverse('shop:cart_add', args=[self.product.id]),
            data='{"quantity": 1}',
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['total_items'], 1)
        self.assertEqual(data['total_price'], 5000.0)

    def test_cart_remove(self):
        # Добавляем товар
        self.client.post(reverse('shop:cart_add', args=[self.product.id]), {'quantity': 1})
        # Удаляем
        response = self.client.post(reverse('shop:cart_remove', args=[self.product.id]))
        self.assertEqual(response.status_code, 302)
        # Проверяем пустую корзину
        response = self.client.get(reverse('shop:cart_detail'))
        self.assertContains(response, "Ваша корзина пуста")

    def test_checkout_creates_order_and_items(self):
        # Добавляем 2 шт в корзину
        self.client.post(reverse('shop:cart_add', args=[self.product.id]), {'quantity': 2})

        # Отправляем форму оформления заказа
        checkout_data = {
            'customer_name': 'Екатерина Романова',
            'phone': '+7 (916) 123-45-67',
            'address': 'Москва, Тверской бульвар, 12, кв. 45',
            'card_message': 'С днём рождения, дорогая мама!',
        }

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(reverse('shop:checkout'), data=checkout_data)

        # Редирект на success
        self.assertEqual(response.status_code, 302)
        order = Order.objects.first()
        self.assertIsNotNone(order)
        self.assertEqual(order.customer_name, 'Екатерина Романова')
        self.assertEqual(order.phone, '+7 (916) 123-45-67')
        self.assertEqual(order.total_price, Decimal('10000.00'))
        self.assertEqual(order.items.count(), 1)

        item = order.items.first()
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.quantity, 2)

        # Проверяем списание остатка (было 8, заказали 2 -> осталось 6)
        self.product.refresh_from_db()
        self.assertEqual(self.product.in_stock, 6)

        # Проверяем, что корзина очистилась
        response = self.client.get(reverse('shop:cart_detail'))
        self.assertContains(response, "Ваша корзина пуста")


class EmailNotificationSignalTestCase(TestCase):
    """Тестирование автоматической отправки E-mail менеджеру через сигналы."""

    def setUp(self):
        mail.outbox = []
        self.category = Category.objects.create(name="Монобукеты", slug="monobukety")
        self.product = Product.objects.create(
            category=self.category,
            title="Букет пионов Сара Бернар",
            price=Decimal("8900.00"),
            in_stock=10
        )

    def test_email_sent_on_order_creation_with_commit(self):
        """Проверка, что сигнал post_save формирует и отправляет письмо менеджеру."""
        with self.captureOnCommitCallbacks(execute=True):
            order = Order.objects.create(
                customer_name="Константин",
                phone="+79250001122",
                address="Кутузовский проспект, 15",
                card_message="С любовью и нежностью",
                total_price=Decimal("8900.00")
            )
            OrderItem.objects.create(
                order=order,
                product=self.product,
                quantity=1,
                price=Decimal("8900.00")
            )

        # Проверяем отправленные письма в почтовом ящике Django
        self.assertGreaterEqual(len(mail.outbox), 1)
        email = mail.outbox[0]

        # Проверяем заголовок и получателя
        self.assertIn(f"Новый заказ #{order.id}", email.subject)
        self.assertIn("Julia", email.subject)
        self.assertEqual(email.to, ["tkachenko.ilya.00@mail.ru"])

        # Проверяем тело письма
        self.assertIn("Константин", email.body)
        self.assertIn("+79250001122", email.body)
        self.assertIn("Кутузовский проспект, 15", email.body)
        self.assertIn("8,900", email.body)
        self.assertIn(f"/admin/shop/order/{order.id}/change/", email.body)

    def test_direct_send_new_order_email_function(self):
        """Прямой тест функции отправки email на случай ручного вызова."""
        order = Order.objects.create(
            customer_name="Мария",
            phone="+79031112233",
            address="ул. Арбат, 10",
            total_price=Decimal("6500.00")
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            price=Decimal("6500.00")
        )
        send_new_order_email(order.id)
        self.assertGreaterEqual(len(mail.outbox), 1)
        self.assertIn("Мария", mail.outbox[-1].body)
