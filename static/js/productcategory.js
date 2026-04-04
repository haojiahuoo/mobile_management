// inventory/static/admin/js/productcategory.js

document.addEventListener('DOMContentLoaded', function() {
    console.log('productcategory.js 已加载');
    
    // 为每一行添加双击事件
    const rows = document.querySelectorAll('#result_list tbody tr');
    console.log('找到行数:', rows.length);
    
    rows.forEach((row, index) => {
        row.style.cursor = 'pointer';
        
        row.addEventListener('dblclick', function(e) {
            console.log('双击了第', index + 1, '行');
            
            // 获取当前行的复选框
            const checkbox = this.querySelector('.leaf-checkbox');
            if (!checkbox) {
                console.log('未找到复选框');
                return;
            }
            
            const categoryId = checkbox.getAttribute('data-id');
            const categoryName = checkbox.getAttribute('data-name');
            const isLeaf = checkbox.checked;
            
            console.log('分类ID:', categoryId, '分类名称:', categoryName, '是否叶子:', isLeaf);
            
            if (isLeaf) {
                // 勾选了"这是一个分类"：跳转到添加商品页面
                console.log('跳转到添加商品页面，分类:', categoryName);
                window.location.href = '/admin/inventory/product/add/?category=' + categoryId;
            } else {
                // 未勾选：进入子分类页面
                console.log('进入子分类页面，父级:', categoryName);
                window.location.href = '?parent=' + categoryId;
            }
        });
    });
    
    // 监听复选框变化，保存状态
    const checkboxes = document.querySelectorAll('.leaf-checkbox');
    console.log('找到复选框数量:', checkboxes.length);
    
    checkboxes.forEach(cb => {
        cb.addEventListener('change', function(e) {
            e.stopPropagation();  // 防止触发行双击
            
            const categoryId = this.getAttribute('data-id');
            const isChecked = this.checked;
            
            console.log('复选框变化:', categoryId, '新状态:', isChecked);
            
            // 发送 AJAX 请求保存状态
            fetch('/admin/inventory/productcategory/update-leaf-status/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    category_id: categoryId,
                    is_leaf: isChecked
                })
            })
            .then(response => response.json())
            .then(data => {
                console.log('AJAX响应:', data);
                if (data.success && isChecked) {
                    // 如果勾选为叶子分类，刷新页面
                    location.reload();
                }
            })
            .catch(error => console.error('Error:', error));
        });
    });
});

// 获取 CSRF Token
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