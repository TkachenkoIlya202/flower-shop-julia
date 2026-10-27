from django.apps import AppConfig


class ShopConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shop'
    verbose_name = 'Управление бутиком флористики'

    def ready(self):
        # Register signals for email notifications on order creation
        import shop.signals  # noqa
