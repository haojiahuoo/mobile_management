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


# ================== 商品管理 ==================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """商品管理"""
    
    change_form_template = 'admin/inventory/product/change_form.html'
    inlines = [ProductSKUInline]
    
    list_display = [
        'id', 'code', 'name', 'brand', 'category',
        'stock_display', 'cost_price', 'sell_price', 
        'show_profit_rate', 'is_active', 'generate_sku_btn'
    ]
    list_filter = ['category', 'supplier', 'is_active', 'color', ('created_at', admin.DateFieldListFilter)]
    search_fields = ['code', 'name', 'brand', 'remark']
    list_per_page = 20
    ordering = ['-created_at']
    
    fieldsets = None
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['category', 'supplier', 'account']
    list_editable = ['sell_price', 'is_active']
    save_on_top = True
    
    def stock_display(self, obj):
        try:
            stock = int(obj.stock)
            if stock <= 0:
                return mark_safe('<span style="color: #dc3545; font-weight: bold;">{} (缺货)</span>'.format(stock))
            elif stock <= 10:
                return mark_safe('<span style="color: #fd7e14; font-weight: bold;">{} (低库存)</span>'.format(stock))
            return mark_safe('<span style="color: #28a745; font-weight: bold;">{}</span>'.format(stock))
        except:
            return str(obj.stock)
    stock_display.short_description = '库存状态'
    stock_display.admin_order_field = 'stock'
    
    def show_profit_rate(self, obj):
        try:
            if obj.sell_price and obj.cost_price and float(obj.cost_price) > 0:
                cost = float(obj.cost_price)
                sell = float(obj.sell_price)
                rate = (sell - cost) / cost * 100
                
                if rate > 30:
                    color, icon = '#28a745', '📈'
                elif rate > 10:
                    color, icon = '#17a2b8', '📊'
                elif rate > 0:
                    color, icon = '#ffc107', '📉'
                else:
                    color, icon = '#dc3545', '⚠️'
                
                return mark_safe('<span style="color: {}; font-weight: bold;">{} {:.1f}%</span>'.format(color, icon, rate))
        except:
            pass
        return "-"
    show_profit_rate.short_description = '利润率'
    show_profit_rate.admin_order_field = 'sell_price'
    
    def generate_sku_btn(self, obj):
        return mark_safe(
            '<a class="button" href="/admin/inventory/product/{}/generate_sku/" '
            'style="background: #79aec8; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none;">⚙️ 生成SKU</a>'.format(obj.id)
        )
    generate_sku_btn.short_description = 'SKU操作'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:product_id>/generate_sku/', self.admin_site.admin_view(self.generate_sku_view), name='product-generate-sku'),
        ]
        return custom_urls + urls
    
    def generate_sku_view(self, request, product_id):
        product_obj = Product.objects.get(id=product_id)
        attributes = {"颜色": ["黑色", "白色"], "容量": ["128G", "256G"]}
        ProductSKU.objects.filter(product=product_obj).delete()
        skus = self.generate_sku(product_obj, attributes)
        ProductSKU.objects.bulk_create(skus)
        self.message_user(request, f'成功生成 {len(skus)} 个SKU')
        return redirect(f"/admin/inventory/product/{product_id}/change/")
    
    def generate_sku(self, product_obj, attributes_dict):
        keys = list(attributes_dict.keys())
        values = list(attributes_dict.values())
        all_combinations = list(cartesian_product(*values))
        skus = []
        for combo in all_combinations:
            attr_combo = dict(zip(keys, combo))
            sku_code = f"{product_obj.code}-{'-'.join([str(v)[:2] for v in combo])}"[:50]
            skus.append(ProductSKU(
                product=product_obj,
                attributes=attr_combo,
                code=sku_code,
                cost_price=product_obj.cost_price,
                sell_price=product_obj.sell_price,
                stock=0
            ))
        return skus
    
    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        category_id = request.GET.get('category')
        if category_id:
            initial['category'] = category_id
        return initial
    
    def save_model(self, request, obj, form, change):
        if not change:
            self.message_user(request, f'成功添加商品：{obj.name}', level='SUCCESS')
        else:
            self.message_user(request, f'成功更新商品：{obj.name}', level='SUCCESS')
        super().save_model(request, obj, form, change)
    
    actions = ['batch_generate_sku', 'batch_update_stock', 'batch_set_active']
    
    def batch_generate_sku(self, request, queryset):
        for product in queryset:
            attributes = {"颜色": ["黑色", "白色"], "容量": ["128G", "256G"]}
            ProductSKU.objects.filter(product=product).delete()
            skus = self.generate_sku(product, attributes)
            ProductSKU.objects.bulk_create(skus)
        self.message_user(request, f'成功为 {queryset.count()} 个商品生成SKU')
    batch_generate_sku.short_description = '批量生成SKU'
    
    def batch_update_stock(self, request, queryset):
        for product in queryset:
            product.stock += 10
            product.save()
        self.message_user(request, f'成功为 {queryset.count()} 个商品增加10个库存')
    batch_update_stock.short_description = '批量增加10个库存'
    
    def batch_set_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'成功启用 {updated} 个商品')
    batch_set_active.short_description = '批量启用商品'


# ================== 分类管理 ==================
@admin.register(ProductCategory)
class ProductCategoryAdmin(BaseAdmin):
    """商品分类管理"""
    
    list_display = (
        'id',
        'code', 
        'name',
        'brand_display',
        'specification_display',
        'model_display',
        'retail_price_display',
        'remark_display',
        'is_active',
        'category_action',
        'edit_button'          # 添加编辑按钮列
    )
    
    list_display_links = None
    list_filter = ('parent', 'is_active', 'level')
    search_fields = ['name', 'code', 'brand', 'model']
    list_editable = ('is_active',)
    list_per_page = 25
    ordering = ['level', 'id']
    
    # ========== 列表页只读显示方法 ==========
    def brand_display(self, obj):
        return obj.brand if obj.brand else '-'
    brand_display.short_description = '品牌'
    
    def specification_display(self, obj):
        return obj.specification if obj.specification else '-'
    specification_display.short_description = '规格'
    
    def model_display(self, obj):
        return obj.model if obj.model else '-'
    model_display.short_description = '型号'
    
    def retail_price_display(self, obj):
        if obj.retail_price:
            return f"¥{obj.retail_price}"
        return '-'
    retail_price_display.short_description = '零售价'
    
    def remark_display(self, obj):
        if obj.remark:
            return obj.remark[:50] + ('...' if len(obj.remark) > 50 else '')
        return '-'
    remark_display.short_description = '商品备注'
    
    # ========== 复选框列 ==========
    def category_action(self, obj):
        """显示"这是一个分类"复选框"""
        return mark_safe(
            '<div style="text-align: center;">'
            '<input type="checkbox" class="leaf-checkbox" data-id="{}" data-name="{}" {} '
            'style="width: 18px; height: 18px; cursor: pointer;">'
            '</div>'.format(
                obj.id,
                obj.name,
                'checked' if obj.is_leaf_category else ''
            )
        )
    category_action.short_description = '这是一个分类'
    
    # ========== 编辑按钮 ==========
    def edit_button(self, obj):
        """编辑按钮"""
        return mark_safe(
            '<a href="{}" class="edit-link" style="display: inline-block; background: #79aec8; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px; font-size: 12px;">'
            '✏️ 编辑'
            '</a>'.format(
                reverse('admin:inventory_productcategory_change', args=[obj.id])
            )
        )
    edit_button.short_description = '操作'
    
    # ========== 查询集处理 ==========
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        parent_id = request.GET.get('parent')
        if parent_id:
            qs = qs.filter(parent_id=parent_id)
        else:
            qs = qs.filter(parent__isnull=True)
        return qs
    
    # ========== 保存处理 ==========
    def save_model(self, request, obj, form, change):
        if not change:
            if obj.parent:
                obj.level = obj.parent.level + 1
            else:
                obj.level = 1
        
        if not obj.code:
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
    
    # ========== 表单页配置 ==========
    fieldsets = (
        ('分类信息', {
            'fields': ('name', 'parent', 'is_active', 'is_leaf_category'),
        }),
        ('商品信息', {
            'fields': ('brand', 'specification', 'model', 'retail_price', 'remark'),
            'classes': ('collapse',),
            'description': '这些信息将作为该分类下新商品的默认值'
        }),
    )
    
    readonly_fields = ['code', 'level', 'created_at']
    
    # ========== 面包屑导航和返回按钮 ==========
    def changelist_view(self, request, extra_context=None):
        from django.urls import reverse
        
        extra_context = extra_context or {}
        
        parent_id = request.GET.get('parent')
        
        if parent_id:
            try:
                current = ProductCategory.objects.get(id=parent_id)
                
                # 构建面包屑
                breadcrumb = []
                temp = current
                while temp:
                    breadcrumb.insert(0, {
                        'id': temp.id,
                        'name': temp.name,
                        'url': f'?parent={temp.id}'
                    })
                    temp = temp.parent
                breadcrumb.insert(0, {'id': None, 'name': '全部', 'url': '?'})
                extra_context['breadcrumb'] = breadcrumb
                extra_context['current_parent_name'] = current.name
                
                # 返回按钮
                if current.parent:
                    back_url = f'?parent={current.parent.id}'
                    back_text = f'返回 {current.parent.name}'
                else:
                    back_url = '?'
                    back_text = '返回全部'
                extra_context['back_button'] = mark_safe(
                    '<div style="margin-bottom: 15px;">'
                    '<a href="{}" class="button" style="background: #6c757d; color: white; padding: 5px 12px; text-decoration: none; border-radius: 3px;">'
                    '← {}'
                    '</a>'
                    '</div>'.format(back_url, back_text)
                )
                
            except Exception as e:
                print(f"Error: {e}")
                pass
        
        extra_context['custom_js'] = self._get_custom_js()
        
        return super().changelist_view(request, extra_context=extra_context)
    
    def _get_custom_js(self):
        return '''
        <script>
        console.log('=== 分类管理JS已加载 ===');
        
        document.addEventListener('DOMContentLoaded', function() {
            console.log('DOM加载完成');
            
            // 绑定双击事件
            const rows = document.querySelectorAll('#result_list tbody tr');
            console.log('找到 ' + rows.length + ' 行');
            
            rows.forEach((row, index) => {
                row.style.cursor = 'pointer';
                
                row.addEventListener('dblclick', function(e) {
                    // 如果点击的是编辑按钮或复选框，不触发双击
                    if (e.target.tagName === 'A' || e.target.type === 'checkbox') {
                        return;
                    }
                    
                    console.log('双击了第 ' + index + ' 行');
                    
                    const checkbox = this.querySelector('.leaf-checkbox');
                    if (!checkbox) {
                        console.log('未找到复选框');
                        return;
                    }
                    
                    const categoryId = checkbox.getAttribute('data-id');
                    const isLeaf = checkbox.checked;
                    
                    console.log('分类ID:', categoryId, '是否叶子:', isLeaf);
                    
                    if (isLeaf) {
                        window.location.href = '/admin/inventory/product/add/?category=' + categoryId;
                    } else {
                        window.location.href = '?parent=' + categoryId;
                    }
                });
            });
            
            // 绑定复选框变化事件
            const checkboxes = document.querySelectorAll('.leaf-checkbox');
            console.log('找到 ' + checkboxes.length + ' 个复选框');
            
            checkboxes.forEach(cb => {
                cb.addEventListener('change', function(e) {
                    e.stopPropagation();
                    const categoryId = this.getAttribute('data-id');
                    const isChecked = this.checked;
                    
                    console.log('复选框变化:', categoryId, isChecked);
                    
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
                            location.reload();
                        }
                    })
                    .catch(error => console.error('Error:', error));
                });
            });
        });
        
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
        </script>
        '''
    
    # ========== AJAX 视图 ==========
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('update-leaf-status/', self.admin_site.admin_view(self.update_leaf_status), name='update-leaf-status'),
        ]
        return custom_urls + urls
    
    def update_leaf_status(self, request):
        import json
        from django.http import JsonResponse
        
        if request.method == 'POST':
            data = json.loads(request.body)
            category_id = data.get('category_id')
            is_leaf = data.get('is_leaf')
            
            try:
                category = ProductCategory.objects.get(id=category_id)
                category.is_leaf_category = is_leaf
                if is_leaf:
                    category.children.all().delete()
                category.save()
                return JsonResponse({'success': True})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        
        return JsonResponse({'success': False, 'error': 'Invalid method'})
    
    class Media:
        js = ('admin/js/productcategory.js',)
        
        
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