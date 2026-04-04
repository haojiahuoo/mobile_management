# inventory/models/finance.py
from django.db import models


class Account(models.Model):
    """账户模型"""
    name = models.CharField(max_length=100, verbose_name="账户名称")
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="余额")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = 'inventory_account'
        verbose_name = "账户"
        verbose_name_plural = "账户信息列表"

    def __str__(self):
        return self.name


class Transaction(models.Model):
    """交易流水模型"""
    TRANSACTION_TYPE = (('income', '收入'), ('expense', '支出'))

    account = models.ForeignKey(Account, on_delete=models.CASCADE, verbose_name="账户")
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPE, verbose_name="类型")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="金额")
    description = models.CharField(max_length=255, null=True, blank=True, verbose_name="说明")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = 'inventory_transaction'
        verbose_name = "交易流水"
        verbose_name_plural = "交易流水记录"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.account.name} - {self.get_type_display()} {self.amount}元"


class IncomeType(models.Model):
    """收入类型"""
    name = models.CharField(max_length=50, verbose_name="收入类型名称")
    code = models.CharField(max_length=50, unique=True, verbose_name="类型编码")
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="父级类型")
    sort_order = models.IntegerField(default=0, verbose_name="排序")
    remark = models.TextField(null=True, blank=True, verbose_name="备注")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    def get_full_path(self):
        """获取完整路径"""
        path_parts = []
        category = self
        while category:
            path_parts.insert(0, category.name)
            category = category.parent
        return ' / '.join(path_parts)
    
    def __str__(self):
        """显示完整路径"""
        return self.get_full_path()  # ✅ 只保留这一个
    
    class Meta:
        db_table = 'inventory_income_type'
        verbose_name = "收入类型"
        verbose_name_plural = "收入类型列表"
        ordering = ['sort_order', 'id']


class ExpenseType(models.Model):
    """费用类型"""
    name = models.CharField(max_length=50, verbose_name="费用类型名称")
    code = models.CharField(max_length=50, unique=True, verbose_name="类型编码")
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="父级类型")
    sort_order = models.IntegerField(default=0, verbose_name="排序")
    remark = models.TextField(null=True, blank=True, verbose_name="备注")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    def get_full_path(self):
        """获取完整路径"""
        path_parts = []
        category = self
        while category:
            path_parts.insert(0, category.name)
            category = category.parent
        return ' / '.join(path_parts)
    
    def __str__(self):
        """显示完整路径"""
        return self.get_full_path()  # ✅ 只保留这一个
    
    class Meta:
        db_table = 'inventory_expense_type'
        verbose_name = "费用类型"
        verbose_name_plural = "费用类型列表"
        ordering = ['sort_order', 'id']

  