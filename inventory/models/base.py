# inventory/models/base.py
from django.db import models


class BaseModel(models.Model):
    """基础抽象模型，包含通用字段"""
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    remark = models.TextField(null=True, blank=True, verbose_name="备注")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    
    class Meta:
        abstract = True