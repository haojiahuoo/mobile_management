# inventory/admin.py
# inventory/admin.py
"""Admin 入口 - 导入所有 Admin 类（自动注册）"""

# 导入所有 Admin 类（@admin.register 会自动注册）
from .admin.core import (
    ProductAdmin, ProductCategoryAdmin,
    ProductAttributeAdmin, ProductAttributeValueAdmin, ProductSKUAdmin
)
from .admin.transaction import (
    StockInAdmin, SaleAdmin, RepairAdmin, RepairItemAdmin, ExpenseAdmin
)
from .admin.party import (
    SupplierAdmin, StoreAdmin, StaffAdmin
)
from .admin.finance import (
    AccountAdmin, TransactionAdmin, IncomeTypeAdmin, ExpenseTypeAdmin, InitialAccountingAdmin
)
from .admin.site import MyAdminSite, admin_site




# from django.contrib import admin
# from django.utils.html import format_html
# from django.utils.timezone import now
# from django.shortcuts import redirect
# from django.urls import path
# from django.db.models import Sum
# from datetime import timedelta
# from . import views
# from django.utils.safestring import mark_safe  # 添加这个
# import json
# from .models import (
#     Account, Product, StockIn, Expense, Sale,
#     Transaction, Repair, RepairItem,
#     Supplier, Store, Staff,
#     IncomeType, ExpenseType,
#     InitialAccounting, ProductCategory,
#     ProductSKU, ProductAttribute, ProductAttributeValue
# )


# # ================== 通用 UI 函数 ==================
# def fmt_money(v):
#     if v is None:
#         return '-'
#     try:
#         return format_html('¥{:.2f}', float(v))
#     except:
#         return '-'


# def fmt_status(v):
#     return format_html(
#         '<span class="status-badge {}">{}</span>',
#         'status-active' if v else 'status-inactive',
#         '启用' if v else '禁用'
#     )


# def fmt_stock(v):
#     if v <= 0:
#         return format_html('<span class="stock-out">⚠️ 缺货 ({})</span>', v)
#     elif v < 10:
#         return format_html('<span class="stock-low">⚠️ 低库存 ({})</span>', v)
#     return format_html('<span class="stock-ok">✓ {}</span>', v)


# # ================== BaseAdmin ==================
# class BaseAdmin(admin.ModelAdmin):
#     list_per_page = 25

#     def status_display(self, obj):
#         if hasattr(obj, 'is_active'):
#             return fmt_status(obj.is_active)
#         return '-'
#     status_display.short_description = '状态'


# # ================== 基础资料 ==================
# class SupplierAdmin(BaseAdmin):
#     list_display = ('name', 'type_display', 'contact_person', 'phone', 'created_at')
#     search_fields = ['name', 'contact_person', 'phone']

#     def type_display(self, obj):
#         return {'supplier': '供应商', 'customer': '客户', 'both': '供应商/客户'}.get(obj.type, obj.type)
#     type_display.short_description = '类型'


# class StoreAdmin(BaseAdmin):
#     list_display = ('code', 'name', 'manager', 'phone', 'status_display')
#     search_fields = ['code', 'name', 'manager']


# class StaffAdmin(BaseAdmin):
#     list_display = ('code', 'name', 'position_display', 'store', 'status_display')
#     search_fields = ['code', 'name']

#     def position_display(self, obj):
#         return {
#             'manager': '经理',
#             'cashier': '收银员',
#             'salesman': '销售员',
#             'technician': '技术员'
#         }.get(obj.position, obj.position)
#     position_display.short_description = '职位'


# class ProductCategoryAdmin(BaseAdmin):
#     list_display = ('name', 'parent', 'level', 'add_product')
#     search_fields = ['name']

#     def add_product(self, obj):
#         if obj.children.exists():
#             return "-"
#         return format_html(
#             '<a class="button" href="/admin/inventory/product/add/?category={}">➕ 添加商品</a>',
#             obj.id
#         )
#     add_product.short_description = '操作'


# class AccountAdmin(BaseAdmin):
#     list_display = ('name', 'balance_display')
#     search_fields = ['name']

#     def balance_display(self, obj):
#         return fmt_money(obj.balance)


# # ================== SKU Inline ==================
# class ProductSKUInline(admin.TabularInline):
#     """SKU 内联管理"""
#     model = ProductSKU
#     extra = 0
#     fields = ['code', 'attributes', 'stock', 'sell_price', 'cost_price']
#     readonly_fields = ['code']
#     can_delete = True
#     show_change_link = True
    
#     def get_extra(self, request, obj=None, **kwargs):
#         return 0


# # ================== 合并后的 ProductAdmin ==================
# class ProductAdmin(admin.ModelAdmin):
#     """商品管理"""
    
#     # ========== 模板配置 ==========
#     change_form_template = 'admin/inventory/product/change_form.html'
    
#     # ========== 内联配置 ==========
#     inlines = [ProductSKUInline]
    
#     # ========== 列表页配置 ==========
#     list_display = [
#         'id', 'code', 'name', 'brand', 'category',
#         'stock_display', 'cost_price', 'sell_price', 
#         'show_profit_rate', 'is_active', 'generate_sku_btn'
#     ]
    
#     list_filter = [
#         'category', 
#         'supplier', 
#         'is_active', 
#         'color',
#         ('created_at', admin.DateFieldListFilter)
#     ]
    
#     search_fields = ['code', 'name', 'brand', 'remark']
#     list_per_page = 20
#     ordering = ['-created_at']
    
#     # ========== 表单页配置 ==========
#     fieldsets = None
#     readonly_fields = ['created_at', 'updated_at']
#     autocomplete_fields = ['category', 'supplier', 'account']
#     list_editable = ['sell_price', 'is_active']
#     save_on_top = True
    
#     # ========== 自定义列表显示方法 ==========
#     def stock_display(self, obj):
#         """库存显示（带颜色和状态）"""
#         if obj.stock <= 0:
#             color = '#dc3545'
#             text = f'{obj.stock} (缺货)'
#             bg = '#fff2f2'
#         elif obj.stock <= 10:
#             color = '#fd7e14'
#             text = f'{obj.stock} (低库存)'
#             bg = '#fff4e6'
#         else:
#             color = '#28a745'
#             text = str(obj.stock)
#             bg = '#e8f5e9'
        
#         return format_html(
#             '<span style="color: {}; font-weight: bold; background: {}; padding: 2px 8px; border-radius: 12px; display: inline-block;">{}</span>',
#             color, bg, text
#         )
#     stock_display.short_description = '库存状态'
#     stock_display.admin_order_field = 'stock'
    
#     def show_profit_rate(self, obj):
#         """利润率显示"""
#         try:
#             if obj.sell_price and obj.cost_price and obj.cost_price > 0:
#                 cost = float(obj.cost_price)
#                 sell = float(obj.sell_price)
#                 rate = (sell - cost) / cost * 100
                
#                 if rate > 30:
#                     color = '#28a745'
#                     icon = '📈'
#                 elif rate > 10:
#                     color = '#17a2b8'
#                     icon = '📊'
#                 elif rate > 0:
#                     color = '#ffc107'
#                     icon = '📉'
#                 else:
#                     color = '#dc3545'
#                     icon = '⚠️'
                
#                 html = '<span style="color: {}; font-weight: bold;">{} {:.1f}%</span>'.format(color, icon, rate)
#             return mark_safe(html)
#         except Exception as e:
#             print(f"Error in show_profit_rate: {e}")
#             return "-"
        
#     show_profit_rate.short_description = '利润率'
#     show_profit_rate.admin_order_field = 'sell_price'
    
#     def generate_sku_btn(self, obj):
#         return format_html(
#             '<a class="button" href="{}">⚙️ 生成SKU</a>',
#             f"/admin/inventory/product/{obj.id}/generate_sku/"
#         )
#     generate_sku_btn.short_description = 'SKU操作'
    
#     # ========== URL 路由配置 ==========
#     def get_urls(self):
#         urls = super().get_urls()
#         custom_urls = [
#             path(
#                 '<int:product_id>/generate_sku/',
#                 self.admin_site.admin_view(self.generate_sku_view),
#                 name='product-generate-sku'
#             ),
#         ]
#         return custom_urls + urls
    
#     def generate_sku_view(self, request, product_id):
#         product_obj = Product.objects.get(id=product_id)
#         attributes = {"颜色": ["黑色", "白色"], "容量": ["128G", "256G"]}
#         ProductSKU.objects.filter(product=product_obj).delete()
#         skus = self.generate_sku(product_obj, attributes)
#         ProductSKU.objects.bulk_create(skus)
#         self.message_user(request, f'成功生成 {len(skus)} 个SKU')
#         return redirect(f"/admin/inventory/product/{product_id}/change/")
    
#     def generate_sku(self, product_obj, attributes_dict):
#         from itertools import product as cartesian_product
#         keys = list(attributes_dict.keys())
#         values = list(attributes_dict.values())
#         all_combinations = list(cartesian_product(*values))
        
#         skus = []
#         for combo in all_combinations:
#             attr_combo = dict(zip(keys, combo))
#             sku_code = f"{product_obj.code}-{'-'.join([str(v)[:2] for v in combo])}"[:50]
#             skus.append(ProductSKU(
#                 product=product_obj,
#                 attributes=attr_combo,
#                 code=sku_code,
#                 cost_price=product_obj.cost_price,
#                 sell_price=product_obj.sell_price,
#                 stock=0
#             ))
#         return skus
    
#     def get_changeform_initial_data(self, request):
#         initial = super().get_changeform_initial_data(request)
#         category_id = request.GET.get('category')
#         if category_id:
#             initial['category'] = category_id
#         return initial
    
#     def save_model(self, request, obj, form, change):
#         if not change:
#             self.message_user(request, f'成功添加商品：{obj.name}', level='SUCCESS')
#         else:
#             self.message_user(request, f'成功更新商品：{obj.name}', level='SUCCESS')
#         super().save_model(request, obj, form, change)
    
#     actions = ['batch_generate_sku', 'batch_update_stock', 'batch_set_active']
    
#     def batch_generate_sku(self, request, queryset):
#         for product in queryset:
#             attributes = {"颜色": ["黑色", "白色"], "容量": ["128G", "256G"]}
#             ProductSKU.objects.filter(product=product).delete()
#             skus = self.generate_sku(product, attributes)
#             ProductSKU.objects.bulk_create(skus)
#         self.message_user(request, f'成功为 {queryset.count()} 个商品生成SKU')
#     batch_generate_sku.short_description = '批量生成SKU'
    
#     def batch_update_stock(self, request, queryset):
#         for product in queryset:
#             product.stock += 10
#             product.save()
#         self.message_user(request, f'成功为 {queryset.count()} 个商品增加10个库存')
#     batch_update_stock.short_description = '批量增加10个库存'
    
#     def batch_set_active(self, request, queryset):
#         updated = queryset.update(is_active=True)
#         self.message_user(request, f'成功启用 {updated} 个商品')
#     batch_set_active.short_description = '批量启用商品'


# # ================== 商品属性管理 ==================
# class ProductAttributeAdmin(admin.ModelAdmin):
#     list_display = ('name',)
#     search_fields = ('name',)
#     ordering = ('name',)


# class ProductAttributeValueAdmin(admin.ModelAdmin):
#     list_display = ('attribute', 'value')
#     list_filter = ('attribute',)
#     search_fields = ('value',)
#     ordering = ('attribute', 'value')


# class ProductSKUAdmin(admin.ModelAdmin):
#     list_display = ('code', 'product', 'attributes_display', 'stock')
#     list_filter = ('product__category',)
#     search_fields = ('code', 'product__name')
#     readonly_fields = ('code',)
    
#     def attributes_display(self, obj):
#         if obj.attributes:
#             return ', '.join([f"{k}:{v}" for k, v in obj.attributes.items()])
#         return '-'
#     attributes_display.short_description = '属性组合'


# # ================== 入库、销售、维修等 Admin ==================
# class StockInAdmin(BaseAdmin):
#     list_display = ('product', 'quantity', 'price_display', 'total_cost', 'created_at')

#     def price_display(self, obj):
#         return fmt_money(obj.price)

#     def total_cost(self, obj):
#         return fmt_money(obj.quantity * obj.price)

#     def save_model(self, request, obj, form, change):
#         if not change:
#             p = obj.product
#             old_stock = p.stock
#             new_stock = old_stock + obj.quantity
#             if new_stock > 0:
#                 p.cost_price = (old_stock * p.cost_price + obj.quantity * obj.price) / new_stock
#             p.stock = new_stock
#             p.save()
#         super().save_model(request, obj, form, change)


# class SaleAdmin(BaseAdmin):
#     list_display = ('product', 'quantity', 'sell_price_display', 'total_price_display', 'profit_display')

#     def sell_price_display(self, obj):
#         return fmt_money(obj.sell_price)

#     def total_price_display(self, obj):
#         return fmt_money(obj.total_price)

#     def profit_display(self, obj):
#         return fmt_money(obj.profit)

#     def save_model(self, request, obj, form, change):
#         if not change:
#             p = obj.product
#             obj.total_price = obj.quantity * obj.sell_price
#             obj.profit = (obj.sell_price - p.cost_price) * obj.quantity
#             p.stock -= obj.quantity
#             p.save()
#         super().save_model(request, obj, form, change)


# class RepairAdmin(BaseAdmin):
#     list_display = ('id', 'device_model', 'cost_display', 'status_display')

#     def cost_display(self, obj):
#         return fmt_money(obj.cost)


# class RepairItemAdmin(BaseAdmin):
#     list_display = ('repair', 'product', 'quantity')


# class ExpenseAdmin(BaseAdmin):
#     list_display = ('title', 'amount_display', 'account', 'created_at')

#     def amount_display(self, obj):
#         return fmt_money(obj.amount)


# class TransactionAdmin(BaseAdmin):
#     list_display = ('account', 'type_display', 'amount_display', 'created_at')

#     def type_display(self, obj):
#         return '收入' if obj.type == 'income' else '支出'

#     def amount_display(self, obj):
#         return fmt_money(obj.amount)


# class IncomeTypeAdmin(BaseAdmin):
#     list_display = ('name', 'parent', 'status_display')
#     search_fields = ['name']


# class ExpenseTypeAdmin(BaseAdmin):
#     list_display = ('name', 'parent', 'status_display')
#     search_fields = ['name']


# class InitialAccountingAdmin(BaseAdmin):
#     list_display = ('account', 'initial_balance', 'initial_date')

#     def changelist_view(self, request, extra_context=None):
#         return redirect('admin:initial_accounting_choice')


# # ================== 自定义 AdminSite ==================
# class MyAdminSite(admin.AdminSite):
#     site_header = "手机维修管理系统"
#     site_title = "管理后台"
#     index_title = "数据总览"
#     index_template = 'admin/index.html'

#     def get_urls(self):
#         urls = super().get_urls()
#         custom_urls = [
#             path('initial-accounting/', self.admin_view(self.initial_accounting_choice), name='initial_accounting_choice'),
#             path('initial-stock/', self.admin_view(self.initial_stock), name='initial_stock'),
#             path('initial-receivable/', self.admin_view(self.initial_receivable), name='initial_receivable'),
#             path('initial-cash/', self.admin_view(self.initial_cash), name='initial_cash'),
#             path('initial-finance/', self.admin_view(self.initial_finance), name='initial_finance'),
#             path('product-category/', self.admin_view(self.category_list), name='category_list'),
#             path('product-category/<int:category_id>/', self.admin_view(self.category_list), name='category_list'),
#             path('category-add/', self.admin_view(self.category_add), name='category_add'),
#             path('category-add/<int:parent_id>/', self.admin_view(self.category_add), name='category_add'),
#             path('inventory/status/', self.admin_view(self.inventory_status), name='inventory_status'),
#         ]
#         return custom_urls + urls

#     def index(self, request, extra_context=None):
#         today = now().date()
#         today_sales = Sale.objects.filter(created_at__date=today).aggregate(total=Sum('total_price'))['total'] or 0
#         today_profit = Sale.objects.filter(created_at__date=today).aggregate(total=Sum('profit'))['total'] or 0
#         today_expense = Expense.objects.filter(created_at__date=today).aggregate(total=Sum('amount'))['total'] or 0

#         total_sales = Sale.objects.aggregate(total=Sum('total_price'))['total'] or 0
#         total_profit = Sale.objects.aggregate(total=Sum('profit'))['total'] or 0
#         total_expense = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0

#         last_7_days = []
#         last_7_days_sales = []
#         for i in range(6, -1, -1):
#             day = today - timedelta(days=i)
#             last_7_days.append(day.strftime('%m-%d'))
#             sales = Sale.objects.filter(created_at__date=day).aggregate(total=Sum('total_price'))['total'] or 0
#             last_7_days_sales.append(float(sales))

#         extra_context = extra_context or {}
#         extra_context.update({
#             'today_sales': today_sales,
#             'today_profit': today_profit,
#             'today_expense': today_expense,
#             'total_sales': total_sales,
#             'total_profit': total_profit,
#             'total_expense': total_expense,
#             'last_7_days': json.dumps(last_7_days),
#             'last_7_days_sales': json.dumps(last_7_days_sales),
#         })
#         return super().index(request, extra_context)

#     def initial_accounting_choice(self, request):
#         return views.initial_accounting_choice(request)

#     def initial_stock(self, request):
#         return views.initial_stock(request)

#     def initial_receivable(self, request):
#         return views.initial_receivable(request)

#     def initial_cash(self, request):
#         return views.initial_cash(request)

#     def initial_finance(self, request):
#         return views.initial_finance(request)

#     def category_list(self, request, category_id=None):
#         return views.category_list(request, category_id)

#     def category_add(self, request, parent_id=None):
#         return views.category_add(request, parent_id)

#     def inventory_status(self, request):
#         return views.inventory_status(request)


# # ================== 统一注册所有模型 ==================
# admin.site.register(Account, AccountAdmin)
# admin.site.register(Product, ProductAdmin)  # 只注册一次
# admin.site.register(ProductCategory, ProductCategoryAdmin)
# admin.site.register(ProductAttribute, ProductAttributeAdmin)
# admin.site.register(ProductAttributeValue, ProductAttributeValueAdmin)
# admin.site.register(ProductSKU, ProductSKUAdmin)
# admin.site.register(Supplier, SupplierAdmin)
# admin.site.register(StockIn, StockInAdmin)
# admin.site.register(Expense, ExpenseAdmin)
# admin.site.register(Sale, SaleAdmin)
# admin.site.register(Repair, RepairAdmin)
# admin.site.register(RepairItem, RepairItemAdmin)
# admin.site.register(Transaction, TransactionAdmin)
# admin.site.register(Store, StoreAdmin)
# admin.site.register(Staff, StaffAdmin)
# admin.site.register(IncomeType, IncomeTypeAdmin)
# admin.site.register(ExpenseType, ExpenseTypeAdmin)
# admin.site.register(InitialAccounting, InitialAccountingAdmin)