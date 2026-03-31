# inventory/models/accounting.py
from django.db import models
from .finance import Account


class InitialAccounting(models.Model):
    """初期建账"""
    account = models.ForeignKey(Account, on_delete=models.CASCADE, verbose_name="账户")
    initial_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="期初余额")
    initial_date = models.DateField(verbose_name="期初日期")
    remark = models.TextField(null=True, blank=True, verbose_name="备注")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = 'inventory_initial_accounting'
        verbose_name = "初期建账"
        verbose_name_plural = "初期建立账户"
        unique_together = ['account', 'initial_date']

    def __str__(self):
        return f"{self.account.name} - 期初余额: {self.initial_balance} (日期: {self.initial_date})"