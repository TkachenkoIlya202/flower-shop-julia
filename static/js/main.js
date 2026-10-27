/**
 * Цветочный магазин «Julia» — Клиентские скрипты
 * Обработка AJAX-запросов к корзине, форматирование телефона и стандартные уведомления.
 */

document.addEventListener('DOMContentLoaded', () => {
    initAddToCartButtons();
    initCartItemActions();
    initPhoneFormatting();
});

/**
 * Получение CSRF токена из cookies для безопасных AJAX-запросов к Django.
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Инициализация кнопок "В корзину" с AJAX.
 */
function initAddToCartButtons() {
    document.querySelectorAll('.btn-add-cart').forEach(button => {
        button.addEventListener('click', async (e) => {
            const productId = button.dataset.productId;
            if (!productId) return;

            e.preventDefault();

            const originalHtml = button.innerHTML;
            button.disabled = true;
            button.innerHTML = `<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span> Добавляем...`;

            try {
                const response = await fetch(`/cart/add/${productId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({ quantity: 1 })
                });

                const data = await response.json();

                if (response.ok && data.success) {
                    updateCartBadge(data.total_items, data.total_price);
                    showToast(data.message || 'Букет добавлен в корзину', 'success');

                    button.classList.remove('btn-success', 'btn-outline-success');
                    button.classList.add('btn-secondary');
                    button.innerHTML = `<i class="bi bi-check2 me-1"></i> Добавлено`;

                    setTimeout(() => {
                        button.classList.remove('btn-secondary');
                        button.classList.add('btn-success');
                        button.innerHTML = originalHtml;
                        button.disabled = false;
                    }, 1400);
                } else {
                    showToast(data.error || 'Ошибка при добавлении', 'danger');
                    button.innerHTML = originalHtml;
                    button.disabled = false;
                }
            } catch (err) {
                console.error('Add to cart error:', err);
                showToast('Ошибка соединения с сервером', 'danger');
                button.innerHTML = originalHtml;
                button.disabled = false;
            }
        });
    });
}

/**
 * Обновление счетчика товаров и суммы в шапке.
 */
function updateCartBadge(count, total) {
    const badge = document.querySelector('.cart-badge');
    const totalEl = document.querySelector('.cart-total-text');

    if (badge) {
        badge.textContent = count;
        badge.style.display = count > 0 ? 'inline-block' : 'none';
    }

    if (totalEl && total !== undefined) {
        totalEl.textContent = `${Math.round(total).toLocaleString('ru-RU')} ₽`;
    }
}

/**
 * Интерактивные действия на странице корзины (изменение количества, удаление).
 */
function initCartItemActions() {
    // Изменение количества (+ / -)
    document.querySelectorAll('.qty-change-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const productId = btn.dataset.productId;
            const action = btn.dataset.action;
            const qtyInput = document.querySelector(`.qty-input-${productId}`);
            if (!qtyInput) return;

            let currentQty = parseInt(qtyInput.value, 10) || 1;
            let newQty = action === 'plus' ? currentQty + 1 : currentQty - 1;

            if (newQty <= 0) {
                if (confirm('Удалить эту позицию из корзины?')) {
                    removeItem(productId);
                }
                return;
            }

            try {
                const response = await fetch(`/cart/update/${productId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({ quantity: newQty })
                });

                const data = await response.json();
                if (data.success) {
                    qtyInput.value = newQty;
                    const itemTotalEl = document.querySelector(`.item-total-${productId}`);
                    const cartItemData = data.cart.items.find(i => i.id == productId);
                    if (itemTotalEl && cartItemData) {
                        itemTotalEl.textContent = `${Math.round(cartItemData.total_price).toLocaleString('ru-RU')} ₽`;
                    }
                    updateCartBadge(data.total_items, data.total_price);
                    updateCartTotals(data.total_price);
                }
            } catch (err) {
                console.error(err);
            }
        });
    });

    // Удаление товара
    document.querySelectorAll('.btn-remove-item-ajax').forEach(btn => {
        btn.addEventListener('click', () => {
            const productId = btn.dataset.productId;
            removeItem(productId);
        });
    });
}

async function removeItem(productId) {
    try {
        const response = await fetch(`/cart/remove/${productId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        const data = await response.json();
        if (data.success) {
            const row = document.querySelector(`.cart-row-${productId}`);
            if (row) {
                row.remove();
                if (data.total_items === 0) {
                    location.reload();
                }
            }
            updateCartBadge(data.total_items, data.total_price);
            updateCartTotals(data.total_price);
            showToast(data.message, 'info');
        }
    } catch (err) {
        console.error(err);
    }
}

function updateCartTotals(totalPrice) {
    document.querySelectorAll('.cart-summary-total').forEach(el => {
        el.textContent = `${Math.round(totalPrice).toLocaleString('ru-RU')} ₽`;
    });
}

/**
 * Простое стандартное всплывающее уведомление Bootstrap.
 */
function showToast(message, type = 'success') {
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
    }

    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-bg-${type} border-0 show shadow-sm`;
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body small">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

    container.appendChild(toastEl);

    setTimeout(() => {
        toastEl.classList.remove('show');
        setTimeout(() => toastEl.remove(), 300);
    }, 2800);
}

/**
 * Автоформатирование российского телефонного номера (+7 (XXX) XXX-XX-XX).
 */
function initPhoneFormatting() {
    const phoneInput = document.getElementById('customer_phone');
    if (!phoneInput) return;

    phoneInput.addEventListener('input', (e) => {
        let val = e.target.value.replace(/\D/g, '');
        if (val.startsWith('7') || val.startsWith('8')) {
            val = val.substring(1);
        }

        let formatted = '+7';
        if (val.length > 0) formatted += ' (' + val.substring(0, 3);
        if (val.length >= 4) formatted += ') ' + val.substring(3, 6);
        if (val.length >= 7) formatted += '-' + val.substring(6, 8);
        if (val.length >= 9) formatted += '-' + val.substring(8, 10);

        e.target.value = formatted;
    });
}
