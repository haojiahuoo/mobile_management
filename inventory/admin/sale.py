# inventory/admin/sale.py
from django.contrib import admin
from django.urls import reverse, path
from django.utils.safestring import mark_safe
from django.contrib import messages
from django import forms
from django.http import JsonResponse
from django.shortcuts import redirect
from ..models import (
    SaleOrder, SaleOrderItem, SaleDelivery, SaleDeliveryItem,
    SaleReturn, SaleReturnItem, Product, Stock, StockRecord
)
from .base import BaseAdmin


class SaleOrderItemForm(forms.ModelForm):
    class Meta:
        model = SaleOrderItem
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'product' in self.fields:
            self.fields['product'].widget.attrs['style'] = 'width: 400px;'


class SaleOrderItemInline(admin.TabularInline):
    model = SaleOrderItem
    form = SaleOrderItemForm
    extra = 1
    fields = ['product', 'quantity', 'unit_price', 'subtotal', 'remark']
    readonly_fields = ['subtotal']
    
    class Media:
        js = ('admin/js/vendor/jquery/jquery.min.js', 'js/sale_inline.js',)


class SaleDeliveryItemForm(forms.ModelForm):
    class Meta:
        model = SaleDeliveryItem
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'product' in self.fields:
            self.fields['product'].widget.attrs['style'] = 'width: 400px;'


class SaleDeliveryItemInline(admin.TabularInline):
    model = SaleDeliveryItem
    form = SaleDeliveryItemForm
    extra = 0
    fields = ['product', 'quantity', 'unit_price', 'subtotal', 'remark']
    readonly_fields = ['subtotal']
    
    class Media:
        js = ('admin/js/vendor/jquery/jquery.min.js', 'js/sale_delivery_inline.js',)


class SaleReturnItemForm(forms.ModelForm):
    class Meta:
        model = SaleReturnItem
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'product' in self.fields:
            self.fields['product'].widget.attrs['style'] = 'width: 400px;'


class SaleReturnItemInline(admin.TabularInline):
    model = SaleReturnItem
    form = SaleReturnItemForm
    extra = 1
    fields = ['product', 'quantity', 'unit_price', 'subtotal', 'remark']
    readonly_fields = ['subtotal']


@admin.register(SaleOrder)
class SaleOrderAdmin(BaseAdmin):
    list_display = ['order_no', 'customer', 'store', 'order_date', 'status', 'total_amount', 'action_buttons']
    list_filter = ['status', 'order_date', 'customer', 'store']
    search_fields = ['order_no', 'customer__name']
    list_per_page = 20
    readonly_fields = ['order_no', 'order_date', 'total_amount', 'created_at', 'updated_at']
    inlines = [SaleOrderItemInline]
    
    fieldsets = (
        ('订单信息', {
            'fields': ('order_no', 'customer', 'store', 'staff', 'expected_date', 'status')
        }),
        ('财务信息', {
            'fields': ('total_amount', 'paid_amount', 'account')
        }),
        ('其他信息', {
            'fields': ('remark', 'created_by', 'created_at', 'updated_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            from django.utils import timezone
            prefix = f"SO{timezone.now().strftime('%Y%m%d')}"
            last = SaleOrder.objects.filter(order_no__startswith=prefix).count()
            obj.order_no = f"{prefix}{last+1:04d}"
            obj.created_by = request.user.username
        super().save_model(request, obj, form, change)
    
    def action_buttons(self, obj):
        edit_url = reverse('admin:inventory_saleorder_change', args=[obj.id])
        edit_btn = f'<a href="{edit_url}" style="background: #79aec8; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">✏️ 编辑</a>'
        
        has_delivery = obj.deliveries.exists()
        if has_delivery:
            delivery_btn = f'<span style="background: #6c757d; color: white; padding: 4px 10px; border-radius: 3px; margin-right: 5px; cursor: not-allowed;">✅ 已出库</span>'
        else:
            delivery_btn = f'<a href="/admin/inventory/saledelivery/create-from-order/{obj.id}/" style="background: #28a745; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">📦 一键出库</a>'
        
        # 检查是否已经有退货单
        has_return = obj.salereturn_set.exists()
        
        if has_return:
            return_btn = f'<span style="background: #6c757d; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px; cursor: not-allowed;" title="已退货，不能再次退货">🗑️ 已退货</span>'
        else:
            return_btn = f'<a href="/admin/inventory/salereturn/create-from-order/{obj.id}/" style="background: #dc3545; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px;" onclick="return confirm(\'确定要退货吗？\')">🗑️ 一键退货</a>'
        
        return mark_safe(f'{edit_btn} {delivery_btn} {return_btn}')
    action_buttons.short_description = '操作'


@admin.register(SaleDelivery)
class SaleDeliveryAdmin(BaseAdmin):
    """销售出库单管理"""
    
    list_display = ['delivery_no', 'sale_order', 'delivery_date', 'total_amount', 'items_count', 'action_buttons']
    list_filter = ['delivery_date']
    search_fields = ['delivery_no', 'sale_order__order_no']
    readonly_fields = ['delivery_no', 'delivery_date', 'total_amount', 'created_at']
    inlines = [SaleDeliveryItemInline]
    
    fieldsets = (
        ('出库信息', {
            'fields': ('delivery_no', 'sale_order')
        }),
        ('其他信息', {
            'fields': ('total_amount', 'remark', 'created_by', 'created_at')
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'sale_order' in form.base_fields:
            form.base_fields['sale_order'].required = False
        return form
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('create-from-order/<int:order_id>/', self.admin_site.admin_view(self.create_from_order), name='sale-delivery-create-from-order'),
        ]
        return custom_urls + urls
    
    def create_from_order(self, request, order_id):
        """根据销售订单直接创建出库单"""
        try:
            order = SaleOrder.objects.get(id=order_id)
            
            if order.deliveries.exists():
                messages.warning(request, f'销售订单 {order.order_no} 已经出库过了！')
                return redirect(f'/admin/inventory/saleorder/')
            
            # 检查库存是否充足
            insufficient_stock = []
            for item in order.items.all():
                try:
                    stock = Stock.objects.get(product=item.product)
                    if stock.quantity < item.quantity:
                        insufficient_stock.append(f"{item.product.name} (需要: {item.quantity}, 库存: {stock.quantity})")
                except Stock.DoesNotExist:
                    insufficient_stock.append(f"{item.product.name} (需要: {item.quantity}, 库存: 0)")
            
            if insufficient_stock:
                messages.error(request, f'以下商品库存不足，无法出库：<br>{"<br>".join(insufficient_stock)}')
                return redirect(f'/admin/inventory/saleorder/')
            
            from django.utils import timezone
            import uuid
            
            # 生成唯一的出库单号
            prefix = f"SD{timezone.now().strftime('%Y%m%d')}"
            
            # 尝试生成唯一编号，最多尝试5次
            delivery_no = None
            for i in range(5):
                if i == 0:
                    last = SaleDelivery.objects.filter(delivery_no__startswith=prefix).count()
                    candidate = f"{prefix}{last+1:04d}"
                else:
                    candidate = f"{prefix}{last+1:04d}{uuid.uuid4().hex[:4]}"
                
                if not SaleDelivery.objects.filter(delivery_no=candidate).exists():
                    delivery_no = candidate
                    break
            
            if not delivery_no:
                # 使用时间戳+随机数
                delivery_no = f"SD{timezone.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4]}"
            
            delivery = SaleDelivery.objects.create(
                delivery_no=delivery_no,
                sale_order=order,
                created_by=request.user.username
            )
            
            for item in order.items.all():
                SaleDeliveryItem.objects.create(
                    delivery=delivery,
                    product=item.product,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                )
            
            # 更新库存（减少）
            for item in delivery.items.all():
                product = item.product
                
                stock = Stock.objects.get(product=product)
                before_quantity = stock.quantity
                stock.quantity -= item.quantity
                if stock.quantity < 0:
                    stock.quantity = 0
                stock.save()
                
                StockRecord.objects.create(
                    product=product,
                    record_type='sale',
                    quantity=item.quantity,
                    before_quantity=before_quantity,
                    after_quantity=stock.quantity,
                    reference_no=delivery.delivery_no,
                    remark=f"销售出库单: {delivery.delivery_no}",
                    created_by=delivery.created_by
                )
                
                product.stock = stock.quantity
                product.save(update_fields=['stock'])
            
            order.status = 'completed'
            order.save()
            
            messages.success(request, f'出库单 {delivery.delivery_no} 已根据销售订单创建并更新库存')
            return redirect(f'/admin/inventory/saledelivery/{delivery.id}/change/')
            
        except SaleOrder.DoesNotExist:
            messages.error(request, '销售订单不存在')
            return redirect('/admin/inventory/saledelivery/add/')
    
    def items_count(self, obj):
        count = obj.items.count()
        if count == 0:
            return mark_safe('<span style="color: red; font-weight: bold;">⚠️ 0条明细</span>')
        return mark_safe(f'<span style="color: green;">{count}条明细</span>')
    items_count.short_description = '明细数量'
    
    def save_model(self, request, obj, form, change):
        from django.utils import timezone
        if not change:
            prefix = f"SD{timezone.now().strftime('%Y%m%d')}"
            last = SaleDelivery.objects.filter(delivery_no__startswith=prefix).count()
            obj.delivery_no = f"{prefix}{last+1:04d}"
            obj.created_by = request.user.username
        super().save_model(request, obj, form, change)
    
    def action_buttons(self, obj):
        edit_url = reverse('admin:inventory_saledelivery_change', args=[obj.id])
        edit_btn = f'<a href="{edit_url}" style="background: #79aec8; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">✏️ 编辑</a>'
        
        # 检查是否已经有退货单
        has_return = obj.salereturn_set.exists()
        
        if has_return:
            return_btn = f'<span style="background: #6c757d; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px; cursor: not-allowed;" title="已退货，不能再次退货">🗑️ 已退货</span>'
        else:
            return_btn = f'<a href="/admin/inventory/salereturn/create-from-delivery/{obj.id}/" style="background: #dc3545; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px;" onclick="return confirm(\'确定要退货吗？\')">🗑️ 一键退货</a>'
        
        return mark_safe(f'{edit_btn} {return_btn}')
    action_buttons.short_description = '操作'

@admin.register(SaleReturn)
class SaleReturnAdmin(BaseAdmin):
    list_display = ['return_no', 'sale_order', 'sale_delivery', 'return_date', 'total_amount', 'items_count', 'action_buttons']
    list_filter = ['return_date']
    search_fields = ['return_no', 'sale_order__order_no', 'sale_delivery__delivery_no']
    readonly_fields = ['return_no', 'return_date', 'total_amount', 'created_at']
    inlines = [SaleReturnItemInline]
    
    fieldsets = (
        ('退货信息', {
            'fields': ('return_no', 'sale_order', 'sale_delivery', 'reason')
        }),
        ('其他信息', {
            'fields': ('total_amount', 'remark', 'created_by', 'created_at')
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'sale_order' in form.base_fields:
            form.base_fields['sale_order'].required = False
        if 'sale_delivery' in form.base_fields:
            form.base_fields['sale_delivery'].required = False
        if 'reason' in form.base_fields:
            form.base_fields['reason'].required = False
        return form
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('create-from-order/<int:order_id>/', self.admin_site.admin_view(self.create_from_order), name='sale-return-create-from-order'),
            path('create-from-delivery/<int:delivery_id>/', self.admin_site.admin_view(self.create_from_delivery), name='sale-return-create-from-delivery'),
        ]
        return custom_urls + urls
    
    def create_from_order(self, request, order_id):
        """根据销售订单直接创建出库单"""
        try:
            order = SaleOrder.objects.get(id=order_id)
            
            if order.deliveries.exists():
                messages.warning(request, f'销售订单 {order.order_no} 已经出库过了！')
                return redirect(f'/admin/inventory/saleorder/')
            
            # 检查库存是否充足
            insufficient_stock = []
            for item in order.items.all():
                try:
                    stock = Stock.objects.get(product=item.product)
                    if stock.quantity < item.quantity:
                        insufficient_stock.append(f"{item.product.name} (需要: {item.quantity}, 库存: {stock.quantity})")
                except Stock.DoesNotExist:
                    insufficient_stock.append(f"{item.product.name} (需要: {item.quantity}, 库存: 0)")
            
            if insufficient_stock:
                messages.error(request, f'以下商品库存不足，无法出库：<br>{"<br>".join(insufficient_stock)}')
                return redirect(f'/admin/inventory/saleorder/')
            
            from django.utils import timezone
            prefix = f"SD{timezone.now().strftime('%Y%m%d')}"
            last = SaleDelivery.objects.filter(delivery_no__startswith=prefix).count()
            delivery_no = f"{prefix}{last+1:04d}"
            
            delivery = SaleDelivery.objects.create(
                delivery_no=delivery_no,
                sale_order=order,
                created_by=request.user.username
            )
            
            for item in order.items.all():
                SaleDeliveryItem.objects.create(
                    delivery=delivery,
                    product=item.product,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                )
            
            # 更新库存（减少）
            for item in delivery.items.all():
                product = item.product
                
                stock = Stock.objects.get(product=product)
                before_quantity = stock.quantity
                stock.quantity -= item.quantity
                if stock.quantity < 0:
                    stock.quantity = 0
                stock.save()
                
                StockRecord.objects.create(
                    product=product,
                    record_type='sale',
                    quantity=item.quantity,
                    before_quantity=before_quantity,
                    after_quantity=stock.quantity,
                    reference_no=delivery.delivery_no,
                    remark=f"销售出库单: {delivery.delivery_no}",
                    created_by=delivery.created_by
                )
                
                product.stock = stock.quantity
                product.save(update_fields=['stock'])
            
            order.status = 'completed'
            order.save()
            
            messages.success(request, f'出库单 {delivery.delivery_no} 已根据销售订单创建并更新库存')
            return redirect(f'/admin/inventory/saledelivery/{delivery.id}/change/')
            
        except SaleOrder.DoesNotExist:
            messages.error(request, '销售订单不存在')
            return redirect('/admin/inventory/saledelivery/add/')

    
    def create_from_delivery(self, request, delivery_id):
        """根据出库单直接创建退货单"""
        try:
            delivery = SaleDelivery.objects.get(id=delivery_id)
            
            # 检查是否已经有退货单
            if delivery.salereturn_set.exists():
                messages.warning(request, f'出库单 {delivery.delivery_no} 已经退货过了！')
                return redirect(f'/admin/inventory/saledelivery/')
            
            from django.utils import timezone
            prefix = f"SR{timezone.now().strftime('%Y%m%d')}"
            last = SaleReturn.objects.filter(return_no__startswith=prefix).count()
            return_no = f"{prefix}{last+1:04d}"
            
            return_order = SaleReturn.objects.create(
                return_no=return_no,
                sale_delivery=delivery,
                sale_order=delivery.sale_order,
                created_by=request.user.username,
                _stock_updated=True
            )
            
            for item in delivery.items.all():
                SaleReturnItem.objects.create(
                    return_order=return_order,
                    product=item.product,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                )
            
            # 更新库存（增加）
            for item in return_order.items.all():
                product = item.product
                
                stock, created = Stock.objects.get_or_create(
                    product=product,
                    defaults={'quantity': 0, 'min_quantity': 10, 'max_quantity': 1000}
                )
                
                before_quantity = stock.quantity
                stock.quantity += item.quantity
                stock.save()
                
                StockRecord.objects.create(
                    product=product,
                    record_type='sale_return',
                    quantity=item.quantity,
                    before_quantity=before_quantity,
                    after_quantity=stock.quantity,
                    reference_no=return_order.return_no,
                    remark=f"销售退货单: {return_order.return_no}",
                    created_by=return_order.created_by
                )
                
                product.stock = stock.quantity
                product.save(update_fields=['stock'])
            
            messages.success(request, f'退货单 {return_order.return_no} 已根据出库单创建并更新库存')
            return redirect(f'/admin/inventory/salereturn/{return_order.id}/change/')
            
        except SaleDelivery.DoesNotExist:
            messages.error(request, '出库单不存在')
            return redirect('/admin/inventory/salereturn/add/')
    
    def items_count(self, obj):
        count = obj.items.count()
        if count == 0:
            return mark_safe('<span style="color: red; font-weight: bold;">⚠️ 0条明细</span>')
        return mark_safe(f'<span style="color: green;">{count}条明细</span>')
    items_count.short_description = '明细数量'
    
    def save_model(self, request, obj, form, change):
        from django.utils import timezone
        if not change:
            prefix = f"SR{timezone.now().strftime('%Y%m%d')}"
            last = SaleReturn.objects.filter(return_no__startswith=prefix).count()
            obj.return_no = f"{prefix}{last+1:04d}"
            obj.created_by = request.user.username
        super().save_model(request, obj, form, change)
    
    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        obj = form.instance
        if getattr(obj, '_stock_updated', False):
            return
        # 手动添加时的库存更新逻辑
        # ...
    
    def action_buttons(self, obj):
        edit_url = reverse('admin:inventory_salereturn_change', args=[obj.id])
        edit_btn = f'<a href="{edit_url}" style="background: #79aec8; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px;">✏️ 编辑</a>'
        return mark_safe(edit_btn)
    action_buttons.short_description = '操作'
