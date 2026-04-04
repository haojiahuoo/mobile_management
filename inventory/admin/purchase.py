# inventory/admin/purchase.py
from django.contrib import admin
from django.urls import reverse, path
from django.utils.safestring import mark_safe
from django.contrib import messages
from django import forms
from django.http import JsonResponse
from django.shortcuts import redirect
from ..models import (
    PurchaseOrder, PurchaseOrderItem, 
    PurchaseReceipt, PurchaseReceiptItem,
    PurchaseReturn, PurchaseReturnItem,
    Product, Stock, StockRecord
)
from .base import BaseAdmin


class PurchaseOrderItemForm(forms.ModelForm):
    """采购订单明细表单 - 商品显示完整路径"""
    
    class Meta:
        model = PurchaseOrderItem
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'product' in self.fields:
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


class PurchaseReturnItemForm(forms.ModelForm):
    """采购退货单明细表单"""
    
    class Meta:
        model = PurchaseReturnItem
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'product' in self.fields:
            self.fields['product'].widget.attrs['style'] = 'width: 400px;'


class PurchaseReturnItemInline(admin.TabularInline):
    """采购退货单明细内联"""
    model = PurchaseReturnItem
    form = PurchaseReturnItemForm
    extra = 1
    fields = ['product', 'quantity', 'unit_price', 'subtotal', 'remark']
    readonly_fields = ['subtotal']
    
    class Media:
        js = ('admin/js/vendor/jquery/jquery.min.js', 'admin/js/jquery.init.js', 'js/purchase_return_inline.js',)


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
        
        has_receipt = obj.receipts.exists()
        if has_receipt:
            receipt_btn = f'<span style="background: #6c757d; color: white; padding: 4px 10px; border-radius: 3px; margin-right: 5px; cursor: not-allowed;">✅ 已入库</span>'
        else:
            receipt_btn = f'<a href="/admin/inventory/purchasereceipt/create-from-order/{obj.id}/" style="background: #28a745; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">📦 一键入库</a>'
        
        has_return = obj.purchasereturn_set.exists()
        
        if has_return:
            return_btn = f'<span style="background: #6c757d; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px; cursor: not-allowed;" title="已退货">🗑️ 已退货</span>'
        elif has_receipt:
            return_btn = f'<a href="/admin/inventory/purchasereturn/create-from-order/{obj.id}/" style="background: #dc3545; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px;" onclick="return confirm(\'确定要退货吗？\')">🗑️ 一键退货</a>'
        else:
            return_btn = f'<span style="background: #6c757d; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px; cursor: not-allowed;" title="未入库不能退货">🗑️ 未入库</span>'
        
        return mark_safe(f'{edit_btn} {receipt_btn} {return_btn}')
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
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'purchase_order' in form.base_fields:
            form.base_fields['purchase_order'].required = False
        return form
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('create-from-order/<int:order_id>/', self.admin_site.admin_view(self.create_from_order), name='create-from-order'),
        ]
        return custom_urls + urls
    

    def create_from_order(self, request, order_id):
        """根据采购订单直接创建入库单"""
        try:
            order = PurchaseOrder.objects.get(id=order_id)
            
            if order.receipts.exists():
                messages.warning(request, f'采购订单 {order.order_no} 已经入库过了！')
                return redirect(f'/admin/inventory/purchaseorder/')
            
            from django.utils import timezone
            import uuid
            
            # 生成唯一的入库单号
            prefix = f"PR{timezone.now().strftime('%Y%m%d')}"
            
            # 尝试生成唯一编号，最多尝试5次
            receipt_no = None
            for i in range(5):
                if i == 0:
                    last = PurchaseReceipt.objects.filter(receipt_no__startswith=prefix).count()
                    candidate = f"{prefix}{last+1:04d}"
                else:
                    candidate = f"{prefix}{last+1:04d}{uuid.uuid4().hex[:4]}"
                
                if not PurchaseReceipt.objects.filter(receipt_no=candidate).exists():
                    receipt_no = candidate
                    break
            
            if not receipt_no:
                receipt_no = f"PR{timezone.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4]}"
            
            receipt = PurchaseReceipt.objects.create(
                receipt_no=receipt_no,
                purchase_order=order,
                created_by=request.user.username
            )
            
            for item in order.items.all():
                PurchaseReceiptItem.objects.create(
                    receipt=receipt,
                    product=item.product,
                    quantity=item.quantity - item.received_quantity,
                    unit_price=item.unit_price,
                )
            
            # 更新库存（增加）
            for item in receipt.items.all():
                product = item.product
                
                stock, created = Stock.objects.get_or_create(
                    product=product,
                    defaults={'quantity': 0, 'min_quantity': 10, 'max_quantity': 1000}
                )
                
                before_quantity = stock.quantity
                stock.quantity += item.quantity
                stock.last_inbound_date = receipt.receipt_date
                stock.save()
                
                StockRecord.objects.create(
                    product=product,
                    record_type='inbound',
                    quantity=item.quantity,
                    before_quantity=before_quantity,
                    after_quantity=stock.quantity,
                    reference_no=receipt.receipt_no,
                    remark=f"采购入库单: {receipt.receipt_no}",
                    created_by=receipt.created_by
                )
                
                product.stock = stock.quantity
                product.save(update_fields=['stock'])
            
            order.status = 'received'
            order.save()
            
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
        super().save_related(request, form, formsets, change)

        obj = form.instance

        # 🚨 防重复（数据库级别）
        if obj.is_stock_updated:
            return

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

                # ✅ 标记为已处理
                obj.is_stock_updated = True
                obj.save(update_fields=['is_stock_updated'])

                messages.success(request, f'✅ 入库成功')
            except Exception as e:
                messages.error(request, f'库存更新失败: {str(e)}')
        else:
            messages.warning(request, f'⚠️ 入库单 {obj.receipt_no} 没有明细，请添加明细后再保存！')
    
    def action_buttons(self, obj):
        edit_url = reverse('admin:inventory_purchasereceipt_change', args=[obj.id])
        edit_btn = f'<a href="{edit_url}" style="background: #79aec8; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">✏️ 编辑</a>'

        has_return = obj.purchasereturn_set.exists()

        if has_return:
            return_btn = '<span style="background: #6c757d; color: white; padding: 4px 10px; border-radius: 3px;">🗑️ 已退货</span>'
        else:
            return_btn = f'<a href="/admin/inventory/purchasereturn/create-from-receipt/{obj.id}/" style="background: #dc3545; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px;" onclick="return confirm(\'确定要退货吗？\')">🗑️ 一键退货</a>'

        return mark_safe(f'{edit_btn} {return_btn}')

    action_buttons.short_description = '操作'


@admin.register(PurchaseReturn)
class PurchaseReturnAdmin(BaseAdmin):
    """采购退货单管理"""
    
    list_display = ['return_no', 'purchase_order', 'purchase_receipt', 'return_date', 'total_amount', 'items_count', 'action_buttons']
    list_filter = ['return_date']
    search_fields = ['return_no', 'purchase_order__order_no', 'purchase_receipt__receipt_no']
    readonly_fields = ['return_no', 'return_date', 'total_amount', 'created_at']
    inlines = [PurchaseReturnItemInline]
    
    fieldsets = (
        ('退货信息', {
            'fields': ('return_no', 'purchase_order', 'purchase_receipt', 'reason')
        }),
        ('其他信息', {
            'fields': ('total_amount', 'remark', 'created_by', 'created_at')
        }),
    )
    
    def items_count(self, obj):
        count = obj.items.count()
        if count == 0:
            return mark_safe('<span style="color: red; font-weight: bold;">⚠️ 0条明细</span>')
        return mark_safe(f'<span style="color: green;">{count}条明细</span>')
    items_count.short_description = '明细数量'
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'purchase_order' in form.base_fields:
            form.base_fields['purchase_order'].required = False
        if 'purchase_receipt' in form.base_fields:
            form.base_fields['purchase_receipt'].required = False
        if 'reason' in form.base_fields:
            form.base_fields['reason'].required = False
        return form
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('create-from-order/<int:order_id>/', self.admin_site.admin_view(self.create_from_order), name='purchase-return-create-from-order'),
            path('create-from-receipt/<int:receipt_id>/', self.admin_site.admin_view(self.create_from_receipt), name='purchase-return-create-from-receipt'),
        ]
        return custom_urls + urls
    
    def create_from_order(self, request, order_id):
        """根据采购订单直接创建退货单"""
        try:
            order = PurchaseOrder.objects.get(id=order_id)
            
            if order.receipts.exists():
                messages.error(request, '❌ 已入库，请在入库单中退货！')
                return redirect('/admin/inventory/purchaseorder/')
            
            # 检查是否已经入库（没有入库不能退货）
            if not order.receipts.exists():
                messages.warning(request, f'采购订单 {order.order_no} 还未入库，不能退货！')
                return redirect(f'/admin/inventory/purchaseorder/')
            
            from django.utils import timezone
            prefix = f"RT{timezone.now().strftime('%Y%m%d')}"
            last = PurchaseReturn.objects.filter(return_no__startswith=prefix).count()
            return_no = f"{prefix}{last+1:04d}"
            
            return_order = PurchaseReturn.objects.create(
                return_no=return_no,
                purchase_order=order,
                created_by=request.user.username,
                _stock_updated=True
            )
            
            for item in order.items.all():
                PurchaseReturnItem.objects.create(
                    return_order=return_order,
                    product=item.product,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                )
            
            # 更新库存（减少）
            for item in return_order.items.all():
                product = item.product
                
                try:
                    stock = Stock.objects.get(product=product)
                    before_quantity = stock.quantity
                    stock.quantity -= item.quantity
                    if stock.quantity < 0:
                        stock.quantity = 0
                    stock.save()
                    
                    StockRecord.objects.create(
                        product=product,
                        record_type='return',
                        quantity=item.quantity,
                        before_quantity=before_quantity,
                        after_quantity=stock.quantity,
                        reference_no=return_order.return_no,
                        remark=f"采购退货单: {return_order.return_no}",
                        created_by=return_order.created_by
                    )
                    
                    product.stock = stock.quantity
                    product.save(update_fields=['stock'])
                except Stock.DoesNotExist:
                    pass
            
            messages.success(request, f'退货单 {return_order.return_no} 已根据采购订单创建并更新库存')
            return redirect(f'/admin/inventory/purchasereturn/{return_order.id}/change/')
            
        except PurchaseOrder.DoesNotExist:
            messages.error(request, '采购订单不存在')
            return redirect('/admin/inventory/purchasereturn/add/')
    
    def create_from_receipt(self, request, receipt_id):
        """根据入库单直接创建退货单"""
        try:
            receipt = PurchaseReceipt.objects.get(id=receipt_id)
            
            # 检查是否已经有退货单
            if receipt.purchasereturn_set.exists():
                messages.warning(request, f'入库单 {receipt.receipt_no} 已经退货过了！')
                return redirect(f'/admin/inventory/purchasereceipt/')
            
            from django.utils import timezone
            prefix = f"RT{timezone.now().strftime('%Y%m%d')}"
            last = PurchaseReturn.objects.filter(return_no__startswith=prefix).count()
            return_no = f"{prefix}{last+1:04d}"
            
            return_order = PurchaseReturn.objects.create(
                return_no=return_no,
                purchase_receipt=receipt,
                purchase_order=receipt.purchase_order,
                created_by=request.user.username,
                _stock_updated=True
            )
            
            for item in receipt.items.all():
                PurchaseReturnItem.objects.create(
                    return_order=return_order,
                    product=item.product,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                )
            
            # 更新库存（减少）
            for item in return_order.items.all():
                product = item.product
                
                try:
                    stock = Stock.objects.get(product=product)
                    before_quantity = stock.quantity
                    stock.quantity -= item.quantity
                    if stock.quantity < 0:
                        stock.quantity = 0
                    stock.save()
                    
                    StockRecord.objects.create(
                        product=product,
                        record_type='return',
                        quantity=item.quantity,
                        before_quantity=before_quantity,
                        after_quantity=stock.quantity,
                        reference_no=return_order.return_no,
                        remark=f"采购退货单: {return_order.return_no}",
                        created_by=return_order.created_by
                    )
                    
                    product.stock = stock.quantity
                    product.save(update_fields=['stock'])
                except Stock.DoesNotExist:
                    pass
            
            messages.success(request, f'退货单 {return_order.return_no} 已根据入库单创建并更新库存')
            return redirect(f'/admin/inventory/purchasereturn/{return_order.id}/change/')
            
        except PurchaseReceipt.DoesNotExist:
            messages.error(request, '入库单不存在')
            return redirect('/admin/inventory/purchasereturn/add/')
    
    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        obj = form.instance
        if getattr(obj, '_stock_updated', False):
            return
        # 手动添加时的库存更新逻辑（可以留空或添加）
    
    def action_buttons(self, obj):
        edit_url = reverse('admin:inventory_purchasereturn_change', args=[obj.id])
        edit_btn = f'<a href="{edit_url}" style="background: #79aec8; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px;">✏️ 编辑</a>'
        return mark_safe(edit_btn)
    action_buttons.short_description = '操作'