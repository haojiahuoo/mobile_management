// inventory/static/js/purchase_order.js
(function($) {
    $(document).ready(function() {
        function calculateTotal() {
            var total = 0;
            $('.field-subtotal input').each(function() {
                var val = parseFloat($(this).val());
                if (!isNaN(val)) {
                    total += val;
                }
            });
            $('#id_total_amount').val(total.toFixed(2));
        }
        
        calculateTotal();
    });
})(jQuery);