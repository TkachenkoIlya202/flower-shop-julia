from django.db import models
from django.utils.text import slugify
from decimal import Decimal


class Category(models.Model):
    """
    Категории цветов и сопутствующих товаров:
    - Монобукеты (розы, хризантемы и др.)
    - Авторские композиции
    - Сопутствующие подарки и услуги (упаковка, воздушные шары)
    """
    name = models.CharField(max_length=150, verbose_name="Название категории")
    slug = models.SlugField(max_length=150, unique=True, verbose_name="URL-слаг")
    description = models.TextField(blank=True, verbose_name="Описание")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ProductQuerySet(models.QuerySet):
    def available(self):
        """Возвращает только товары, которые есть в наличии (остаток > 0)."""
        return self.filter(in_stock__gt=0)


class Product(models.Model):
    """
    Товары / Премиальные букеты:
    title, price, image, category, in_stock (Integer для авто-снятия с публикации при 0).
    """
    category = models.ForeignKey(
        Category,
        related_name='products',
        on_delete=models.CASCADE,
        verbose_name="Категория"
    )
    title = models.CharField(max_length=200, verbose_name="Название букета / товара")
    slug = models.SlugField(max_length=200, unique=True, blank=True, verbose_name="URL-слаг")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена (₽)")
    image = models.ImageField(upload_to='products/%Y/%m/%d', blank=True, null=True, verbose_name="Фотография")
    image_url_fallback = models.URLField(blank=True, verbose_name="Внешняя ссылка на фото (резерв)")
    description = models.TextField(blank=True, verbose_name="Описание композиции")
    composition = models.CharField(max_length=255, blank=True, verbose_name="Состав букета")
    in_stock = models.IntegerField(default=10, verbose_name="Количество в наличии (шт)")
    is_featured = models.BooleanField(default=False, verbose_name="Выбор флориста (хит)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = "Букет / Товар"
        verbose_name_plural = "Букеты и товары"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} — {self.price:,.0f} ₽"

    @property
    def is_available(self):
        """Проверка наличия (автоматическое снятие при 0)."""
        return self.in_stock > 0

    @property
    def display_image(self):
        """Возвращает URL изображения: загруженное медиа либо стильный fallback."""
        if self.image:
            return self.image.url
        if self.image_url_fallback:
            return self.image_url_fallback
        return "/static/images/placeholder-bouquet.svg"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title) or f"product-{self.pk or ''}"
        super().save(*args, **kwargs)


class Order(models.Model):
    """
    Заказы:
    id, customer_name, phone, total_price, created_at, status
    """
    STATUS_NEW = 'Новый'
    STATUS_ASSEMBLY = 'В сборке'
    STATUS_COURIER = 'Передан курьеру'
    STATUS_DELIVERED = 'Доставлен'

    STATUS_CHOICES = [
        (STATUS_NEW, 'Новый'),
        (STATUS_ASSEMBLY, 'В сборке'),
        (STATUS_COURIER, 'Передан курьеру'),
        (STATUS_DELIVERED, 'Доставлен'),
    ]

    customer_name = models.CharField(max_length=150, verbose_name="Имя клиента")
    phone = models.CharField(max_length=30, verbose_name="Номер телефона")
    address = models.CharField(max_length=255, blank=True, verbose_name="Адрес доставки")
    card_message = models.TextField(blank=True, verbose_name="Текст фирменной открытки")
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Итоговая сумма (₽)"
    )
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default=STATUS_NEW,
        verbose_name="Статус заказа"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата изменения")

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-created_at']

    def __str__(self):
        return f"Заказ #{self.id} от {self.customer_name} ({self.status}) — {self.total_price:,.0f} ₽"

    def calculate_total(self):
        """Пересчет общей суммы заказа по позициям."""
        total = sum(item.get_cost() for item in self.items.all())
        self.total_price = total
        self.save(update_fields=['total_price'])
        return total


class OrderItem(models.Model):
    """
    Позиции в заказе:
    order (ForeignKey), product (ForeignKey), quantity (Integer)
    """
    order = models.ForeignKey(
        Order,
        related_name='items',
        on_delete=models.CASCADE,
        verbose_name="Заказ"
    )
    product = models.ForeignKey(
        Product,
        related_name='order_items',
        on_delete=models.CASCADE,
        verbose_name="Букет / Товар"
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество (шт)")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена за единицу (₽)")

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"

    def __str__(self):
        return f"{self.quantity} шт. × {self.product.title}"

    def get_cost(self):
        return Decimal(self.price) * self.quantity
