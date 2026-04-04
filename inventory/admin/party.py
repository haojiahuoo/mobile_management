# inventory/admin/party.py
from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe
from ..models import Supplier, Store, Staff
from .base import BaseAdmin


@admin.register(Supplier)
class SupplierAdmin(BaseAdmin):
    list_display = ('name', 'type_display', 'contact_person', 'phone', 'created_at', 'action_buttons')
    search_fields = ['name', 'contact_person', 'phone']

    def type_display(self, obj):
        return {'supplier': '供应商', 'customer': '客户', 'both': '供应商/客户'}.get(obj.type, obj.type)
    type_display.short_description = '类型'
    
    def action_buttons(self, obj):
        """操作按钮：编辑和删除"""
        edit_url = reverse('admin:inventory_supplier_change', args=[obj.id])
        delete_url = reverse('admin:inventory_supplier_delete', args=[obj.id])
        
        edit_btn = f'<a href="{edit_url}" class="edit-btn" style="background: #79aec8; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">✏️ 编辑</a>'
        delete_btn = f'<a href="{delete_url}" class="delete-btn" style="background: #dc3545; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px;" onclick="return confirm(\'确定要删除【{obj.name}】吗？\')">🗑️ 删除</a>'
        
        return mark_safe(f'{edit_btn} {delete_btn}')
    action_buttons.short_description = '操作'


@admin.register(Store)
class StoreAdmin(BaseAdmin):
    list_display = ('code', 'name', 'manager', 'phone', 'action_buttons')
    search_fields = ['code', 'name', 'manager']
    
    def action_buttons(self, obj):
        """操作按钮：编辑和删除"""
        edit_url = reverse('admin:inventory_store_change', args=[obj.id])
        delete_url = reverse('admin:inventory_store_delete', args=[obj.id])
        
        edit_btn = f'<a href="{edit_url}" class="edit-btn" style="background: #79aec8; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">✏️ 编辑</a>'
        delete_btn = f'<a href="{delete_url}" class="delete-btn" style="background: #dc3545; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px;" onclick="return confirm(\'确定要删除【{obj.name}】吗？\')">🗑️ 删除</a>'
        
        return mark_safe(f'{edit_btn} {delete_btn}')
    action_buttons.short_description = '操作'


@admin.register(Staff)
class StaffAdmin(BaseAdmin):
    list_display = ('code', 'name', 'position_display', 'store', 'action_buttons')
    search_fields = ['code', 'name']

    def position_display(self, obj):
        return {
            'manager': '经理',
            'cashier': '收银员',
            'salesman': '销售员',
            'technician': '技术员'
        }.get(obj.position, obj.position)
    position_display.short_description = '职位'
    
    def action_buttons(self, obj):
        """操作按钮：编辑和删除"""
        edit_url = reverse('admin:inventory_staff_change', args=[obj.id])
        delete_url = reverse('admin:inventory_staff_delete', args=[obj.id])
        
        edit_btn = f'<a href="{edit_url}" class="edit-btn" style="background: #79aec8; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">✏️ 编辑</a>'
        delete_btn = f'<a href="{delete_url}" class="delete-btn" style="background: #dc3545; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px;" onclick="return confirm(\'确定要删除【{obj.name}】吗？\')">🗑️ 删除</a>'
        
        return mark_safe(f'{edit_btn} {delete_btn}')
    action_buttons.short_description = '操作'