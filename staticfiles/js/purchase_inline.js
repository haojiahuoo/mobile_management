// inventory/static/js/purchase_inline.js
(function($) {
    $(document).ready(function() {
        // 计算单行小计
        function calculateRow(row) {
            var quantity = parseFloat($(row).find('.field-quantity input').val()) || 0;
            var unit_price = parseFloat($(row).find('.field-unit_price input').val()) || 0;
            var subtotal = quantity * unit_price;
            
            // 小计是 <p> 标签，不是 input
            var subtotalElement = $(row).find('.field-subtotal p');
            if (subtotalElement.length) {
                subtotalElement.text(subtotal.toFixed(2));
            }
            
            return subtotal;
        }
        
        // 计算总金额
        function calculateTotal() {
            var total = 0;
            // 遍历所有小计的 <p> 标签
            $('.field-subtotal p').each(function() {
                var val = parseFloat($(this).text());
                if (!isNaN(val)) {
                    total += val;
                }
            });
            
            // 更新总额字段
            var totalField = $('#id_total_amount');
            if (totalField.length) {
                totalField.val(total.toFixed(2));
            }
            return total;
        }
        
        // 绑定事件
        function bindEvents() {
            $('.field-quantity input, .field-unit_price input').off('input').on('input', function() {
                var row = $(this).closest('tr');
                calculateRow(row);
                calculateTotal();
            });
        }
        
        bindEvents();
        
        // 监听动态添加的行
        $(document).on('click', '.add-row', function() {
            setTimeout(function() {
                bindEvents();
                calculateTotal();
            }, 200);
        });
        
        $(document).on('click', '.delete-row', function() {
            setTimeout(calculateTotal, 100);
        });
        
        // 初始化计算
        calculateTotal();
    });
})(jQuery);