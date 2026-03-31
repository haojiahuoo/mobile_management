# inventory/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.utils.timezone import now
from django.shortcuts import redirect
from django.urls import path
from django.db.models import Sum
from datetime import timedelta
from itertools import product
import json
import uuid

from .models import (
    Account, Product, StockIn, Expense, Sale,
    Transaction, Repair, RepairItem,
    Supplier, Store, Staff,
    IncomeType, ExpenseType,
    InitialAccounting, ProductCategory,
    ProductSKU, ProductAttribute, ProductAttributeValue
)
from . import views


# ================== 通用 UI 函数 ==================
def fmt_money(v):
    if v is None:
        return '-'
    try:
        return format_html('¥{:.2f}', float(v))
    except:
        return '-'


def fmt_status(v):
    return format_html(
        '<span class="status-badge {}">{}</span>',
        'status-active' if v else 'status-inactive',
        '启用' if v else '禁用'
    )


def fmt_stock(v):
    if v <= 0:
        return format_html('<span class="stock-out">⚠️ 缺货 ({})</span>', v)
    elif v < 10:
        return format_html('<span class="stock-low">⚠️ 低库存 ({})</span>', v)
    return format_html('<span class="stock-ok">✓ {}</span>', v)


# ================== BaseAdmin ==================
class BaseAdmin(admin.ModelAdmin):
    list_per_page = 25

    def status_display(self, obj):
        if hasattr(obj, 'is_active'):
            return fmt_status(obj.is_active)
        return '-'
    status_display.short_description = '状态'


# ================== 基础资料 ==================
class SupplierAdmin(BaseAdmin):
    list_display = ('name', 'type_display', 'contact_person', 'phone', 'created_at')

    def type_display(self, obj):
        return {'supplier': '供应商', 'customer': '客户', 'both': '供应商/客户'}.get(obj.type, obj.type)
    type_display.short_description = '类型'


class StoreAdmin(BaseAdmin):
    list_display = ('code', 'name', 'manager', 'phone', 'status_display')


class StaffAdmin(BaseAdmin):
    list_display = ('code', 'name', 'position_display', 'store', 'status_display')

    def position_display(self, obj):
        return {
            'manager': '经理',
            'cashier': '收银员',
            'salesman': '销售员',
            'technician': '技术员'
        }.get(obj.position, obj.position)
    position_display.short_description = '职位'


class ProductCategoryAdmin(BaseAdmin):
    list_display = ('name', 'parent', 'level', 'add_product')

    def add_product(self, obj):
        if obj.children.exists():
            return "-"
        return format_html(
            '<a class="button" href="/admin/inventory/product/add/?category={}">➕ 添加商品</a>',
            obj.id
        )
    add_product.short_description = '操作'


# ================== 商品管理 ==================
# SKU Inline
class ProductSKUInline(admin.TabularInline):
    model = ProductSKU
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductSKUInline]
    list_display = ('code', 'brand', 'name', 'category', 'stock', 'sell_price', 'generate_sku_btn')
    search_fields = ('name', 'brand', 'code')
    list_filter = ('category', 'brand')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:product_id>/generate_sku/', self.admin_site.admin_view(self.generate_sku_view))
        ]
        return custom_urls + urls

    def generate_sku_btn(self, obj):
        return format_html(
            '<a class="button" href="{}">生成SKU</a>',
            f"/admin/inventory/product/{obj.id}/generate_sku/"
        )
    generate_sku_btn.short_description = '生成SKU'

    def generate_sku_view(self, request, product_id):
        product = Product.objects.get(id=product_id)
        # 示例属性字典（可扩展为动态 UI）
        attributes = {"颜色": ["黑色", "白色"], "容量": ["128G", "256G"]}
        # 删除原 SKU
        ProductSKU.objects.filter(product=product).delete()
        skus = generate_sku(product, attributes)
        ProductSKU.objects.bulk_create(skus)
        return redirect(f"/admin/inventory/product/{product_id}/change/")

    # 自动带分类
    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        category_id = request.GET.get('category')
        if category_id:
            initial['category'] = category_id
        return initial


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(ProductAttributeValue)
class ProductAttributeValueAdmin(admin.ModelAdmin):
    list_display = ('attribute', 'value')


# ================== SKU 生成函数 ==================
def generate_sku(product, attributes_dict):
    keys = list(attributes_dict.keys())
    values = list(attributes_dict.values())
    all_combinations = list(product(*values))
    skus = []
    for combo in all_combinations:
        attr_combo = dict(zip(keys, combo))
        skus.append(ProductSKU(
            product=product,
            attributes=attr_combo,
            code=str(uuid.uuid4())[:8]
        ))
    return skus


# ================== 入库 ==================
class StockInAdmin(BaseAdmin):
    list_display = ('product', 'quantity', 'price_display', 'total_cost', 'created_at')

    def price_display(self, obj):
        return fmt_money(obj.price)

    def total_cost(self, obj):
        return fmt_money(obj.quantity * obj.price)

    def save_model(self, request, obj, form, change):
        if not change:
            p = obj.product
            old_stock = p.stock
            new_stock = old_stock + obj.quantity
            if new_stock > 0:
                p.cost_price = (old_stock * p.cost_price + obj.quantity * obj.price) / new_stock
            p.stock = new_stock
            p.save()
        super().save_model(request, obj, form, change)


# ================== 销售 ==================
class SaleAdmin(BaseAdmin):
    list_display = ('product', 'quantity', 'sell_price_display', 'total_price_display', 'profit_display')

    def sell_price_display(self, obj):
        return fmt_money(obj.sell_price)

    def total_price_display(self, obj):
        return fmt_money(obj.total_price)

    def profit_display(self, obj):
        return fmt_money(obj.profit)

    def save_model(self, request, obj, form, change):
        if not change:
            p = obj.product
            obj.total_price = obj.quantity * obj.sell_price
            obj.profit = (obj.sell_price - p.cost_price) * obj.quantity
            p.stock -= obj.quantity
            p.save()
        super().save_model(request, obj, form, change)


# ================== 维修 ==================
class RepairAdmin(BaseAdmin):
    list_display = ('id', 'device_model', 'cost_display', 'status_display')

    def cost_display(self, obj):
        return fmt_money(obj.cost)


class RepairItemAdmin(BaseAdmin):
    list_display = ('repair', 'product', 'quantity')


# ================== 财务 ==================
class AccountAdmin(BaseAdmin):
    list_display = ('name', 'balance_display')

    def balance_display(self, obj):
        return fmt_money(obj.balance)


class ExpenseAdmin(BaseAdmin):
    list_display = ('title', 'amount_display', 'account', 'created_at')

    def amount_display(self, obj):
        return fmt_money(obj.amount)


class TransactionAdmin(BaseAdmin):
    list_display = ('account', 'type_display', 'amount_display', 'created_at')

    def type_display(self, obj):
        return '收入' if obj.type == 'income' else '支出'

    def amount_display(self, obj):
        return fmt_money(obj.amount)


class IncomeTypeAdmin(BaseAdmin):
    list_display = ('name', 'parent', 'status_display')


class ExpenseTypeAdmin(BaseAdmin):
    list_display = ('name', 'parent', 'status_display')


class InitialAccountingAdmin(BaseAdmin):
    list_display = ('account', 'initial_balance', 'initial_date')

    def changelist_view(self, request, extra_context=None):
        return redirect('admin:initial_accounting_choice')


# ================== 自定义 AdminSite ==================
class MyAdminSite(admin.AdminSite):
    site_header = "手机维修管理系统"
    site_title = "管理后台"
    index_title = "数据总览"
    index_template = 'admin/index.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('initial-accounting/', self.admin_view(self.initial_accounting_choice), name='initial_accounting_choice'),
            path('initial-stock/', self.admin_view(self.initial_stock), name='initial_stock'),
            path('initial-receivable/', self.admin_view(self.initial_receivable), name='initial_receivable'),
            path('initial-cash/', self.admin_view(self.initial_cash), name='initial_cash'),
            path('initial-finance/', self.admin_view(self.initial_finance), name='initial_finance'),
            path('product-category/', self.admin_view(self.category_list), name='category_list'),
            path('product-category/<int:category_id>/', self.admin_view(self.category_list), name='category_list'),
            path('category-add/', self.admin_view(self.category_add), name='category_add'),
            path('category-add/<int:parent_id>/', self.admin_view(self.category_add), name='category_add'),
            path('inventory/status/', self.admin_view(self.inventory_status), name='inventory_status'),
        ]
        return custom_urls + urls

    def index(self, request, extra_context=None):
        today = now().date()
        today_sales = Sale.objects.filter(created_at__date=today).aggregate(total=Sum('total_price'))['total'] or 0
        today_profit = Sale.objects.filter(created_at__date=today).aggregate(total=Sum('profit'))['total'] or 0
        today_expense = Expense.objects.filter(created_at__date=today).aggregate(total=Sum('amount'))['total'] or 0

        total_sales = Sale.objects.aggregate(total=Sum('total_price'))['total'] or 0
        total_profit = Sale.objects.aggregate(total=Sum('profit'))['total'] or 0
        total_expense = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0

        last_7_days = []
        last_7_days_sales = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            last_7_days.append(day.strftime('%m-%d'))
            sales = Sale.objects.filter(created_at__date=day).aggregate(total=Sum('total_price'))['total'] or 0
            last_7_days_sales.append(float(sales))

        extra_context = extra_context or {}
        extra_context.update({
            'today_sales': today_sales,
            'today_profit': today_profit,
            'today_expense': today_expense,
            'total_sales': total_sales,
            'total_profit': total_profit,
            'total_expense': total_expense,
            'last_7_days': json.dumps(last_7_days),
            'last_7_days_sales': json.dumps(last_7_days_sales),
        })
        return super().index(request, extra_context)

    # 自定义视图入口
    def initial_accounting_choice(self, request):
        return views.initial_accounting_choice(request)

    def initial_stock(self, request):
        return views.initial_stock(request)

    def initial_receivable(self, request):
        return views.initial_receivable(request)

    def initial_cash(self, request):
        return views.initial_cash(request)

    def initial_finance(self, request):
        return views.initial_finance(request)

    def category_list(self, request, category_id=None):
        return views.category_list(request, category_id)

    def category_add(self, request, parent_id=None):
        return views.category_add(request, parent_id)

    def inventory_status(self, request):
        return views.inventory_status(request)


# ================== 注册默认 Admin ==================
admin_site = MyAdminSite(name='myadmin')

admin_site.register(Account, AccountAdmin)
admin_site.register(Product, ProductAdmin)
admin_site.register(StockIn, StockInAdmin)
admin_site.register(Expense, ExpenseAdmin)
admin_site.register(Sale, SaleAdmin)
admin_site.register(Repair, RepairAdmin)
admin_site.register(RepairItem, RepairItemAdmin)
admin_site.register(Transaction, TransactionAdmin)
admin_site.register(Supplier, SupplierAdmin)
admin_site.register(Store, StoreAdmin)
admin_site.register(Staff, StaffAdmin)
admin_site.register(IncomeType, IncomeTypeAdmin)
admin_site.register(ExpenseType, ExpenseTypeAdmin)
admin_site.register(InitialAccounting, InitialAccountingAdmin)
admin_site.register(ProductCategory, ProductCategoryAdmin)
admin_site.register(ProductAttribute, ProductAttributeAdmin)
admin_site.register(ProductAttributeValue, ProductAttributeValueAdmin)
admin_site.register(ProductSKU)