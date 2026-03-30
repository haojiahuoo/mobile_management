from django.contrib import admin
from django.db.models import Sum
from django.utils.timezone import now
from django.db.models.functions import TruncDate
import json
from datetime import timedelta

from .models import (
    Account, Product, StockIn, Expense, Sale,
    Transaction, Customer, Repair, RepairItem, Supplier, Store, Staff, IncomeType, ExpenseType, InitialAccounting
)

# ================== 各模型后台 ==================

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'balance', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name',)
    readonly_fields = ('created_at',)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'account', 'type', 'amount', 'description', 'created_at')
    list_filter = ('type', 'account', 'created_at')
    search_fields = ('description', 'account__name')
    readonly_fields = ('created_at',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'stock', 'cost_price', 'sell_price', 'account', 'created_at')
    search_fields = ('name',)
    list_filter = ('category', 'account')
    readonly_fields = ('created_at',)


@admin.register(StockIn)
class StockInAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'quantity', 'price', 'supplier', 'account', 'created_at')
    list_filter = ('supplier', 'account', 'created_at')
    search_fields = ('product__name', 'supplier')
    readonly_fields = ('created_at',)
    
    def total_cost(self, obj):
        return obj.quantity * obj.price
    total_cost.short_description = '总成本'


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'amount', 'category', 'account', 'remark', 'created_at')
    list_filter = ('category', 'account', 'created_at')
    search_fields = ('title', 'remark')
    readonly_fields = ('created_at',)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'phone', 'address', 'created_at')
    search_fields = ('name', 'phone')
    readonly_fields = ('created_at',)


@admin.register(Repair)
class RepairAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'device_model', 'cost', 'status', 'account', 'created_at')
    list_filter = ('status', 'account', 'created_at')
    search_fields = ('device_model', 'customer__name', 'issue')
    readonly_fields = ('created_at',)


@admin.register(RepairItem)
class RepairItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'repair', 'product', 'quantity', 'created_at')
    list_filter = ('repair__status', 'created_at')
    search_fields = ('product__name', 'repair__device_model')
    readonly_fields = ('created_at',)


# ================== 销售后台管理（带图表） ==================

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'customer', 'quantity', 'sell_price', 'total_price', 'profit', 'account', 'created_at')
    list_filter = ('account', 'created_at')
    search_fields = ('product__name', 'customer__name')
    readonly_fields = ('total_price', 'profit', 'created_at')

# ================== 自定义后台站点 ==================

class MyAdminSite(admin.AdminSite):
    site_header = "手机维修管理系统"
    site_title = "管理后台"
    index_title = "数据总览"
    index_template = 'admin/myadmin/index.html'  # 指定自定义模板

    def index(self, request, extra_context=None):
        today = now().date()

        # 今日数据 - 使用英文字段名
        today_sales = Sale.objects.filter(created_at__date=today).aggregate(
            total=Sum('total_price')
        )['total'] or 0

        today_profit = Sale.objects.filter(created_at__date=today).aggregate(
            total=Sum('profit')
        )['total'] or 0

        today_expense = Expense.objects.filter(created_at__date=today).aggregate(
            total=Sum('amount')
        )['total'] or 0

        # 累计数据
        total_sales = Sale.objects.aggregate(total=Sum('total_price'))['total'] or 0
        total_profit = Sale.objects.aggregate(total=Sum('profit'))['total'] or 0
        total_expense = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0
        
        # 账户总余额
        total_balance = Account.objects.aggregate(total=Sum('balance'))['total'] or 0
        
        # 库存总价值
        total_inventory_value = sum(
            product.stock * product.cost_price 
            for product in Product.objects.all()
        )
        
        # 待维修数量（pending 状态）
        pending_repairs = Repair.objects.filter(status='pending').count()

        # 近7天销售趋势
        last_7_days = []
        last_7_days_sales = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            last_7_days.append(day.strftime('%m-%d'))
            day_sales = Sale.objects.filter(created_at__date=day).aggregate(
                total=Sum('total_price')
            )['total'] or 0
            last_7_days_sales.append(float(day_sales))

        # 利润排行榜
        top_products = (
            Sale.objects
            .values('product__name')
            .annotate(total_profit=Sum('profit'))
            .order_by('-total_profit')[:10]
        )

        # 热销商品排行榜
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

# ================== 基础资料管理 ==================

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'type', 'contact_person', 'phone', 'created_at')
    list_filter = ('type', 'created_at')
    search_fields = ('name', 'contact_person', 'phone')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name', 'manager', 'phone', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'code', 'manager')
    readonly_fields = ('created_at',)


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name', 'position', 'phone', 'store', 'is_active', 'hire_date')
    list_filter = ('position', 'store', 'is_active', 'hire_date')
    search_fields = ('name', 'code', 'phone')
    readonly_fields = ('created_at',)


@admin.register(IncomeType)
class IncomeTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name', 'parent', 'sort_order', 'is_active')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'code')
    ordering = ('sort_order',)


@admin.register(ExpenseType)
class ExpenseTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name', 'parent', 'sort_order', 'is_active')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'code')
    ordering = ('sort_order',)


@admin.register(InitialAccounting)
class InitialAccountingAdmin(admin.ModelAdmin):
    list_display = ('id', 'account', 'initial_balance', 'initial_date', 'created_at')
    list_filter = ('initial_date', 'account')
    search_fields = ('account__name',)
    readonly_fields = ('created_at', 'updated_at')
# ================== 创建 admin_site 实例 ==================

admin_site = MyAdminSite(name='myadmin')

# 注册所有模型
admin_site.register(Account, AccountAdmin)
admin_site.register(Product, ProductAdmin)
admin_site.register(StockIn, StockInAdmin)
admin_site.register(Expense, ExpenseAdmin)
admin_site.register(Sale, SaleAdmin)
admin_site.register(Customer, CustomerAdmin)
admin_site.register(Repair, RepairAdmin)
admin_site.register(RepairItem, RepairItemAdmin)
admin_site.register(Transaction, TransactionAdmin)

# 新增的基础资料
admin_site.register(Supplier, SupplierAdmin)
admin_site.register(Store, StoreAdmin)
admin_site.register(Staff, StaffAdmin)
admin_site.register(IncomeType, IncomeTypeAdmin)
admin_site.register(ExpenseType, ExpenseTypeAdmin)
admin_site.register(InitialAccounting, InitialAccountingAdmin)
