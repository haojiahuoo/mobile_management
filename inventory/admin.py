# inventory/admin.py
from django.contrib import admin
from django.db.models import Sum
from django.utils.timezone import now
import json
from datetime import timedelta
from django.shortcuts import redirect, render
from django.urls import path
from django.contrib.admin.views.decorators import staff_member_required

from .models import (
    Account, Product, StockIn, Expense, Sale,
    Transaction, Repair, RepairItem, 
    Supplier, Store, Staff, IncomeType, ExpenseType, InitialAccounting, ProductCategory
)

# 导入 views 模块
from . import views


# ================== 基础资料管理 ==================

class SupplierAdmin(admin.ModelAdmin):
    """来往单位管理"""
    list_display = ('id', 'name', 'type', 'contact_person', 'phone', 'created_at')
    list_display_links = ('name',)
    list_filter = ('type', 'created_at')
    search_fields = ('name', 'contact_person', 'phone')
    list_per_page = 25
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('单位信息', {
            'fields': (
                ('name', 'type'),
                ('contact_person', 'phone'),
                ('address',),
            ),
            'classes': ('wide',),
        }),
        ('财务信息', {
            'fields': (
                ('bank_name', 'bank_account'),
                ('tax_number',),
            ),
            'classes': ('wide',),
        }),
        ('其他信息', {
            'fields': ('remark',),
            'classes': ('collapse',),
        }),
    )


class StoreAdmin(admin.ModelAdmin):
    """门店信息管理"""
    list_display = ('code', 'name', 'manager', 'phone', 'is_active', 'created_at')
    list_display_links = ('name',)
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'code', 'manager')
    list_per_page = 25
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('门店信息', {
            'fields': (
                ('code', 'name'),
                ('manager', 'phone'),
                ('address',),
                ('business_hours',),
            ),
            'classes': ('wide',),
        }),
        ('状态', {
            'fields': ('is_active', 'remark'),
            'classes': ('wide',),
        }),
    )


class StaffAdmin(admin.ModelAdmin):
    """职员信息管理"""
    list_display = ('code', 'name', 'position', 'phone', 'store', 'is_active', 'hire_date')
    list_display_links = ('name',)
    list_filter = ('position', 'store', 'is_active', 'hire_date')
    search_fields = ('name', 'code', 'phone')
    list_per_page = 25
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('基本信息', {
            'fields': (
                ('code', 'name'),
                ('position', 'phone'),
                ('id_card', 'hire_date'),
            ),
            'classes': ('wide',),
        }),
        ('薪资信息', {
            'fields': (
                ('salary', 'commission_rate'),
                ('store',),
            ),
            'classes': ('wide',),
        }),
        ('其他信息', {
            'fields': ('remark', 'is_active'),
            'classes': ('collapse',),
        }),
    )


class IncomeTypeAdmin(admin.ModelAdmin):
    """收入类型管理"""
    list_display = ('code', 'name', 'parent', 'sort_order', 'is_active')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'code')
    list_per_page = 25
    ordering = ('sort_order',)


class ExpenseTypeAdmin(admin.ModelAdmin):
    """费用类型管理"""
    list_display = ('code', 'name', 'parent', 'sort_order', 'is_active')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'code')
    list_per_page = 25
    ordering = ('sort_order',)


# ================== 商品管理 ==================

class ProductCategoryAdmin(admin.ModelAdmin):
    """商品分类管理"""
    list_display = ('code', 'name', 'level', 'parent', 'sort_order', 'is_active')
    list_filter = ('level', 'is_active')
    search_fields = ('name', 'code')
    list_per_page = 25
    
    def changelist_view(self, request, extra_context=None):
        return redirect('admin:category_list')
    
    def add_view(self, request, form_url='', extra_context=None):
        return redirect('admin:category_add')


class ProductAdmin(admin.ModelAdmin):
    """商品信息管理"""
    list_display = ('code', 'brand', 'name', 'category', 'supplier', 'unit', 'stock', 'cost_price', 'sell_price', 'is_active')
    list_display_links = ('code', 'name')
    list_filter = ('category', 'supplier', 'is_active', 'brand')
    search_fields = ('code', 'name', 'brand')
    list_editable = ('stock', 'sell_price', 'is_active')
    list_per_page = 25
    list_select_related = ('category', 'supplier')
    
    fieldsets = (
        ('📦 商品信息', {
            'fields': (
                ('code', 'brand', 'name'),
                ('category', 'supplier', 'unit'),
                ('stock', 'cost_price', 'sell_price'),
                ('account', 'is_active'),
            ),
            'classes': ('wide',),
        }),
        ('📝 备注信息', {
            'fields': ('remark',),
            'classes': ('collapse',),
        }),
    )


class StockInAdmin(admin.ModelAdmin):
    """入库记录管理"""
    list_display = ('id', 'product_code', 'product_name', 'quantity', 'price', 'total_cost', 'supplier', 'account', 'created_at')
    list_display_links = ('id',)
    list_filter = ('supplier', 'account', 'created_at')
    search_fields = ('product__name', 'product__code', 'supplier')
    list_per_page = 25
    readonly_fields = ('created_at',)
    
    def product_code(self, obj):
        return obj.product.code if obj.product else '-'
    product_code.short_description = '商品编号'
    
    def product_name(self, obj):
        return obj.product.name if obj.product else '-'
    product_name.short_description = '商品名称'
    
    def total_cost(self, obj):
        return obj.quantity * obj.price
    total_cost.short_description = '总成本'


# ================== 销售管理 ==================

class SaleAdmin(admin.ModelAdmin):
    """销售记录管理"""
    list_display = ('id', 'product_code', 'product_name', 'customer_name', 'quantity', 'sell_price', 'total_price', 'profit', 'created_at')
    list_display_links = ('id',)
    list_filter = ('created_at', 'account')
    search_fields = ('product__name', 'product__code', 'customer__name')
    list_per_page = 25
    readonly_fields = ('total_price', 'profit', 'created_at')
    
    def product_code(self, obj):
        return obj.product.code if obj.product else '-'
    product_code.short_description = '商品编号'
    
    def product_name(self, obj):
        return obj.product.name if obj.product else '-'
    product_name.short_description = '商品名称'
    
    def customer_name(self, obj):
        return obj.customer.name if obj.customer else '-'
    customer_name.short_description = '客户名称'
    
    fieldsets = (
        ('💰 销售信息', {
            'fields': (
                ('product', 'customer'),
                ('quantity', 'sell_price'),
                ('total_price', 'profit'),
                ('account', 'created_at'),
            ),
            'classes': ('wide',),
        }),
    )


# ================== 维修管理 ==================

class RepairAdmin(admin.ModelAdmin):
    """维修记录管理"""
    list_display = ('id', 'customer_name', 'device_model', 'cost', 'status', 'created_at')
    list_display_links = ('id',)
    list_filter = ('status', 'created_at')
    search_fields = ('device_model', 'customer__name')
    list_per_page = 25
    readonly_fields = ('created_at',)
    
    def customer_name(self, obj):
        return obj.customer.name if obj.customer else '-'
    customer_name.short_description = '客户名称'
    
    fieldsets = (
        ('🔧 维修信息', {
            'fields': (
                ('customer', 'device_model'),
                ('issue',),
                ('cost', 'status'),
                ('account', 'remark'),
            ),
            'classes': ('wide',),
        }),
    )


class RepairItemAdmin(admin.ModelAdmin):
    """维修用料管理"""
    list_display = ('id', 'repair_id', 'product_name', 'quantity', 'created_at')
    list_display_links = ('id',)
    list_filter = ('repair__status', 'created_at')
    search_fields = ('product__name', 'repair__device_model')
    list_per_page = 25
    readonly_fields = ('created_at',)
    
    def repair_id(self, obj):
        return obj.repair.id
    repair_id.short_description = '维修单号'
    
    def product_name(self, obj):
        return obj.product.name if obj.product else '-'
    product_name.short_description = '用料名称'


# ================== 财务管理 ==================

class AccountAdmin(admin.ModelAdmin):
    """银行账户管理"""
    list_display = ('name', 'balance', 'created_at')
    list_display_links = ('name',)
    list_filter = ('created_at',)
    search_fields = ('name',)
    list_per_page = 25
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('🏦 账户信息', {
            'fields': (
                ('name', 'balance'),
            ),
            'classes': ('wide',),
        }),
    )


class ExpenseAdmin(admin.ModelAdmin):
    """支出记录管理"""
    list_display = ('title', 'amount', 'category', 'account', 'created_at')
    list_display_links = ('title',)
    list_filter = ('category', 'account', 'created_at')
    search_fields = ('title', 'remark')
    list_per_page = 25
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('💸 支出信息', {
            'fields': (
                ('title', 'amount'),
                ('category', 'account'),
                ('remark',),
            ),
            'classes': ('wide',),
        }),
    )


class TransactionAdmin(admin.ModelAdmin):
    """交易流水管理"""
    list_display = ('account', 'type', 'amount', 'description', 'created_at')
    list_display_links = ('account',)
    list_filter = ('type', 'account', 'created_at')
    search_fields = ('description', 'account__name')
    list_per_page = 25
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('📊 交易信息', {
            'fields': (
                ('account', 'type'),
                ('amount', 'description'),
            ),
            'classes': ('wide',),
        }),
    )


# ================== 初期建账 ==================

class InitialAccountingAdmin(admin.ModelAdmin):
    """初期建账管理"""
    list_display = ('account', 'initial_balance', 'initial_date', 'created_at')
    list_filter = ('initial_date', 'account')
    search_fields = ('account__name',)
    list_per_page = 25
    readonly_fields = ('created_at', 'updated_at')
    
    def changelist_view(self, request, extra_context=None):
        return redirect('admin:initial_accounting_choice')


# ================== 自定义后台站点 ==================

class MyAdminSite(admin.AdminSite):
    site_header = "手机维修管理系统"
    site_title = "管理后台"
    index_title = "数据总览"
    index_template = 'admin/index.html'

    # 初期建账页面包装
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
    
    # 商品分类页面包装
    def category_list(self, request, category_id=None):
        return views.category_list(request, category_id)
    
    def category_add(self, request, parent_id=None):
        return views.category_add(request, parent_id)
    
    # 库存状态页面包装
    def inventory_status(self, request):
        return views.inventory_status(request)
    
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

        today_sales = Sale.objects.filter(created_at__date=today).aggregate(
            total=Sum('total_price')
        )['total'] or 0

        today_profit = Sale.objects.filter(created_at__date=today).aggregate(
            total=Sum('profit')
        )['total'] or 0

        today_expense = Expense.objects.filter(created_at__date=today).aggregate(
            total=Sum('amount')
        )['total'] or 0

        total_sales = Sale.objects.aggregate(total=Sum('total_price'))['total'] or 0
        total_profit = Sale.objects.aggregate(total=Sum('profit'))['total'] or 0
        total_expense = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0
        
        total_balance = Account.objects.aggregate(total=Sum('balance'))['total'] or 0
        
        total_inventory_value = sum(
            product.stock * product.cost_price 
            for product in Product.objects.all()
        )
        
        pending_repairs = Repair.objects.filter(status='pending').count()

        last_7_days = []
        last_7_days_sales = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            last_7_days.append(day.strftime('%m-%d'))
            day_sales = Sale.objects.filter(created_at__date=day).aggregate(
                total=Sum('total_price')
            )['total'] or 0
            last_7_days_sales.append(float(day_sales))

        top_products = (
            Sale.objects
            .values('product__name')
            .annotate(total_profit=Sum('profit'))
            .order_by('-total_profit')[:10]
        )

        top_sales = (
            Sale.objects
            .values('product__name')
            .annotate(total_sales=Sum('quantity'))
            .order_by('-total_sales')[:10]
        )

        extra_context = extra_context or {}
        extra_context.update({
            'today_sales': today_sales,
            'today_profit': today_profit,
            'today_expense': today_expense,
            'total_sales': total_sales,
            'total_expense': total_expense,
            'total_profit': total_profit,
            'net_profit': total_profit - total_expense,
            'total_balance': total_balance,
            'total_inventory_value': total_inventory_value,
            'pending_repairs': pending_repairs,
            'last_7_days': json.dumps(last_7_days),
            'last_7_days_sales': json.dumps(last_7_days_sales),
            'top_products': top_products,
            'top_sales': top_sales,
        })

        return super().index(request, extra_context)


# ================== 创建 admin_site 实例 ==================
admin_site = MyAdminSite(name='myadmin')

# 注册所有模型
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