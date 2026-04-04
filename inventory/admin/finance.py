# inventory/admin/finance.py
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from ..models import Account, Transaction, IncomeType, ExpenseType, InitialAccounting
from .base import BaseAdmin, fmt_money


@admin.register(Account)
class AccountAdmin(BaseAdmin):
    list_display = ('name', 'balance_display', 'action_buttons')
    search_fields = ['name']
    
    def balance_display(self, obj):
        return fmt_money(obj.balance)
    balance_display.short_description = '余额'
    
    def action_buttons(self, obj):
        """操作按钮"""
        edit_url = reverse('admin:inventory_account_change', args=[obj.id])
        delete_url = reverse('admin:inventory_account_delete', args=[obj.id])
        
        edit_btn = f'<a href="{edit_url}" class="edit-btn" style="background: #79aec8; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">✏️ 编辑</a>'
        delete_btn = f'<a href="{delete_url}" class="delete-btn" style="background: #dc3545; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px;" onclick="return confirm(\'确定要删除【{obj.name}】吗？\')">🗑️ 删除</a>'
        
        return mark_safe(f'{edit_btn} {delete_btn}')
    action_buttons.short_description = '操作'


@admin.register(Transaction)
class TransactionAdmin(BaseAdmin):
    list_display = ('account', 'type_display', 'amount_display', 'created_at', 'action_buttons')
    
    def type_display(self, obj):
        return '收入' if obj.type == 'income' else '支出'
    type_display.short_description = '类型'
    
    def amount_display(self, obj):
        return fmt_money(obj.amount)
    amount_display.short_description = '金额'
    
    def action_buttons(self, obj):
        """操作按钮"""
        edit_url = reverse('admin:inventory_transaction_change', args=[obj.id])
        delete_url = reverse('admin:inventory_transaction_delete', args=[obj.id])
        
        edit_btn = f'<a href="{edit_url}" class="edit-btn" style="background: #79aec8; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">✏️ 编辑</a>'
        delete_btn = f'<a href="{delete_url}" class="delete-btn" style="background: #dc3545; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px;" onclick="return confirm(\'确定要删除这笔交易吗？\')">🗑️ 删除</a>'
        
        return mark_safe(f'{edit_btn} {delete_btn}')
    action_buttons.short_description = '操作'


@admin.register(IncomeType)
class IncomeTypeAdmin(BaseAdmin):
    list_display = ('name', 'parent_display', 'action_buttons')
    search_fields = ['name']
    
    def parent_display(self, obj):
        """显示父级的完整路径"""
        if obj.parent:
            if hasattr(obj.parent, 'get_full_path'):
                return obj.parent.get_full_path()
            return obj.parent.name
        return '-'
    parent_display.short_description = '父级分类'
    
    def action_buttons(self, obj):
        """操作按钮"""
        edit_url = reverse('admin:inventory_incometype_change', args=[obj.id])
        delete_url = reverse('admin:inventory_incometype_delete', args=[obj.id])
        
        edit_btn = f'<a href="{edit_url}" class="edit-btn" style="background: #79aec8; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">✏️ 编辑</a>'
        delete_btn = f'<a href="{delete_url}" class="delete-btn" style="background: #dc3545; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px;" onclick="return confirm(\'确定要删除【{obj.name}】吗？\')">🗑️ 删除</a>'
        
        return mark_safe(f'{edit_btn} {delete_btn}')
    action_buttons.short_description = '操作'


@admin.register(ExpenseType)
class ExpenseTypeAdmin(BaseAdmin):
    list_display = ('name', 'parent_display', 'action_buttons')
    search_fields = ['name']
   
    def parent_display(self, obj):
        """显示父级的完整路径"""
        if obj.parent:
            if hasattr(obj.parent, 'get_full_path'):
                return obj.parent.get_full_path()
            return obj.parent.name
        return '-'
    parent_display.short_description = '父级分类'
    
    def action_buttons(self, obj):
        """操作按钮"""
        edit_url = reverse('admin:inventory_expensetype_change', args=[obj.id])
        delete_url = reverse('admin:inventory_expensetype_delete', args=[obj.id])
        
        edit_btn = f'<a href="{edit_url}" class="edit-btn" style="background: #79aec8; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">✏️ 编辑</a>'
        delete_btn = f'<a href="{delete_url}" class="delete-btn" style="background: #dc3545; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px;" onclick="return confirm(\'确定要删除【{obj.name}】吗？\')">🗑️ 删除</a>'
        
        return mark_safe(f'{edit_btn} {delete_btn}')
    action_buttons.short_description = '操作'


@admin.register(InitialAccounting)
class InitialAccountingAdmin(BaseAdmin):
    list_display = ('account', 'initial_balance', 'initial_date', 'action_buttons')
    
    def initial_balance_display(self, obj):
        return fmt_money(obj.initial_balance)
    initial_balance_display.short_description = '期初余额'
    
    def action_buttons(self, obj):
        """操作按钮"""
        edit_url = reverse('admin:inventory_initialaccounting_change', args=[obj.id])
        delete_url = reverse('admin:inventory_initialaccounting_delete', args=[obj.id])
        
        edit_btn = f'<a href="{edit_url}" class="edit-btn" style="background: #79aec8; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">✏️ 编辑</a>'
        delete_btn = f'<a href="{delete_url}" class="delete-btn" style="background: #dc3545; color: white; padding: 4px 10px; text-decoration: none; border-radius: 3px;" onclick="return confirm(\'确定要删除这笔期初数据吗？\')">🗑️ 删除</a>'
        
        return mark_safe(f'{edit_btn} {delete_btn}')
    action_buttons.short_description = '操作'
    
    # def changelist_view(self, request, extra_context=None):
    #     # 改为直接使用URL路径
    #     return redirect('/admin/initial-accounting/')