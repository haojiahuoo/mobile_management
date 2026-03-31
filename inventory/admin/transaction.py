# inventory/admin/transaction.py
from django.contrib import admin
from ..models import StockIn, Sale, Repair, RepairItem, Expense
from .base import BaseAdmin, fmt_money


@admin.register(StockIn)
class StockInAdmin(BaseAdmin):
    list_display = ('product', 'quantity', 'price_display', 'total_cost', 'created_at')

    def price_display(self, obj):
        return fmt_money(obj.price)

    def total_cost(self, obj):
        return fmt_money(obj.quantity * obj.price)

    def save_model(self, request, obj, form, change):
        if not change:
            p = obj.product
            old_stock = p.stock
            new_stock = old_stock + obj.quantity
            if new_stock > 0:
                p.cost_price = (old_stock * p.cost_price + obj.quantity * obj.price) / new_stock
            p.stock = new_stock
            p.save()
        super().save_model(request, obj, form, change)


@admin.register(Sale)
class SaleAdmin(BaseAdmin):
    list_display = ('product', 'quantity', 'sell_price_display', 'total_price_display', 'profit_display')

    def sell_price_display(self, obj):
        return fmt_money(obj.sell_price)

    def total_price_display(self, obj):
        return fmt_money(obj.total_price)

    def profit_display(self, obj):
        return fmt_money(obj.profit)

    def save_model(self, request, obj, form, change):
        if not change:
            p = obj.product
            obj.total_price = obj.quantity * obj.sell_price
            obj.profit = (obj.sell_price - p.cost_price) * obj.quantity
            p.stock -= obj.quantity
            p.save()
        super().save_model(request, obj, form, change)


@admin.register(Repair)
class RepairAdmin(BaseAdmin):
    list_display = ('id', 'device_model', 'cost_display', 'status_display')

    def cost_display(self, obj):
        return fmt_money(obj.cost)


@admin.register(RepairItem)
class RepairItemAdmin(BaseAdmin):
    list_display = ('repair', 'product', 'quantity')


@admin.register(Expense)
class ExpenseAdmin(BaseAdmin):
    list_display = ('title', 'amount_display', 'account', 'created_at')

    def amount_display(self, obj):
        return fmt_money(obj.amount)