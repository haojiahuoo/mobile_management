# inventory/admin/base.py
from django.contrib import admin
from django.utils.html import format_html


def fmt_money(v):
    """格式化金额"""
    if v is None:
        return '-'
    try:
        return format_html('¥{:.2f}', float(v))
    except:
        return '-'


def fmt_status(v):
    """格式化状态"""
    return format_html(
        '<span class="status-badge {}">{}</span>',
        'status-active' if v else 'status-inactive',
        '启用' if v else '禁用'
    )


def fmt_stock(v):
    """格式化库存"""
    if v <= 0:
        return format_html('<span class="stock-out">⚠️ 缺货 ({})</span>', v)
    elif v < 10:
        return format_html('<span class="stock-low">⚠️ 低库存 ({})</span>', v)
    return format_html('<span class="stock-ok">✓ {}</span>', v)


class BaseAdmin(admin.ModelAdmin):
    """基础 Admin 类"""
    list_per_page = 25

    def status_display(self, obj):
        if hasattr(obj, 'is_active'):
            return fmt_status(obj.is_active)
        return '-'
    status_display.short_description = '状态'