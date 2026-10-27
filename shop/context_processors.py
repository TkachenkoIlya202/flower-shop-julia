from .cart import Cart


def cart_context(request):
    """
    Контекстный процессор для внедрения корзины во все шаблоны сайта.
    """
    return {
        'cart': Cart(request)
    }
