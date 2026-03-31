# inventory/admin/site.py
from django.contrib import admin
from django.utils.timezone import now
from django.urls import path
from django.db.models import Sum
from datetime import timedelta
import json
from ..models import Sale, Expense
from .. import views


class MyAdminSite(admin.AdminSite):
    site_header = "手机维修管理系统"
    site_title = "管理后台"
    index_title = "数据总览"
    index_template = 'admin/index.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('initial-accounting/', self.admin_view(self.initial_accounting_choice), name='initial_accounting_choice'),
            path('initial-stock/', self.admin_view(self.initial_stock), name='initial_stock'),
            path('initial-receivable/', self.admin_view(self.initial_receivable), name='initial_receivable'),
            path('initial-cash/', self.admin_view(self.initial_cash), name='initial_cash'),
            path('initial-finance/', self.admin_view(self.initial_finance), name='initial_finance'),
            path('product-category/', self.admin_view(self.category_list), name='category_list'),
            path('product-category/<int:category_id>/', self.admin_view(self.category_list), name='category_list'),
            path('category-add/', self.admin_view(self.category_add), name='category_add'),
            path('category-add/<int:parent_id>/', self.admin_view(self.category_add), name='category_add'),
            path('inventory/status/', self.admin_view(self.inventory_status), name='inventory_status'),
        ]
        return custom_urls + urls

    def index(self, request, extra_context=None):
        today = now().date()
        today_sales = Sale.objects.filter(created_at__date=today).aggregate(total=Sum('total_price'))['total'] or 0
        today_profit = Sale.objects.filter(created_at__date=today).aggregate(total=Sum('profit'))['total'] or 0
        today_expense = Expense.objects.filter(created_at__date=today).aggregate(total=Sum('amount'))['total'] or 0

        total_sales = Sale.objects.aggregate(total=Sum('total_price'))['total'] or 0
        total_profit = Sale.objects.aggregate(total=Sum('profit'))['total'] or 0
        total_expense = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0

        last_7_days = []
        last_7_days_sales = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            last_7_days.append(day.strftime('%m-%d'))
            sales = Sale.objects.filter(created_at__date=day).aggregate(total=Sum('total_price'))['total'] or 0
            last_7_days_sales.append(float(sales))

        extra_context = extra_context or {}
        extra_context.update({
            'today_sales': today_sales,
            'today_profit': today_profit,
            'today_expense': today_expense,
            'total_sales': total_sales,
            'total_profit': total_profit,
            'total_expense': total_expense,
            'last_7_days': json.dumps(last_7_days),
            'last_7_days_sales': json.dumps(last_7_days_sales),
        })
        return super().index(request, extra_context)

    def initial_accounting_choice(self, request):
        return views.initial_accounting_choice(request)

    def initial_stock(self, request):
        return views.initial_stock(request)

    def initial_receivable(self, request):
        return views.initial_receivable(request)

    def initial_cash(self, request):
        return views.initial_cash(request)

    def initial_finance(self, request):
        return views.initial_finance(request)

    def category_list(self, request, category_id=None):
        return views.category_list(request, category_id)

    def category_add(self, request, parent_id=None):
        return views.category_add(request, parent_id)

    def inventory_status(self, request):
        return views.inventory_status(request)


admin_site = MyAdminSite(name='myadmin')