from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, Order, OrderItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'products_count')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

    def products_count(self, obj):
        return obj.products.count()
    products_count.short_description = "Кол-во товаров"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('preview_thumb', 'title', 'category', 'price_display', 'in_stock', 'is_featured', 'created_at')
    list_filter = ('category', 'is_featured', 'created_at')
    search_fields = ('title', 'description', 'composition')
    list_editable = ('in_stock', 'is_featured')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('preview_large', 'created_at', 'updated_at')

    def price_display(self, obj):
        return f"{obj.price:,.0f} ₽"
    price_display.short_description = "Цена"

    def in_stock_badge(self, obj):
        if obj.in_stock > 0:
            return format_html('<span style="color:#2F5245;font-weight:bold;">В наличии ({})</span>', obj.in_stock)
        return format_html('<span style="color:#B33939;font-weight:bold;">Снят с публикации (0)</span>')
    in_stock_badge.short_description = "Остаток"

    def preview_thumb(self, obj):
        url = obj.display_image
        if url:
            return format_html('<img src="{}" style="width:45px;height:45px;object-fit:cover;border-radius:6px;" />', url)
        return "—"
    preview_thumb.short_description = "Фото"

    def preview_large(self, obj):
        url = obj.display_image
        if url:
            return format_html('<img src="{}" style="max-width:250px;border-radius:8px;" />', url)
        return "—"
    preview_large.short_description = "Предпросмотр фото"


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    raw_id_fields = ('product',)
    readonly_fields = ('get_total',)

    def get_total(self, obj):
        return f"{obj.get_cost():,.2f} ₽" if obj.pk else "—"
    get_total.short_description = "Стоимость"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'phone', 'total_display', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('customer_name', 'phone', 'id', 'address')
    list_editable = ('status',)
    inlines = [OrderItemInline]
    readonly_fields = ('created_at', 'updated_at')

    def total_display(self, obj):
        return f"{obj.total_price:,.2f} ₽"
    total_display.short_description = "Итого"

    def status_badge(self, obj):
        colors = {
            'Новый': '#8E6B23',
            'В сборке': '#24527A',
            'Передан курьеру': '#5B3256',
            'Доставлен': '#2F5245',
        }
        color = colors.get(obj.status, '#333')
        return format_html(
            '<span style="background-color:{};color:#fff;padding:3px 8px;border-radius:12px;font-size:12px;font-weight:500;">{}</span>',
            color, obj.status
        )
    status_badge.short_description = "Статус"
