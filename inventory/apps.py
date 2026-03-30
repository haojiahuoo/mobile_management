# inventory/apps.py
from django.apps import AppConfig

class InventoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventory'
    verbose_name = '基本信息'  # 顶部菜单会显示"基本信息"而不是"inventory"