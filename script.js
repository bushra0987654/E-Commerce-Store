/* ============================================================
   Custom JavaScript for SimpleShop
   ============================================================ */

document.addEventListener('DOMContentLoaded', function () {

    // Auto-dismiss Bootstrap alerts after 4 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) bsAlert.close();
        }, 4000);
    });

    // Prevent quantity inputs from going below 1 or above their max
    const quantityInputs = document.querySelectorAll('input[type="number"][name="quantity"]');
    quantityInputs.forEach(function (input) {
        input.addEventListener('change', function () {
            const min = parseInt(input.min) || 1;
            const max = input.max ? parseInt(input.max) : Infinity;
            let value = parseInt(input.value) || min;
            if (value < min) value = min;
            if (value > max) value = max;
            input.value = value;
        });
    });

    // Simple client-side confirmation for destructive cart actions
    const emptyCartForm = document.querySelector('form[action*="empty"]');
    if (emptyCartForm) {
        emptyCartForm.addEventListener('submit', function (e) {
            if (!confirm('Are you sure you want to empty your cart?')) {
                e.preventDefault();
            }
        });
    }

});
