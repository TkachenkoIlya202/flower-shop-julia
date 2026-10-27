import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from .models import Order

logger = logging.getLogger(__name__)


def send_new_order_email(order_id):
    """
    Формирует и отправляет E-mail уведомление менеджеру о новом заказе.
    Использует django.core.mail.send_mail.
    """
    try:
        order = Order.objects.prefetch_related('items__product').get(id=order_id)
    except Order.DoesNotExist:
        logger.error(f"Не удалось отправить уведомление: Заказ #{order_id} не найден.")
        return

    subject = f"🌸 Новый заказ #{order.id} на сумму {order.total_price:,.0f} ₽ — Магазин цветов «Julia»"

    # Формируем список позиций в заказе
    items_lines = []
    for item in order.items.all():
        items_lines.append(
            f"  • {item.product.title} — {item.quantity} шт. × {item.price:,.0f} ₽ = {item.get_cost():,.0f} ₽"
        )

    items_text = "\n".join(items_lines) if items_lines else "  (Состав уточняется у клиента)"

    address_text = order.address if order.address else "Не указан (уточнить при подтверждении)"
    card_text = order.card_message if order.card_message else "Без открытки"

    message = f"""Здравствуйте!

В цветочном магазине «Julia» оформлен новый заказ!
Главный флорист: Ткаченко Юлия Геннадьевна

ДЕТАЛИ ЗАКАЗА #{order.id}:
--------------------------------------------------
Клиент: {order.customer_name}
Телефон: {order.phone}
Адрес доставки: {address_text}
Текст открытки: {card_text}
Статус: {order.status}
Дата оформления: {order.created_at.strftime('%d.%m.%Y в %H:%M')}

СОСТАВ ЗАКАЗА:
--------------------------------------------------
{items_text}

ИТОГО К ОПЛАТЕ: {order.total_price:,.2f} ₽
--------------------------------------------------

Пожалуйста, свяжитесь с клиентом для подтверждения заказа.
Ссылка на заказ в панели управления:
http://127.0.0.1:8000/admin/shop/order/{order.id}/change/

С уважением,
Цветочный магазин «Julia»
Главный флорист: Ткаченко Юлия Геннадьевна
"""

    html_message = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #f8f9fa; padding: 25px; border-radius: 8px; border: 1px solid #dee2e6;">
        <div style="text-align: center; border-bottom: 2px solid #198754; padding-bottom: 15px; margin-bottom: 20px;">
            <h1 style="color: #198754; margin: 0; font-size: 24px;">Цветочный магазин «Julia»</h1>
            <p style="color: #6c757d; margin: 5px 0 0 0; font-size: 13px;">Главный флорист: Ткаченко Юлия Геннадьевна</p>
        </div>

        <h2 style="color: #212529; font-size: 18px; margin-top: 0;">Поступил новый заказ #{order.id}</h2>

        <div style="background: #ffffff; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #2F5245; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
            <p style="margin: 6px 0;"><strong>Клиент:</strong> {order.customer_name}</p>
            <p style="margin: 6px 0;"><strong>Телефон:</strong> <a href="tel:{order.phone}" style="color: #2F5245; font-weight: bold;">{order.phone}</a></p>
            <p style="margin: 6px 0;"><strong>Адрес:</strong> {address_text}</p>
            <p style="margin: 6px 0;"><strong>Текст открытки:</strong> <em>«{card_text}»</em></p>
            <p style="margin: 6px 0;"><strong>Статус:</strong> <span style="background: #E8EFEA; color: #2F5245; padding: 3px 8px; border-radius: 6px; font-size: 13px;">{order.status}</span></p>
        </div>

        <h3 style="color: #2F5245; font-size: 16px; margin-bottom: 10px;">Состав букета / заказа:</h3>
        <table style="width: 100%; border-collapse: collapse; background: #ffffff; border-radius: 8px; overflow: hidden; margin-bottom: 20px;">
            <thead>
                <tr style="background: #2F5245; color: #ffffff; text-align: left; font-size: 13px;">
                    <th style="padding: 10px 14px;">Товар</th>
                    <th style="padding: 10px 14px; text-align: center;">Кол-во</th>
                    <th style="padding: 10px 14px; text-align: right;">Сумма</th>
                </tr>
            </thead>
            <tbody>
                {''.join(f'''<tr style="border-bottom: 1px solid #F0ECE6;">
                    <td style="padding: 10px 14px; color: #333;">{item.product.title}</td>
                    <td style="padding: 10px 14px; text-align: center; color: #666;">{item.quantity} шт.</td>
                    <td style="padding: 10px 14px; text-align: right; font-weight: bold; color: #2F5245;">{item.get_cost():,.0f} ₽</td>
                </tr>''' for item in order.items.all())}
            </tbody>
            <tfoot>
                <tr style="background: #F8F5F0;">
                    <td colspan="2" style="padding: 12px 14px; font-weight: bold; font-size: 15px;">Итого к оплате:</td>
                    <td style="padding: 12px 14px; text-align: right; font-weight: bold; font-size: 18px; color: #2F5245;">{order.total_price:,.2f} ₽</td>
                </tr>
            </tfoot>
        </table>

        <div style="text-align: center; margin-top: 25px;">
            <a href="http://127.0.0.1:8000/admin/shop/order/{order.id}/change/" style="display: inline-block; background: #2F5245; color: #ffffff; text-decoration: none; padding: 12px 28px; border-radius: 25px; font-weight: 500; font-size: 14px; letter-spacing: 0.5px;">Перейти к заказу в панели управления</a>
        </div>
    </div>
    """

    manager_email = getattr(settings, 'MANAGER_EMAIL', 'tkachenko.ilya.00@mail.ru')
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'tkachenko.ilya.00@mail.ru')

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[manager_email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Уведомление о заказе #{order.id} успешно отправлено на {manager_email}")
    except Exception as exc:
        logger.error(f"Ошибка при отправке E-mail менеджеру по заказу #{order.id}: {exc}")


@receiver(post_save, sender=Order)
def order_post_save_receiver(sender, instance, created, **kwargs):
    """
    Сигнал post_save для модели Order.
    При создании нового заказа (created=True) генерирует и отправляет E-mail уведомление менеджеру.
    Использует transaction.on_commit, чтобы все связанные OrderItem успели сохраниться.
    """
    if created:
        order_id = instance.id
        # Если находимся внутри транзакции (например, при оформлении checkout_view),
        # откладываем отправку до фиксации транзакции, чтобы успели создаться OrderItem.
        connection = transaction.get_connection()
        if connection.in_atomic_block:
            transaction.on_commit(lambda: send_new_order_email(order_id))
        else:
            send_new_order_email(order_id)
