import re
from django import forms
from .models import Order


class OrderCreateForm(forms.ModelForm):
    """
    Форма оформления заказа с валидацией имени и номера телефона (Bootstrap 5).
    """
    customer_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Как к вам обращаться (например, Анна)',
            'id': 'customer_name',
            'autocomplete': 'name',
        }),
        label='Ваше имя'
    )

    phone = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+7 (999) 000-00-00',
            'id': 'customer_phone',
            'autocomplete': 'tel',
        }),
        label='Номер телефона'
    )

    address = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Город, улица, дом, квартира (или самовывоз)',
            'id': 'customer_address',
        }),
        label='Адрес доставки'
    )

    card_message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Текст для бесплатной поздравительной открытки...',
            'id': 'customer_card_message',
        }),
        label='Текст открытки'
    )

    class Meta:
        model = Order
        fields = ['customer_name', 'phone', 'address', 'card_message']

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        digits = re.sub(r'\D', '', phone)
        if len(digits) < 10:
            raise forms.ValidationError("Пожалуйста, укажите корректный номер телефона (не менее 10 цифр).")
        return phone


class CartAddProductForm(forms.Form):
    """Форма добавления товара с указанием количества."""
    quantity = forms.IntegerField(
        min_value=1,
        max_value=20,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-sm text-center', 'min': '1', 'max': '20'})
    )
    override = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.HiddenInput
    )
