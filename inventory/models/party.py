# inventory/models/party.py
from django.db import models
from .base import BaseModel


class Supplier(models.Model):
    """来往单位（供应商/客户）"""
    SUPPLIER_TYPE = (('supplier', '供应商'), ('customer', '客户'), ('both', '既是供应商也是客户'))

    name = models.CharField(max_length=100, verbose_name="单位名称")
    type = models.CharField(max_length=20, choices=SUPPLIER_TYPE, default='customer', verbose_name="单位类型")
    contact_person = models.CharField(max_length=50, null=True, blank=True, verbose_name="联系人")
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="联系电话")
    address = models.TextField(null=True, blank=True, verbose_name="地址")
    bank_name = models.CharField(max_length=100, null=True, blank=True, verbose_name="开户银行")
    bank_account = models.CharField(max_length=50, null=True, blank=True, verbose_name="银行账号")
    tax_number = models.CharField(max_length=50, null=True, blank=True, verbose_name="税号")
    remark = models.TextField(null=True, blank=True, verbose_name="备注")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = 'inventory_supplier'
        verbose_name = "来往单位"
        verbose_name_plural = "来往单位列表"

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class Store(models.Model):
    """门店信息"""
    name = models.CharField(max_length=100, verbose_name="门店名称")
    code = models.CharField(max_length=50, unique=True, verbose_name="门店编码")
    manager = models.CharField(max_length=50, null=True, blank=True, verbose_name="负责人")
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="联系电话")
    address = models.TextField(verbose_name="门店地址")
    business_hours = models.CharField(max_length=100, null=True, blank=True, verbose_name="营业时间")
    remark = models.TextField(null=True, blank=True, verbose_name="备注")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = 'inventory_store'
        verbose_name = "门店信息"
        verbose_name_plural = "门店信息列表"

    def __str__(self):
        return self.name


class Staff(models.Model):
    """职员信息"""
    POSITION = (
        ('manager', '经理'),
        ('cashier', '收银员'),
        ('salesman', '销售员'),
        ('technician', '技术员'),
        ('other', '其他'),
    )
    name = models.CharField(max_length=50, verbose_name="姓名")
    code = models.CharField(max_length=50, unique=True, verbose_name="工号")
    position = models.CharField(max_length=20, choices=POSITION, default='salesman', verbose_name="职位")
    phone = models.CharField(max_length=20, verbose_name="联系电话")
    id_card = models.CharField(max_length=18, null=True, blank=True, verbose_name="身份证号")
    hire_date = models.DateField(verbose_name="入职日期")
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="基本工资")
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="提成比例(%)")
    store = models.ForeignKey(Store, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="所属门店")
    remark = models.TextField(null=True, blank=True, verbose_name="备注")
    is_active = models.BooleanField(default=True, verbose_name="是否在职")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = 'inventory_staff'
        verbose_name = "职员信息"
        verbose_name_plural = "职员信息列表"

    def __str__(self):
        return f"{self.name} ({self.get_position_display()})"