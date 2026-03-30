# inventory/views.py
from rest_framework import viewsets
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import (
    Product, Supplier, Account, InitialAccounting, ProductCategory
)
from .serializers import ProductSerializer


# ================== API 视图 ==================
class ProductViewSet(viewsets.ModelViewSet):
    """商品 API 接口"""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


# ================== 自定义后台视图 ==================
@staff_member_required
def inventory_status(request):
    """库存状态页面"""
    products = Product.objects.all().order_by('category__name', 'name')
    
    # 计算库存统计
    total_products = products.count()
    total_stock = sum(p.stock for p in products)
    total_value = sum(p.stock * p.cost_price for p in products)
    
    # 低库存商品（库存 < 10）
    low_stock_products = [p for p in products if p.stock < 10]
    
    # 缺货商品（库存 = 0）
    out_of_stock_products = [p for p in products if p.stock == 0]
    
    context = {
        'products': products,
        'total_products': total_products,
        'total_stock': total_stock,
        'total_value': total_value,
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,
        'title': '库存状态',
    }
    return render(request, 'inventory/dashboard/stock_status.html', context)


# ================== 初期建账页面 ==================

@staff_member_required
def initial_accounting_choice(request):
    """初期建账选择页面"""
    return render(request, 'inventory/initial_accounting/choice.html')


@staff_member_required
def initial_stock(request):
    """初期库存商品"""
    if request.method == 'POST':
        # 保存库存数据
        for key, value in request.POST.items():
            if key.startswith('stock_'):
                product_id = key.split('_')[1]
                stock = request.POST.get(f'stock_{product_id}', 0)
                cost = request.POST.get(f'cost_{product_id}', 0)
                try:
                    product = Product.objects.get(id=product_id)
                    product.stock = int(stock)
                    product.cost_price = float(cost)
                    product.save()
                except Product.DoesNotExist:
                    pass
        messages.success(request, '库存数据已保存')
        return redirect('admin:initial_stock')
    
    products = Product.objects.all().select_related('category').order_by('category__name', 'name')
    return render(request, 'inventory/initial_accounting/stock.html', {'products': products})


@staff_member_required
def initial_receivable(request):
    """初期应收应付"""
    if request.method == 'POST':
        type_data = request.POST.get('type')
        # 这里可以保存应收应付数据
        messages.success(request, '应收应付数据已保存')
        return redirect('admin:initial_receivable')
    
    customers = Supplier.objects.filter(type='customer')  # 客户类型
    suppliers = Supplier.objects.filter(type='supplier')  # 供应商类型
    return render(request, 'inventory/initial_accounting/receivable.html', {
        'customers': customers,
        'suppliers': suppliers
    })


@staff_member_required
def initial_cash(request):
    """初期现金存款"""
    if request.method == 'POST':
        for key, value in request.POST.items():
            if key.startswith('balance_'):
                account_id = key.split('_')[1]
                balance = request.POST.get(f'balance_{account_id}', 0)
                try:
                    account = Account.objects.get(id=account_id)
                    account.balance = float(balance)
                    account.save()
                except Account.DoesNotExist:
                    pass
        messages.success(request, '账户余额已保存')
        return redirect('admin:initial_cash')
    
    accounts = Account.objects.all()
    return render(request, 'inventory/initial_accounting/cash.html', {'accounts': accounts})


@staff_member_required
def initial_finance(request):
    """初期财务数据"""
    if request.method == 'POST':
        # 保存财务数据到 InitialAccounting 模型
        initial_profit = request.POST.get('initial_profit', 0)
        initial_cost = request.POST.get('initial_cost', 0)
        initial_income = request.POST.get('initial_income', 0)
        initial_expense = request.POST.get('initial_expense', 0)
        initial_date = request.POST.get('initial_date', '2024-01-01')
        
        # 保存或更新财务数据
        obj, created = InitialAccounting.objects.get_or_create(
            account=None,  # 特殊标识财务数据
            initial_date=initial_date,
            defaults={
                'initial_balance': float(initial_profit) + float(initial_income) - float(initial_cost) - float(initial_expense),
                'remark': f'利润:{initial_profit},成本:{initial_cost},收入:{initial_income},支出:{initial_expense}'
            }
        )
        messages.success(request, '财务数据已保存')
        return redirect('admin:initial_finance')
    
    return render(request, 'inventory/initial_accounting/finance.html')


# ================== 商品分类管理 ==================

@staff_member_required
def category_list(request, category_id=None):
    """商品分类列表页面（侧边栏菜单）"""
    current_category = None
    categories = None
    products = None
    
    if category_id:
        current_category = get_object_or_404(ProductCategory, id=category_id)
        # 获取当前分类下的子分类
        categories = ProductCategory.objects.filter(
            parent=current_category, 
            is_active=True
        ).order_by('sort_order', 'code')
        # 获取当前分类下的商品
        products = Product.objects.filter(
            category=current_category, 
            is_active=True
        ).select_related('supplier').order_by('code')
    else:
        # 获取顶级分类
        categories = ProductCategory.objects.filter(
            parent__isnull=True, 
            is_active=True
        ).order_by('sort_order', 'code')
    
    # 构建面包屑导航
    breadcrumb = []
    if current_category:
        temp = current_category
        while temp:
            breadcrumb.insert(0, temp)
            temp = temp.parent
    
    context = {
        'current_category': current_category,
        'categories': categories,
        'products': products,
        'breadcrumb': breadcrumb,
    }
    return render(request, 'inventory/product/category_list.html', context)


@staff_member_required
def category_add(request, parent_id=None):
    """添加分类"""
    parent = None
    if parent_id:
        parent = get_object_or_404(ProductCategory, id=parent_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        parent_id = request.POST.get('parent_id')
        
        parent_obj = None
        if parent_id and parent_id != '0':
            parent_obj = get_object_or_404(ProductCategory, id=parent_id)
            # 获取同级分类数量，生成编码
            siblings = ProductCategory.objects.filter(parent=parent_obj)
            code_num = siblings.count() + 1
            code = f"{parent_obj.code}{code_num:04d}"
            level = parent_obj.level + 1
        else:
            # 顶级分类
            top_level_count = ProductCategory.objects.filter(parent__isnull=True).count()
            code_num = top_level_count + 1
            code = f"{code_num:04d}"
            level = 1
        
        ProductCategory.objects.create(
            name=name,
            code=code,
            parent=parent_obj,
            level=level,
            sort_order=0,
            is_active=True
        )
        
        messages.success(request, f'分类 "{name}" 添加成功')
        
        if parent_obj:
            return redirect('admin:category_list', category_id=parent_obj.id)
        return redirect('admin:category_list')
    
    return render(request, 'inventory/product/category_add.html', {'parent': parent})