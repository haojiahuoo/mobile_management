# inventory/admin/party.py
from django.contrib import admin
from ..models import Supplier, Store, Staff
from .base import BaseAdmin


@admin.register(Supplier)
class SupplierAdmin(BaseAdmin):
    list_display = ('name', 'type_display', 'contact_person', 'phone', 'created_at')
    search_fields = ['name', 'contact_person', 'phone']

    def type_display(self, obj):
        return {'supplier': '供应商', 'customer': '客户', 'both': '供应商/客户'}.get(obj.type, obj.type)
    type_display.short_description = '类型'


@admin.register(Store)
class StoreAdmin(BaseAdmin):
    list_display = ('code', 'name', 'manager', 'phone', 'status_display')
    search_fields = ['code', 'name', 'manager']


@admin.register(Staff)
class StaffAdmin(BaseAdmin):
    list_display = ('code', 'name', 'position_display', 'store', 'status_display')
    search_fields = ['code', 'name']

    def position_display(self, obj):
        return {
            'manager': '经理',
            'cashier': '收银员',
            'salesman': '销售员',
            'technician': '技术员'
        }.get(obj.position, obj.position)
    position_display.short_description = '职位'