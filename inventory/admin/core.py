# inventory/admin/core.py
from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from itertools import product as cartesian_product
from ..models import Product, ProductCategory, ProductAttribute, ProductAttributeValue, ProductSKU
from .base import BaseAdmin
from ..models.core import ColorChoices  # 添加这一行
from django.urls import path, reverse
from django.http import JsonResponse
from .initial import initial_stock_setup
from django.http import HttpResponseRedirect
from django.contrib import messages

from django import forms
from decimal import Decimal

# ================== SKU Inline ==================
class ProductSKUInline(admin.TabularInline):
    """SKU 内联管理"""
    model = ProductSKU
    extra = 0
    fields = ['code', 'attributes', 'stock', 'sell_price', 'cost_price']
    readonly_fields = ['code']
    can_delete = True
    show_change_link = True
    
    def get_extra(self, request, obj=None, **kwargs):
        return 0

# ================== 商品表单 ==================
# 创建自定义表单
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
    
    def clean_sell_price(self):
        """确保售价不为空"""
        sell_price = self.cleaned_data.get('sell_price')
        if sell_price is None:
            return Decimal('0.00')
        return sell_price
    
    def clean_cost_price(self):
        """确保成本价不为空"""
        cost_price = self.cleaned_data.get('cost_price')
        if cost_price is None:
            return Decimal('0.00')
        return cost_price
    
    def clean_stock(self):
        """确保库存不为空"""
        stock = self.cleaned_data.get('stock')
        if stock is None:
            return 0
        return stock


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """商品管理"""
    
    # 使用自定义表单
    form = ProductForm
    
    list_display = ['code', 'name', 'brand', 'category_path', 'sell_price', 'stock_display', 'is_active', 'cost_price', 'stock', 'action_buttons']
    list_editable = ['cost_price', 'stock']  # 列表页直接编辑
    list_filter = ['category', 'supplier', 'is_active']
    search_fields = ['code', 'name', 'brand']
    list_per_page = 20
    ordering = ['-created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('code', 'name', 'brand', 'category', 'unit')
        }),
        ('价格信息', {
            'fields': ('sell_price', 'cost_price', 'stock')  # 添加成本价和库存
        }),
        ('其他信息', {
            'fields': ('supplier', 'account', 'color', 'color_hex', 'is_active', 'remark')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    # exclude = ['cost_price', 'stock']
    
    def action_buttons(self, obj):
        """操作按钮：编辑和删除"""
        # 编辑按钮
        edit_url = reverse('admin:inventory_product_change', args=[obj.id])
        edit_btn = f'<a href="{edit_url}" class="button edit-btn" style="background: #79aec8; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">✏️ 编辑</a>'
        
        # 删除按钮（检查是否可以删除）
        delete_url = reverse('admin:inventory_product_delete', args=[obj.id])
        if self.can_delete_object(obj):
            delete_btn = f'<a href="{delete_url}" class="button delete-btn" style="background: #dc3545; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px;" onclick="return confirm(\'确定要删除【{obj.name}】吗？\')">🗑️ 删除</a>'
        else:
            delete_btn = f'<span style="background: #6c757d; color: white; padding: 4px 10px; border-radius: 3px; cursor: not-allowed;" title="该商品有关联单据，无法删除">🚫 禁用删除</span>'
        
        return mark_safe(f'{edit_btn} {delete_btn}')
    action_buttons.short_description = '操作'
    action_buttons.allow_tags = True
    
    def can_delete_object(self, obj):
        """检查商品是否可以删除"""
        # 检查是否有采购单关联
        if hasattr(obj, 'stockin_set') and obj.stockin_set.exists():
            return False
        # 检查是否有销售单关联
        if hasattr(obj, 'sale_set') and obj.sale_set.exists():
            return False
        # 检查是否有维修单关联
        if hasattr(obj, 'repairitem_set') and obj.repairitem_set.exists():
            return False
        # 检查是否有SKU关联
        if hasattr(obj, 'skus') and obj.skus.exists():
            return False
        return True
    
    def has_delete_permission(self, request, obj=None):
        """重写删除权限"""
        if obj and not self.can_delete_object(obj):
            return False
        return super().has_delete_permission(request, obj)
    
    def delete_view(self, request, object_id, extra_context=None):
        """重写删除视图，添加提示"""
        obj = self.get_object(request, object_id)
        if obj and not self.can_delete_object(obj):
            messages.error(request, f'商品【{obj.name}】有关联单据，无法删除！')
            return HttpResponseRedirect(reverse('admin:inventory_product_changelist'))
        return super().delete_view(request, object_id, extra_context)
    
    def get_form(self, request, obj=None, **kwargs):
        """设置表单字段的初始值"""
        form = super().get_form(request, obj, **kwargs)
        # 为售价设置默认值
        if 'sell_price' in form.base_fields:
            form.base_fields['sell_price'].initial = Decimal('0.00')
            form.base_fields['sell_price'].widget.attrs['step'] = '0.01'
            form.base_fields['sell_price'].widget.attrs['min'] = '0'
        return form
    
    def save_model(self, request, obj, form, change):
        """保存时确保数值字段不为空"""
        if obj.sell_price is None:
            obj.sell_price = Decimal('0.00')
        if obj.cost_price is None:
            obj.cost_price = Decimal('0.00')
        if obj.stock is None:
            obj.stock = 0
        super().save_model(request, obj, form, change)
    
    def category_path(self, obj):
        """获取商品分类的完整路径"""
        try:
            if obj and obj.category:
                names = []
                cat = obj.category
                while cat:
                    names.insert(0, cat.name)
                    cat = cat.parent
                return ' / '.join(names)
        except Exception as e:
            print(f"category_path error: {e}")
        return '-'
    category_path.short_description = '商品分类'
    
    def stock_display(self, obj):
        """库存显示（带预警）"""
        try:
            stock = obj.stock if obj.stock is not None else 0
            if stock <= 0:
                return f'{stock} (缺货)'
            elif stock <= 10:
                return f'{stock} (低库存)'
            return stock
        except Exception as e:
            print(f"stock_display error: {e}")
            return '0'
    stock_display.short_description = '库存'
    
    def get_urls(self):
        """添加初期建账URL"""
        urls = super().get_urls()
        custom_urls = [
            path('initial-stock-setup/', self.admin_site.admin_view(initial_stock_setup), 
                name='product-initial-stock-setup'),
        ]
        return custom_urls + urls
    
# ================== 商品分类管理 ==================
# inventory/admin/core.py
from django.contrib import admin
from django.utils.safestring import mark_safe
from ..models import ProductCategory


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    """商品分类管理 - 标准Admin页面（无树形导航）"""
    
    # 列表页显示字段 - 将 'parent' 改为 'parent_display'
    list_display = ['id', 'code', 'name', 'parent_display', 'level', 'is_active', 'action_buttons']
    
    # 列表页筛选器
    list_filter = ['parent', 'is_active', 'level']
    
    # 搜索字段
    search_fields = ['name', 'code']
    
    # 每页显示数量
    list_per_page = 20
    
    # 默认排序
    ordering = ['level', 'id']
    
    # 可编辑字段（列表页直接编辑）
    list_editable = ['is_active']
    
    # 表单页配置
    fieldsets = (
        ('分类信息', {
            'fields': ('name', 'code', 'parent', 'level', 'is_active')
        }),
        ('商品信息（默认值）', {
            'fields': ('brand', 'specification', 'model', 'retail_price', 'remark'),
            'classes': ('collapse',),
            'description': '这些信息将作为该分类下新商品的默认值'
        }),
    )
    
    # 只读字段
    readonly_fields = ['code', 'level']
    
    def parent_display(self, obj):
        """显示父级分类的完整路径"""
        if obj.parent:
            if hasattr(obj.parent, 'get_full_path'):
                return obj.parent.get_full_path()
            # 手动构建路径
            path_parts = []
            cat = obj.parent
            while cat:
                path_parts.insert(0, cat.name)
                cat = cat.parent
            return ' / '.join(path_parts)
        return '-'
    parent_display.short_description = '父级分类'
    parent_display.admin_order_field = 'parent__name'
    
    
    def action_buttons(self, obj):
        """操作按钮：编辑和删除"""
        # 编辑按钮
        edit_url = reverse('admin:inventory_productcategory_change', args=[obj.id])
        edit_btn = f'<a href="{edit_url}" class="button edit-btn" style="background: #79aec8; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">✏️ 编辑</a>'
        
        # 删除按钮（检查是否可以删除）
        delete_url = reverse('admin:inventory_productcategory_delete', args=[obj.id])
        if self.can_delete_object(obj):
            delete_btn = f'<a href="{delete_url}" class="button delete-btn" style="background: #dc3545; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px;" onclick="return confirm(\'确定要删除【{obj.name}】及其所有子分类吗？\')">🗑️ 删除</a>'
        else:
            delete_btn = f'<span style="background: #6c757d; color: white; padding: 4px 10px; border-radius: 3px; cursor: not-allowed;" title="该分类下有商品，无法删除">🚫 禁用删除</span>'
        
        return mark_safe(f'{edit_btn} {delete_btn}')
    action_buttons.short_description = '操作'
    
    def can_delete_object(self, obj):
        """检查分类是否可以删除"""
        # 检查是否有子分类
        if obj.children.exists():
            return False
        # 检查分类下是否有商品
        if hasattr(obj, 'products') and obj.products.exists():
            return False
        return True
    
    def has_delete_permission(self, request, obj=None):
        """重写删除权限"""
        if obj and not self.can_delete_object(obj):
            return False
        return super().has_delete_permission(request, obj)
    
    def delete_view(self, request, object_id, extra_context=None):
        """重写删除视图，添加提示"""
        obj = self.get_object(request, object_id)
        if obj:
            if obj.children.exists():
                messages.error(request, f'分类【{obj.name}】下有子分类，请先删除子分类！')
                return HttpResponseRedirect(reverse('admin:inventory_productcategory_changelist'))
            if hasattr(obj, 'products') and obj.products.exists():
                messages.error(request, f'分类【{obj.name}】下有商品，无法删除！')
                return HttpResponseRedirect(reverse('admin:inventory_productcategory_changelist'))
        return super().delete_view(request, object_id, extra_context)
    
    # 保存时自动处理
    def save_model(self, request, obj, form, change):
        """保存时自动处理层级和编码"""
        if not change:  # 新增
            if obj.parent:
                obj.level = obj.parent.level + 1
            else:
                obj.level = 1
        
        if not obj.code:  # 自动生成编码
            if obj.parent:
                siblings = ProductCategory.objects.filter(parent=obj.parent).exclude(id=obj.id)
                max_code = siblings.order_by('-code').first()
                if max_code and max_code.code:
                    last_num = int(max_code.code[-4:])
                    obj.code = f"{obj.parent.code}{(last_num + 1):04d}"
                else:
                    obj.code = f"{obj.parent.code}0001"
            else:
                siblings = ProductCategory.objects.filter(parent__isnull=True).exclude(id=obj.id)
                max_code = siblings.order_by('-code').first()
                if max_code and max_code.code:
                    last_num = int(max_code.code)
                    obj.code = f"{(last_num + 1):04d}"
                else:
                    obj.code = "0001"
        
        super().save_model(request, obj, form, change)
        
# ================== SKU 属性管理 ==================
@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(ProductAttributeValue)
class ProductAttributeValueAdmin(admin.ModelAdmin):
    list_display = ('attribute', 'value')
    list_filter = ('attribute',)
    search_fields = ('value',)
    ordering = ('attribute', 'value')


@admin.register(ProductSKU)
class ProductSKUAdmin(admin.ModelAdmin):
    list_display = ('code', 'product', 'attributes_display', 'stock')
    list_filter = ('product__category',)
    search_fields = ('code', 'product__name')
    readonly_fields = ('code',)
    
    def attributes_display(self, obj):
        if obj.attributes:
            return ', '.join([f"{k}:{v}" for k, v in obj.attributes.items()])
        return '-'
    attributes_display.short_description = '属性组合'