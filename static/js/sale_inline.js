// inventory/static/js/sale_inline.js
(function($) {
    $(document).ready(function() {
        function calculateRow(row) {
            var quantity = parseFloat(row.find('.field-quantity input').val()) || 0;
            var unit_price = parseFloat(row.find('.field-unit_price input').val()) || 0;
            var subtotal = quantity * unit_price;
            row.find('.field-subtotal p').text(subtotal.toFixed(2));
            return subtotal;
        }
        
        function calculateTotal() {
            var total = 0;
            $('.field-subtotal p').each(function() {
                var val = parseFloat($(this).text());
                if (!isNaN(val)) total += val;
            });
            $('#id_total_amount').val(total.toFixed(2));
            return total;
        }
        
        function bindEvents() {
            $('.field-quantity input, .field-unit_price input').off('input').on('input', function() {
                var row = $(this).closest('tr');
                calculateRow(row);
                calculateTotal();
            });
        }
        
        bindEvents();
        $(document).on('click', '.add-row', function() {
            setTimeout(function() {
                bindEvents();
                calculateTotal();
            }, 200);
        });
        $(document).on('click', '.delete-row', function() {
            setTimeout(calculateTotal, 100);
        });
        calculateTotal();
    });
})(jQuery);