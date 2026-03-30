# mobile_management/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from inventory import views
from inventory.admin import admin_site

router = DefaultRouter()
router.register(r'products', views.ProductViewSet)

urlpatterns = [
    # 初期建账页面
    path('admin/initial-accounting/', views.initial_accounting_choice, name='initial_accounting_choice'),
    path('admin/initial-stock/', views.initial_stock, name='initial_stock'),
    path('admin/initial-receivable/', views.initial_receivable, name='initial_receivable'),
    path('admin/initial-cash/', views.initial_cash, name='initial_cash'),
    path('admin/initial-finance/', views.initial_finance, name='initial_finance'),
    
    # 商品分类管理
    path('admin/product-category/', views.category_list, name='category_list'),
    path('admin/product-category/<int:category_id>/', views.category_list, name='category_list'),
    path('admin/category-add/', views.category_add, name='category_add'),
    path('admin/category-add/<int:parent_id>/', views.category_add, name='category_add'),
    
    # 库存状态
    path('admin/inventory/status/', views.inventory_status, name='inventory_status'),
    
    # Django Admin
    path('admin/', admin_site.urls),
    path('api/', include(router.urls)),
]