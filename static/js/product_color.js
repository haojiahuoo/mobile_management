// static/admin/js/product_color.js

document.addEventListener('DOMContentLoaded', function() {
    const colorSelect = document.getElementById('id_color');
    const colorHexInput = document.getElementById('id_color_hex');
    const colorPreview = document.createElement('div');
    
    if (colorSelect && colorHexInput) {
        // 添加颜色预览
        colorPreview.style.width = '30px';
        colorPreview.style.height = '30px';
        colorPreview.style.borderRadius = '4px';
        colorPreview.style.border = '1px solid #ddd';
        colorPreview.style.marginLeft = '10px';
        colorPreview.style.display = 'inline-block';
        colorPreview.style.verticalAlign = 'middle';
        
        colorSelect.parentNode.appendChild(colorPreview);
        
        // 更新颜色预览
        function updateColorPreview() {
            const selectedColor = colorSelect.value;
            const hexValue = colorHexInput.value;
            
            if (hexValue && hexValue.match(/^#[0-9A-Fa-f]{6}$/)) {
                colorPreview.style.backgroundColor = hexValue;
            } else if (selectedColor === 'black') {
                colorPreview.style.backgroundColor = '#000000';
                colorHexInput.value = '#000000';
            } else if (selectedColor === 'white') {
                colorPreview.style.backgroundColor = '#FFFFFF';
                colorHexInput.value = '#FFFFFF';
            } else if (selectedColor === 'red') {
                colorPreview.style.backgroundColor = '#FF0000';
                colorHexInput.value = '#FF0000';
            } else if (selectedColor === 'blue') {
                colorPreview.style.backgroundColor = '#0000FF';
                colorHexInput.value = '#0000FF';
            } else if (selectedColor === 'green') {
                colorPreview.style.backgroundColor = '#00FF00';
                colorHexInput.value = '#00FF00';
            } else if (selectedColor === 'yellow') {
                colorPreview.style.backgroundColor = '#FFFF00';
                colorHexInput.value = '#FFFF00';
            } else if (selectedColor === 'purple') {
                colorPreview.style.backgroundColor = '#800080';
                colorHexInput.value = '#800080';
            } else if (selectedColor === 'pink') {
                colorPreview.style.backgroundColor = '#FFC0CB';
                colorHexInput.value = '#FFC0CB';
            } else if (selectedColor === 'gold') {
                colorPreview.style.backgroundColor = '#FFD700';
                colorHexInput.value = '#FFD700';
            } else if (selectedColor === 'silver') {
                colorPreview.style.backgroundColor = '#C0C0C0';
                colorHexInput.value = '#C0C0C0';
            } else if (selectedColor === 'gray') {
                colorPreview.style.backgroundColor = '#808080';
                colorHexInput.value = '#808080';
            } else if (selectedColor === 'orange') {
                colorPreview.style.backgroundColor = '#FFA500';
                colorHexInput.value = '#FFA500';
            } else if (selectedColor === 'brown') {
                colorPreview.style.backgroundColor = '#8B4513';
                colorHexInput.value = '#8B4513';
            } else if (selectedColor === 'custom') {
                // 自定义颜色，使用已有的hex值或默认
                if (colorHexInput.value) {
                    colorPreview.style.backgroundColor = colorHexInput.value;
                }
            } else {
                colorPreview.style.backgroundColor = '#FFFFFF';
                colorHexInput.value = '';
            }
        }
        
        colorSelect.addEventListener('change', updateColorPreview);
        colorHexInput.addEventListener('input', function() {
            if (this.value.match(/^#[0-9A-Fa-f]{6}$/)) {
                colorPreview.style.backgroundColor = this.value;
            }
        });
        
        updateColorPreview();
    }
});