from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from inventory import views

router = DefaultRouter()
router.register(r'products', views.ProductViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),  # 使用 Django 默认的 admin
    path('api/', include(router.urls)),
]