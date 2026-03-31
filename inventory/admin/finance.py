# inventory/admin/finance.py
from django.contrib import admin
from django.shortcuts import redirect
from ..models import Account, Transaction, IncomeType, ExpenseType, InitialAccounting
from .base import BaseAdmin, fmt_money


@admin.register(Account)
class AccountAdmin(BaseAdmin):
    list_display = ('name', 'balance_display')
    search_fields = ['name']

    def balance_display(self, obj):
        return fmt_money(obj.balance)


@admin.register(Transaction)
class TransactionAdmin(BaseAdmin):
    list_display = ('account', 'type_display', 'amount_display', 'created_at')

    def type_display(self, obj):
        return '收入' if obj.type == 'income' else '支出'

    def amount_display(self, obj):
        return fmt_money(obj.amount)


@admin.register(IncomeType)
class IncomeTypeAdmin(BaseAdmin):
    list_display = ('name', 'parent', 'status_display')
    search_fields = ['name']


@admin.register(ExpenseType)
class ExpenseTypeAdmin(BaseAdmin):
    list_display = ('name', 'parent', 'status_display')
    search_fields = ['name']


@admin.register(InitialAccounting)
class InitialAccountingAdmin(BaseAdmin):
    list_display = ('account', 'initial_balance', 'initial_date')

    def changelist_view(self, request, extra_context=None):
        return redirect('admin:initial_accounting_choice')