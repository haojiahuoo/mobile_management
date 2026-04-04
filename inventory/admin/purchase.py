# inventory/admin/purchase.py
from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.contrib import messages
from django import forms
from ..models import (
    PurchaseOrder, PurchaseOrderItem, 
    PurchaseReceipt, PurchaseReceiptItem,
    PurchaseReturn, PurchaseReturnItem,
    Product, Stock, StockRecord
)
from .base import BaseAdmin
from django.urls import reverse, path  # 添加 path
from django.http import JsonResponse
from django.urls import path
from django.shortcuts import redirect

class PurchaseOrderItemForm(forms.ModelForm):
    """采购订单明细表单 - 商品显示完整路径"""
    
    class Meta:
        model = PurchaseOrderItem
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'product' in self.fields:
            # 加宽选择框
            self.fields['product'].widget.attrs['style'] = 'width: 800px;'


class PurchaseOrderItemInline(admin.TabularInline):
    """采购订单明细内联"""
    model = PurchaseOrderItem
    form = PurchaseOrderItemForm
    extra = 1
    fields = ['product', 'quantity', 'unit_price', 'subtotal', 'remark']
    readonly_fields = ['subtotal']
    
    class Media:
        js = ('admin/js/vendor/jquery/jquery.min.js', 'js/purchase_inline.js',)


class PurchaseReceiptItemForm(forms.ModelForm):
    """采购入库单明细表单 - 商品显示完整路径"""
    
    class Meta:
        model = PurchaseReceiptItem
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'product' in self.fields:
            self.fields['product'].widget.attrs['style'] = 'width: 400px;'


class PurchaseReceiptItemInline(admin.TabularInline):
    """采购入库单明细内联"""
    model = PurchaseReceiptItem
    form = PurchaseReceiptItemForm
    extra = 0
    fields = ['product', 'quantity', 'unit_price', 'subtotal', 'remark']
    readonly_fields = ['subtotal']
    
    class Media:
        js = ('admin/js/vendor/jquery/jquery.min.js', 'js/purchase_receipt_inline.js',)


class PurchaseReturnItemInline(admin.TabularInline):
    """采购退货单明细内联"""
    model = PurchaseReturnItem
    extra = 1
    fields = ['product', 'quantity', 'unit_price', 'subtotal', 'remark']
    readonly_fields = ['subtotal']


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(BaseAdmin):
    """采购订单管理"""
    
    list_display = ['order_no', 'supplier', 'order_date', 'status', 'total_amount', 'action_buttons']
    list_filter = ['status', 'order_date', 'supplier']
    search_fields = ['order_no', 'supplier__name']
    list_per_page = 20
    readonly_fields = ['order_no', 'order_date', 'total_amount', 'created_at', 'updated_at']
    inlines = [PurchaseOrderItemInline]
    
    fieldsets = (
        ('订单信息', {
            'fields': ('order_no', 'supplier', 'expected_date', 'status')
        }),
        ('财务信息', {
            'fields': ('total_amount', 'paid_amount', 'account')
        }),
        ('其他信息', {
            'fields': ('remark', 'created_by', 'created_at', 'updated_at')
        }),
    )
    
    class Media:
        js = ('admin/js/vendor/jquery/jquery.min.js', 'admin/js/jquery.init.js', 'js/purchase_order.js',)
    
    def save_model(self, request, obj, form, change):
        if not change:
            from django.utils import timezone
            prefix = f"PO{timezone.now().strftime('%Y%m%d')}"
            last = PurchaseOrder.objects.filter(order_no__startswith=prefix).count()
            obj.order_no = f"{prefix}{last+1:04d}"
            obj.created_by = request.user.username
        super().save_model(request, obj, form, change)
    
    def action_buttons(self, obj):
        edit_url = reverse('admin:inventory_purchaseorder_change', args=[obj.id])
        edit_btn = f'<a href="{edit_url}" style="background: #79aec8; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">✏️ 编辑</a>'
        
        # 修改入库按钮，直接跳转到创建入库单的视图
        receipt_url = f'/admin/inventory/purchasereceipt/create-from-order/{obj.id}/'
        receipt_btn = f'<a href="{receipt_url}" style="background: #28a745; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px;">📦 一键入库</a>'
        
        return mark_safe(f'{edit_btn} {receipt_btn}')
    action_buttons.short_description = '操作'


@admin.register(PurchaseReceipt)
class PurchaseReceiptAdmin(BaseAdmin):
    """采购入库单管理"""
    
    list_display = ['receipt_no', 'purchase_order', 'receipt_date', 'total_amount', 'items_count', 'action_buttons']
    list_filter = ['receipt_date']
    search_fields = ['receipt_no', 'purchase_order__order_no']
    readonly_fields = ['receipt_no', 'receipt_date', 'total_amount', 'created_at']
    inlines = [PurchaseReceiptItemInline]
    
    fieldsets = (
        ('入库信息', {
            'fields': ('receipt_no', 'purchase_order')
        }),
        ('其他信息', {
            'fields': ('total_amount', 'remark', 'created_by', 'created_at')
        }),
    )
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('get-order-items/', self.admin_site.admin_view(self.get_order_items), name='get-order-items'),
            path('create-from-order/<int:order_id>/', self.admin_site.admin_view(self.create_from_order), name='create-from-order'),
        ]
        return custom_urls + urls
    
    def get_order_items(self, request):
        """获取采购订单的明细"""
        order_id = request.GET.get('order_id')
        if not order_id:
            return JsonResponse({'error': '未提供订单ID'}, status=400)
        
        try:
            order = PurchaseOrder.objects.get(id=order_id)
            items = []
            for item in order.items.all():
                items.append({
                    'product_id': item.product.id,
                    'product_name': str(item.product),
                    'quantity': item.quantity - item.received_quantity,
                    'unit_price': float(item.unit_price),
                })
            return JsonResponse({'success': True, 'items': items})
        except PurchaseOrder.DoesNotExist:
            return JsonResponse({'error': '采购订单不存在'}, status=404)
    
    def create_from_order(self, request, order_id):
        """根据采购订单直接创建入库单"""
        try:
            order = PurchaseOrder.objects.get(id=order_id)
            
            # 创建入库单
            from django.utils import timezone
            prefix = f"PR{timezone.now().strftime('%Y%m%d')}"
            last = PurchaseReceipt.objects.filter(receipt_no__startswith=prefix).count()
            receipt_no = f"{prefix}{last+1:04d}"
            
            receipt = PurchaseReceipt.objects.create(
                receipt_no=receipt_no,
                purchase_order=order,
                created_by=request.user.username
            )
            
            # 创建入库单明细
            for item in order.items.all():
                PurchaseReceiptItem.objects.create(
                    receipt=receipt,
                    product=item.product,
                    quantity=item.quantity - item.received_quantity,
                    unit_price=item.unit_price,
                )
            
            # 更新库存
            receipt.update_stock()
            
            messages.success(request, f'入库单 {receipt.receipt_no} 已根据采购订单创建并更新库存')
            return redirect(f'/admin/inventory/purchasereceipt/{receipt.id}/change/')
            
        except PurchaseOrder.DoesNotExist:
            messages.error(request, '采购订单不存在')
            return redirect('/admin/inventory/purchasereceipt/add/')
    
    def items_count(self, obj):
        count = obj.items.count()
        if count == 0:
            return mark_safe('<span style="color: red; font-weight: bold;">⚠️ 0条明细</span>')
        return mark_safe(f'<span style="color: green;">{count}条明细</span>')
    items_count.short_description = '明细数量'
    
    def save_model(self, request, obj, form, change):
        from django.utils import timezone
        
        if not change:
            prefix = f"PR{timezone.now().strftime('%Y%m%d')}"
            last = PurchaseReceipt.objects.filter(receipt_no__startswith=prefix).count()
            obj.receipt_no = f"{prefix}{last+1:04d}"
            obj.created_by = request.user.username
        
        super().save_model(request, obj, form, change)
        
        if obj.purchase_order:
            obj.purchase_order.status = 'received'
            obj.purchase_order.save()
    
    def save_related(self, request, form, formsets, change):
        """在保存所有关联对象（明细）后调用，更新库存"""
        super().save_related(request, form, formsets, change)
        
        obj = form.instance
        item_count = obj.items.count()
        
        if item_count > 0:
            try:
                for item in obj.items.all():
                    product = item.product
                    
                    stock, created = Stock.objects.get_or_create(
                        product=product,
                        defaults={'quantity': 0, 'min_quantity': 10, 'max_quantity': 1000}
                    )
                    
                    before_quantity = stock.quantity
                    stock.quantity += item.quantity
                    stock.last_inbound_date = obj.receipt_date
                    stock.save()
                    
                    StockRecord.objects.create(
                        product=product,
                        record_type='inbound',
                        quantity=item.quantity,
                        before_quantity=before_quantity,
                        after_quantity=stock.quantity,
                        reference_no=obj.receipt_no,
                        remark=f"采购入库单: {obj.receipt_no}",
                        created_by=obj.created_by
                    )
                    
                    product.stock = stock.quantity
                    product.save(update_fields=['stock'])
                
                messages.success(request, f'✅ 入库单 {obj.receipt_no} 保存成功！已更新 {item_count} 种商品的库存。')
            except Exception as e:
                messages.error(request, f'库存更新失败: {str(e)}')
        else:
            messages.warning(request, f'⚠️ 入库单 {obj.receipt_no} 没有明细，请添加明细后再保存！')
    
    def action_buttons(self, obj):
        edit_url = reverse('admin:inventory_purchasereceipt_change', args=[obj.id])
        edit_btn = f'<a href="{edit_url}" style="background: #79aec8; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px;">✏️ 编辑</a>'
        return mark_safe(edit_btn)
    action_buttons.short_description = '操作'


@admin.register(PurchaseReturn)
class PurchaseReturnAdmin(BaseAdmin):
    """采购退货单管理"""
    
    list_display = ['return_no', 'purchase_order', 'return_date', 'total_amount', 'action_buttons']
    list_filter = ['return_date']
    search_fields = ['return_no', 'purchase_order__order_no']
    readonly_fields = ['return_no', 'return_date', 'total_amount', 'created_at']
    inlines = [PurchaseReturnItemInline]
    
    fieldsets = (
        ('退货信息', {
            'fields': ('return_no', 'purchase_order', 'reason')
        }),
        ('其他信息', {
            'fields': ('total_amount', 'remark', 'created_by', 'created_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            from django.utils import timezone
            prefix = f"RT{timezone.now().strftime('%Y%m%d')}"
            last = PurchaseReturn.objects.filter(return_no__startswith=prefix).count()
            obj.return_no = f"{prefix}{last+1:04d}"
            obj.created_by = request.user.username
        super().save_model(request, obj, form, change)
    
    def action_buttons(self, obj):
        edit_url = reverse('admin:inventory_purchasereturn_change', args=[obj.id])
        edit_btn = f'<a href="{edit_url}" style="background: #79aec8; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px;">✏️ 编辑</a>'
        return mark_safe(edit_btn)
    action_buttons.short_description = '操作'