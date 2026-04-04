# inventory/admin/initial.py
"""初期建账管理 - 独立模块"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from ..models import Product


@staff_member_required
def initial_stock_setup(request):
    """初期库存建账页面"""
    if request.method == 'POST':
        # 保存初期库存数据
        for key, value in request.POST.items():
            if key.startswith('cost_'):
                product_id = key.split('_')[1]
                try:
                    product = Product.objects.get(id=product_id)
                    product.cost_price = request.POST.get(f'cost_{product_id}', 0)
                    product.stock = request.POST.get(f'stock_{product_id}', 0)
                    product.save()
                except Product.DoesNotExist:
                    pass
        messages.success(request, '初期库存设置成功！')
        return redirect('admin:inventory_product_changelist')
    
    # 获取所有商品
    products = Product.objects.all().select_related('category').order_by('category__name', 'name')
    
    context = {
        'products': products,
        'title': '初期库存建账',
    }
    return render(request, 'admin/inventory/initial_stock_setup.html', context)