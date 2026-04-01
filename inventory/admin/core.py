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


# ================== 库存状态管理 ==================
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
            path('get_next_code/', self.admin_site.admin_view(self.get_next_code), name='product-get-next-code'),
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
        
        if obj.category:
            if not obj.brand:
                obj.brand = obj.category.brand
            if not obj.specification:
                obj.specification = obj.category.specification
                
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
    
    # 添加这个方法
    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        """传递分类数据到模板"""
        
        # 获取所有激活的分类（用于显示下拉框）
        categories = ProductCategory.objects.filter(is_active=True).order_by('level', 'id')
        context['categories'] = categories
        
        # 如果是新增页面且URL有category参数，传递当前选中的分类
        if add:
            category_id = request.GET.get('category')
            if category_id:
                try:
                    default_category = ProductCategory.objects.get(id=category_id)
                    context['default_category_id'] = category_id
                    context['default_category_name'] = default_category.name
                except ProductCategory.DoesNotExist:
                    pass
        
        return super().render_change_form(request, context, add, change, form_url, obj)

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        
        category_id = request.GET.get('category')
        if category_id:
            initial['category'] = category_id
        
        return initial

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        
        if request.GET.get('category'):
            readonly.append('category')
        
        return readonly
    
    def get_next_code(self, request):
        """获取下一个商品编号"""
        category_id = request.GET.get('category_id')
        if category_id:
            try:
                category = ProductCategory.objects.get(id=category_id)
                # 获取该分类下的最大编号
                products = Product.objects.filter(category_id=category_id)
                max_code = None
                for product in products:
                    if product.code and product.code.startswith(f"{category.code}-"):
                        try:
                            num = int(product.code.split('-')[-1])
                            if max_code is None or num > max_code:
                                max_code = num
                        except:
                            continue
                
                next_number = 1 if max_code is None else max_code + 1
                return JsonResponse({
                    'category_code': category.code,
                    'next_number': next_number
                })
            except ProductCategory.DoesNotExist:
                pass
        
        return JsonResponse({'category_code': 'ERROR', 'next_number': 1})
    
    
# ================== 商品分类管理 ==================
@admin.register(ProductCategory)
class ProductCategoryAdmin(BaseAdmin):
    """商品分类管理"""
    
    # ========== 列表页显示字段 ==========
    list_display = (
        'id', 'code', 'name',
        'brand_display',      # 品牌（自定义显示）
        'specification_display',  # 规格
        'model_display',      # 型号
        'retail_price_display',   # 零售价
        'remark_display',     # 备注
        'edit_button'         # 编辑按钮
    )
    
    list_display_links = None                           # 禁用默认的链接
    # list_filter = ('parent', 'is_active', 'level')    # 右侧筛选器
    search_fields = ['name', 'code', 'brand', 'model']  # 可搜索字段
    list_editable = ()            # 不可直接编辑
    list_per_page = 25            # 每页显示25条
    ordering = ['level', 'id']    # 按层级和ID排序
    
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
            return obj.remark[:10] + ('...' if len(obj.remark) > 10 else '')
        return '-'
    remark_display.short_description = '商品备注'
    
    # ========== 编辑按钮 ==========
    def edit_button(self, obj):
        """编辑按钮"""
        from django.urls import reverse
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
        # parent_id = request.GET.get('parent')
        # if parent_id:
        #     qs = qs.filter(parent_id=parent_id)
        # else:
        #     qs = qs.filter(parent__isnull=True)
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
            #name(名称)、parent(父级分类)、is_active(是否启用)
            'fields': ('name', 'parent', 'is_active'), 
        }),
        ('商品信息', {
                        # 品牌、      规格、        型号、      零售价、       备注
            'fields': ('brand', 'specification', 'model', 'retail_price', 'remark'),
            'classes': ('collapse',),   # 这个分组默认折叠，点击才展开（适用于非核心信息）
            'description': '这些信息将作为该分类下新商品的默认值'
        }),
    )
    '''
    这些字段在编辑页面只能看不能改，通常用于：
        code：系统自动生成的编码
        level：自动计算的层级
        created_at：创建时间戳（不可修改）
    '''
    readonly_fields = ['code', 'level', 'created_at']
    
    # ========== 树形结构构建方法 ==========
    def _build_tree_html(self, categories, parent_id=None, level=0, expand_ids=None):
        """构建可折叠的树形结构HTML"""
        if expand_ids is None:
            expand_ids = []
        
        html = ''
        siblings = [cat for cat in categories if cat.parent_id == parent_id]
        
        for i, cat in enumerate(siblings):
            is_last = (i == len(siblings) - 1)
            children = categories.filter(parent_id=cat.id)
            has_children = children.exists()
            
            # 构建前缀
            prefix = ''
            if level > 0:
                prefix = ' ' * (level - 1)
                if is_last:
                    prefix += '└'
                else:
                    prefix += '├'
            
            # 判断是否默认展开
            is_expanded = cat.id in expand_ids
            display_style = 'block' if is_expanded else 'none'
            toggle_icon = '▼' if is_expanded else '▶'
            
            # 高亮当前选中的分类
            current_parent = self.request.GET.get('parent')
            is_active = str(cat.id) == current_parent
            
            # 文件夹图标
            folder_icon = '📁' if has_children else '📄'
            
            html += f'''
            <div class="tree-node" style="margin: 2px 0;">
                <div class="tree-item" style="white-space: nowrap; 
                    background: {is_active and '#e9ecef' or 'transparent'};
                    font-weight: {is_active and 'bold' or 'normal'};">
                    <span class="tree-prefix" style="color: #6c757d;">{prefix}</span>
                    <span class="tree-folder-icon">{folder_icon}</span>
                    <a href="?parent={cat.id}" data-id="{cat.id}" 
                    data-has-children="{str(has_children).lower()}"
                    class="tree-link {'has-children' if has_children else 'no-children'}"
                    style="text-decoration: none; color: {is_active and '#0d6efd' or '#2c3e50'};">
                        {cat.name}
                    </a>
                    {f'<span class="tree-toggle" data-id="{cat.id}" style="cursor: pointer; margin-left: 5px; color: #6c757d;">{toggle_icon}</span>' if has_children else ''}
                </div>
                <div class="tree-children" id="children_{cat.id}" style="display: {display_style}; margin-left: 20px;">
                    {self._build_tree_html(categories, cat.id, level + 1, expand_ids) if has_children else ''}
                </div>
            </div>
            '''
        
        return html
    
    def _get_category_path(self, category):
        """获取分类的完整路径"""
        path = []
        current = category
        while current:
            path.insert(0, current.name)
            current = current.parent
        return ' > '.join(path)
    
    # ========== 主视图 ==========
    def changelist_view(self, request, extra_context=None):
        """列表页视图 - 添加树形导航"""
        
        extra_context = extra_context or {}
        self.request = request
        
        # 获取需要展开的所有父级ID
        def _get_expand_ids(category):
            ids = []
            current = category
            while current:
                ids.append(current.id)
                current = current.parent
            return ids
        
        # 获取所有分类
        all_categories = ProductCategory.objects.filter(is_active=True).order_by('level', 'id')
        
        # 获取当前选中分类的完整路径
        parent_id = request.GET.get('parent')
        current_path = ''
        expand_ids = []
        
        if parent_id:
            try:
                current = ProductCategory.objects.get(id=parent_id)
                current_path = self._get_category_path(current)
                expand_ids = _get_expand_ids(current)
            except ProductCategory.DoesNotExist:
                pass
        
        # 构建树形结构（传入 expand_ids）
        category_tree = self._build_tree_html(all_categories, expand_ids=expand_ids)
        
        # 传递给模板
        extra_context['expand_ids'] = expand_ids
        extra_context['category_tree'] = mark_safe(category_tree)
        extra_context['current_path'] = current_path
        extra_context['custom_js'] = self._get_custom_js()
        
        return super().changelist_view(request, extra_context=extra_context)
    
    # ========== JavaScript ==========
    def _get_custom_js(self):
        return '''
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            // 加载保存的展开状态
            function loadExpandedState() {
                const expanded = localStorage.getItem('category_tree_expanded');
                if (expanded) {
                    const expandedIds = JSON.parse(expanded);
                    expandedIds.forEach(id => {
                        const childrenDiv = document.getElementById('children_' + id);
                        const toggleSpan = document.querySelector(`.tree-toggle[data-id="${id}"]`);
                        if (childrenDiv && toggleSpan) {
                            childrenDiv.style.display = 'block';
                            toggleSpan.textContent = '▼';
                        }
                    });
                }
            }
            
            document.querySelectorAll('.tree-link').forEach(link => {
                link.addEventListener('click', function(e) {
                    const hasChildren = this.getAttribute('data-has-children') === 'true';
                    
                    if (!hasChildren) {
                        e.preventDefault();  // 🚫 阻止跳转
                    }
                });
            });

            // 保存展开状态
            function saveExpandedState() {
                const expandedIds = [];
                document.querySelectorAll('.tree-children').forEach(children => {
                    if (children.style.display === 'block') {
                        const id = children.id.replace('children_', '');
                        expandedIds.push(id);
                    }
                });
                localStorage.setItem('category_tree_expanded', JSON.stringify(expandedIds));
            }
            
            // 绑定折叠/展开事件
            document.querySelectorAll('.tree-toggle').forEach(toggle => {
                toggle.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    const categoryId = this.getAttribute('data-id');
                    const childrenDiv = document.getElementById('children_' + categoryId);
                    
                    if (childrenDiv) {
                        if (childrenDiv.style.display === 'none' || !childrenDiv.style.display) {
                            childrenDiv.style.display = 'block';
                            this.textContent = '▼';
                        } else {
                            childrenDiv.style.display = 'none';
                            this.textContent = '▶';
                        }
                    }
                });
            });

            document.querySelectorAll('.tree-item a').forEach(link => {
                link.addEventListener('click', function(e) {
                    // 不阻止跳转
                });
            });

            // 为右侧列表添加双击事件
            const rows = document.querySelectorAll('#result_list tbody tr');
            rows.forEach(row => {
                row.style.cursor = 'pointer';
                row.addEventListener('dblclick', function(e) {
                    if (e.target.tagName === 'A' || e.target.closest('.edit-link')) {
                        return;
                    }
                    
                    const firstCell = this.querySelector('td:first-child');
                    if (!firstCell) return;
                    
                    let categoryId = firstCell.textContent.trim();
                    const idInput = this.querySelector('input[name="_selected_action"]');
                    if (idInput) {
                        categoryId = idInput.value;
                    }
                    
                    if (categoryId) {
                        const hasChildren = this.querySelector('.button') !== null;
                        if (hasChildren) {
                            window.location.href = '?parent=' + categoryId;
                        } else {
                            window.location.href = '/admin/inventory/product/add/?category=' + categoryId;
                        }
                    }
                });
            });
            
            // 自动滚动到当前选中的分类
            const activeLink = document.querySelector('.tree-item a[style*="font-weight: bold"]');
            if (activeLink) {
                activeLink.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        });
        </script>
        '''
     
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