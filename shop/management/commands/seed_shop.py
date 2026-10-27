from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal
from shop.models import Category, Product

User = get_user_model()


class Command(BaseCommand):
    help = "Наполняет базу данных первоначальными категориями и товарами магазина цветов «Julia»."

    def handle(self, *args, **options):
        self.stdout.write("Создание категорий цветов и сопутствующих товаров для магазина «Julia»...")

        cat_mono, _ = Category.objects.get_or_create(
            slug="monobukety",
            defaults={
                "name": "Монобукеты (розы, хризантемы)",
                "description": "Классические букеты из одного вида свежих цветов: розы, хризантемы, тюльпаны."
            }
        )

        cat_author, _ = Category.objects.get_or_create(
            slug="avtorskie-kompozicii",
            defaults={
                "name": "Авторские композиции",
                "description": "Авторские букеты и композиции в коробках, собранные главным флористом Ткаченко Юлией Геннадьевной."
            }
        )

        cat_services, _ = Category.objects.get_or_create(
            slug="podarki-i-uslugi",
            defaults={
                "name": "Сопутствующие подарки и услуги",
                "description": "Красивая подарочная упаковка, гелиевые воздушные шары и поздравительные открытки."
            }
        )

        products_data = [
            # 1. Монобукеты
            {
                "category": cat_mono,
                "title": "Монобукет из 25 роз Охара",
                "slug": "ohara-roses-25",
                "price": Decimal("8900.00"),
                "in_stock": 12,
                "is_featured": True,
                "composition": "25 садовых роз White O'Hara, шелковая лента",
                "description": "Нежные французские розы с тонким приятным ароматом. Собрано флористом Ткаченко Юлией Геннадьевной.",
                "image_url_fallback": "https://images.unsplash.com/photo-1561181286-d3fee7d55364?auto=format&fit=crop&w=800&q=80",
            },
            {
                "category": cat_mono,
                "title": "Букет кустовых хризантем",
                "slug": "chrysanthemum-bouquet",
                "price": Decimal("4500.00"),
                "in_stock": 15,
                "is_featured": False,
                "composition": "9 пышных веток хризантем, крафтовая бумага, атласная лента",
                "description": "Стойкие и свежие хризантемы. Стоят в вазе до трех недель.",
                "image_url_fallback": "https://images.unsplash.com/photo-1508610048659-a06b669e3321?auto=format&fit=crop&w=800&q=80",
            },
            {
                "category": cat_mono,
                "title": "Монобукет из 35 коралловых роз",
                "slug": "coral-roses-35",
                "price": Decimal("11500.00"),
                "in_stock": 7,
                "is_featured": True,
                "composition": "35 коралловых роз премиум сорта Kahala, атласная лента",
                "description": "Яркий и выразительный букет из свежих роз персиково-кораллового оттенка.",
                "image_url_fallback": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=800&q=80",
            },
            {
                "category": cat_mono,
                "title": "Букет белых роз Mondial",
                "slug": "white-roses-mondial",
                "price": Decimal("6400.00"),
                "in_stock": 10,
                "is_featured": False,
                "composition": "19 белых роз Mondial высотой 60 см, матовая бумага",
                "description": "Элегантный монобукет из белоснежных роз с крупным бутоном.",
                "image_url_fallback": "https://images.unsplash.com/photo-1533616688419-b7a585564566?auto=format&fit=crop&w=800&q=80",
            },
            # 2. Авторские композиции
            {
                "category": cat_author,
                "title": "Авторский букет «Нежное утро»",
                "slug": "gentle-morning-bouquet",
                "price": Decimal("7800.00"),
                "in_stock": 8,
                "is_featured": True,
                "composition": "Пионы, кустовые розы, эвкалипт, озотамнус",
                "description": "Фирменная композиция от главного флориста Ткаченко Юлии Геннадьевны. Нежная цветовая гамма и гармоничное сочетание цветов.",
                "image_url_fallback": "https://images.unsplash.com/photo-1526047932273-341f2a7631f9?auto=format&fit=crop&w=800&q=80",
            },
            {
                "category": cat_author,
                "title": "Композиция в шляпной коробке",
                "slug": "hatbox-flower-arrangement",
                "price": Decimal("9200.00"),
                "in_stock": 5,
                "is_featured": True,
                "composition": "Гортензия, пионовидные розы, эустома, зелень, шляпная коробка",
                "description": "Цветы собраны на флористической губке с водой. Удобно дарить и легко ухаживать.",
                "image_url_fallback": "https://images.unsplash.com/photo-1582794543139-8ac9cb0f7b11?auto=format&fit=crop&w=800&q=80",
            },
            {
                "category": cat_author,
                "title": "Букет «Весеннее вдохновение»",
                "slug": "spring-inspiration-bouquet",
                "price": Decimal("6900.00"),
                "in_stock": 6,
                "is_featured": False,
                "composition": "Тюльпаны, ранункулюсы, белая сирень, ветви эвкалипта",
                "description": "Легкий весенний букет с живыми красками и свежим ароматом.",
                "image_url_fallback": "https://images.unsplash.com/photo-1490750967868-88aa4486c946?auto=format&fit=crop&w=800&q=80",
            },
            # 3. Сопутствующие услуги и подарки
            {
                "category": cat_services,
                "title": "Набор гелиевых шаров (10 шт.)",
                "slug": "helium-balloons-set-10",
                "price": Decimal("2500.00"),
                "in_stock": 20,
                "is_featured": False,
                "composition": "10 шаров пастельных оттенков, ленты, грузик",
                "description": "Воздушные шары с гелием для праздничного настроения. Долго летают благодаря обработке Hi-Float.",
                "image_url_fallback": "https://images.unsplash.com/photo-1530103862676-de8c9debad1d?auto=format&fit=crop&w=800&q=80",
            },
            {
                "category": cat_services,
                "title": "Подарочная упаковка и открытка",
                "slug": "gift-wrapping-and-card",
                "price": Decimal("600.00"),
                "in_stock": 50,
                "is_featured": False,
                "composition": "Крафтовая или дизайнерская бумага, атласная лента, открытка для пожеланий",
                "description": "Аккуратное оформление букета или подарка с открыткой, подписанной от вашего имени.",
                "image_url_fallback": "https://images.unsplash.com/photo-1549465220-1a8b9238cd48?auto=format&fit=crop&w=800&q=80",
            },
        ]

        for p_data in products_data:
            Product.objects.update_or_create(
                slug=p_data["slug"],
                defaults=p_data
            )
            self.stdout.write(f"  ✓ Товар создан/обновлен: {p_data['title']}")

        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults={"email": "tkachenko.ilya.00@mail.ru", "is_staff": True, "is_superuser": True}
        )
        if created:
            admin_user.set_password("admin123")
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("✓ Создан суперпользователь: admin / admin123"))

        self.stdout.write(self.style.SUCCESS("✨ База данных магазина «Julia» успешно обновлена!"))
