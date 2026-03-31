# inventory/models/transaction.py
from django.db import models
from .core import Product
from .finance import Account
from .party import Supplier


class StockIn(models.Model):
    """采购记录模型"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="商品")
    quantity = models.IntegerField(verbose_name="入库数量")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="进货单价")
    supplier = models.CharField(max_length=100, null=True, blank=True, verbose_name="供应商")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True, verbose_name="支付账户")

    class Meta:
        db_table = 'inventory_stockin'
        verbose_name = "采购记录"
        verbose_name_plural = "采购记录列表"

    def __str__(self):
        return f"{self.product.name} 入库 {self.quantity}"


class Sale(models.Model):
    """销售记录模型"""
    customer = models.ForeignKey(
        Supplier, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="客户", limit_choices_to={'type': 'customer'}
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="商品")
    quantity = models.IntegerField(verbose_name="销售数量")
    sell_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="销售单价")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, editable=False, verbose_name="总金额")
    profit = models.DecimalField(max_digits=10, decimal_places=2, editable=False, verbose_name="利润")
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True, verbose_name="收款账户")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = 'inventory_sale'
        verbose_name = "销售记录"
        verbose_name_plural = "销售记录列表"

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.sell_price
        if self.product and self.product.cost_price:
            cost_total = self.quantity * self.product.cost_price
            self.profit = self.total_price - cost_total
        else:
            self.profit = 0
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} 销售 {self.quantity}"


class Repair(models.Model):
    """维修记录模型"""
    STATUS = (('pending', '待维修'), ('repairing', '维修中'), ('done', '已完成'))

    customer = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, verbose_name="客户",
        limit_choices_to={'type': 'customer'}
    )
    device_model = models.CharField(max_length=100, verbose_name="设备型号")
    issue = models.TextField(verbose_name="故障描述")
    cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="维修费用")
    status = models.CharField(max_length=20, choices=STATUS, default='pending', verbose_name="维修状态")
    remark = models.TextField(null=True, blank=True, verbose_name="备注")
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="收款账户")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = 'inventory_repair'
        verbose_name = "维修记录"
        verbose_name_plural = "维修记录列表"

    def __str__(self):
        return f"{self.device_model} - {self.get_status_display()}"


class RepairItem(models.Model):
    """维修用料模型"""
    repair = models.ForeignKey(Repair, on_delete=models.CASCADE, verbose_name="维修记录")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="维修用料")
    quantity = models.IntegerField(verbose_name="使用数量")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = 'inventory_repairitem'
        verbose_name = "维修用料"
        verbose_name_plural = "维修用料记录"

    def __str__(self):
        return f"{self.repair.device_model} - {self.product.name} x{self.quantity}"


class Expense(models.Model):
    """支出记录模型"""
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True, verbose_name="支付账户")
    title = models.CharField(max_length=100, verbose_name="支出名称")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="金额")
    category = models.CharField(max_length=50, verbose_name="分类")
    remark = models.TextField(null=True, blank=True, verbose_name="备注")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = 'inventory_expense'
        verbose_name = "支出记录"
        verbose_name_plural = "支出记录列表"

    def __str__(self):
        return self.title