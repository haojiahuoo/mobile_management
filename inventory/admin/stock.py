# inventory/admin/stock.py
from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.contrib import messages
from django.shortcuts import redirect
from ..models import Stock, StockRecord, StockCheck, StockCheckItem, StockTransfer, StockTransferItem
from .base import BaseAdmin, fmt_money


class StockCheckItemInline(admin.TabularInline):
    model = StockCheckItem
    extra = 1
    fields = ['product', 'system_quantity', 'actual_quantity', 'difference', 'remark']
    readonly_fields = ['difference']


class StockTransferItemInline(admin.TabularInline):
    model = StockTransferItem
    extra = 1
    fields = ['product', 'quantity', 'remark']


@admin.register(Stock)
class StockAdmin(BaseAdmin):
    """库存管理"""
    list_display = ['product', 'quantity', 'min_quantity', 'max_quantity', 'status_display', 'action_buttons']
    list_filter = ['product__category']
    search_fields = ['product__name', 'product__code']
    readonly_fields = ['last_inbound_date', 'last_outbound_date', 'updated_at']
    
    fieldsets = (
        ('库存信息', {
            'fields': ('product', 'quantity', 'min_quantity', 'max_quantity')
        }),
        ('时间信息', {
            'fields': ('last_inbound_date', 'last_outbound_date', 'updated_at')
        }),
    )
    
    def status_display(self, obj):
        if obj.is_low_stock():
            return mark_safe('<span style="color: #d9534f;">⚠️ 低库存</span>')
        elif obj.is_high_stock():
            return mark_safe('<span style="color: #f0ad4e;">📦 高库存</span>')
        return mark_safe('<span style="color: #5cb85c;">✓ 正常</span>')
    status_display.short_description = '状态'
    
    def action_buttons(self, obj):
        edit_url = reverse('admin:inventory_stock_change', args=[obj.id])
        edit_btn = f'<a href="{edit_url}" style="background: #79aec8; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px;">✏️ 编辑</a>'
        return mark_safe(edit_btn)
    action_buttons.short_description = '操作'


@admin.register(StockRecord)
class StockRecordAdmin(BaseAdmin):
    """库存流水"""
    list_display = ['product', 'record_type', 'quantity', 'before_quantity', 'after_quantity', 'reference_no', 'created_at']
    list_filter = ['record_type', 'created_at']
    search_fields = ['product__name', 'reference_no']
    readonly_fields = ['before_quantity', 'after_quantity', 'created_at', 'created_by']
    
    fieldsets = (
        ('流水信息', {
            'fields': ('product', 'record_type', 'quantity', 'before_quantity', 'after_quantity')
        }),
        ('关联信息', {
            'fields': ('reference_no', 'remark', 'created_by', 'created_at')
        }),
    )


@admin.register(StockCheck)
class StockCheckAdmin(BaseAdmin):
    """库存盘点"""
    list_display = ['check_no', 'store', 'check_date', 'status', 'action_buttons']
    list_filter = ['status', 'check_date']
    search_fields = ['check_no', 'store__name']
    readonly_fields = ['check_no', 'created_at']
    inlines = [StockCheckItemInline]
    
    fieldsets = (
        ('盘点信息', {
            'fields': ('check_no', 'store', 'check_date', 'status')
        }),
        ('其他信息', {
            'fields': ('remark', 'created_by', 'created_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            from django.utils import timezone
            prefix = f"SC{timezone.now().strftime('%Y%m%d')}"
            last = StockCheck.objects.filter(check_no__startswith=prefix).count()
            obj.check_no = f"{prefix}{last+1:04d}"
            obj.created_by = request.user.username
        super().save_model(request, obj, form, change)
    
    def action_buttons(self, obj):
        edit_url = reverse('admin:inventory_stockcheck_change', args=[obj.id])
        edit_btn = f'<a href="{edit_url}" style="background: #79aec8; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px;">✏️ 编辑</a>'
        return mark_safe(edit_btn)
    action_buttons.short_description = '操作'


@admin.register(StockTransfer)
class StockTransferAdmin(BaseAdmin):
    """库存调拨"""
    list_display = ['transfer_no', 'from_store', 'to_store', 'transfer_date', 'status', 'action_buttons']
    list_filter = ['status', 'transfer_date']
    search_fields = ['transfer_no', 'from_store__name', 'to_store__name']
    readonly_fields = ['transfer_no', 'created_at']
    inlines = [StockTransferItemInline]
    
    fieldsets = (
        ('调拨信息', {
            'fields': ('transfer_no', 'from_store', 'to_store', 'transfer_date', 'status')
        }),
        ('其他信息', {
            'fields': ('remark', 'created_by', 'created_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            from django.utils import timezone
            prefix = f"ST{timezone.now().strftime('%Y%m%d')}"
            last = StockTransfer.objects.filter(transfer_no__startswith=prefix).count()
            obj.transfer_no = f"{prefix}{last+1:04d}"
            obj.created_by = request.user.username
        super().save_model(request, obj, form, change)
    
    def action_buttons(self, obj):
        edit_url = reverse('admin:inventory_stocktransfer_change', args=[obj.id])
        edit_btn = f'<a href="{edit_url}" style="background: #79aec8; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px;">✏️ 编辑</a>'
        return mark_safe(edit_btn)
    action_buttons.short_description = '操作'