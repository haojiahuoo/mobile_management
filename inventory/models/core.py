# inventory/models/core.py
import re
import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from ..choices import ColorChoices
from ..validators import validate_color_hex



class ProductCategory(models.Model):
    """商品分类模型（支持无限级分类）"""
    name = models.CharField(max_length=100, verbose_name="分类名称")
    code = models.CharField(max_length=50, unique=True, verbose_name="分类编码", blank=True)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True,
        related_name='children', verbose_name="父级分类"
    )
    level = models.IntegerField(default=1, verbose_name="层级")
    sort_order = models.IntegerField(default=0, verbose_name="排序")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    # ========== 商品信息字段（仅在最终分类填写）==========
    brand = models.CharField(max_length=100, blank=True, default="", verbose_name="品牌")
    specification = models.CharField(max_length=200, blank=True, default="", verbose_name="规格")
    model = models.CharField(max_length=100, blank=True, default="", verbose_name="型号")
    retail_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="零售价"
    )
    remark = models.TextField(null=True, blank=True, verbose_name="商品备注")
    
    def get_full_path(self):
        """获取完整路径"""
        path_parts = []
        category = self
        while category:
            path_parts.insert(0, category.name)
            category = category.parent
        return ' / '.join(path_parts)
    
    def __str__(self):
        """在下拉框中显示完整路径"""
        return self.get_full_path()  # ✅ 只保留这一个
    
    class Meta:
        db_table = 'inventory_product_category'
        verbose_name = "商品分类"
        verbose_name_plural = "商品分类列表"
        ordering = ['level', 'sort_order', 'id']

    def save(self, *args, **kwargs):
        """保存时自动生成编码"""
        if not self.code:
            self.code = self._generate_code()
        super().save(*args, **kwargs)

    def _generate_code(self):
        """自动生成分类编码"""
        if self.parent:
            siblings = ProductCategory.objects.filter(parent=self.parent).exclude(id=self.id)
            last_code = siblings.order_by('-code').first()
            if last_code and last_code.code:
                last_num = int(last_code.code[-4:])
                new_num = last_num + 1
                return f"{self.parent.code}{new_num:04d}"
            else:
                return f"{self.parent.code}0001"
        else:
            siblings = ProductCategory.objects.filter(parent__isnull=True).exclude(id=self.id)
            last_code = siblings.order_by('-code').first()
            if last_code and last_code.code:
                last_num = int(last_code.code)
                new_num = last_num + 1
                return f"{new_num:04d}"
            else:
                return "0001"

    def get_full_code(self):
        """获取完整编码"""
        if self.parent:
            return f"{self.parent.get_full_code()}{self.code[-4:]}"
        return self.code

    def get_full_name(self):
        """获取完整名称"""
        if self.parent:
            return f"{self.parent.get_full_name()} > {self.name}"
        return self.name

    @property
    def productcategory_set(self):
        return self.children
    
    
    
# ================== 商品 ==================
class Product(models.Model):
    """商品模型"""
    
    code = models.CharField(
        max_length=50, unique=True, verbose_name="商品编号",
        blank=True, null=True, db_index=True,
        help_text="商品唯一编号，不填则自动生成"
    )
    brand = models.CharField(
        max_length=100, verbose_name="商品品牌",
        blank=True, default="", db_index=True
    )
    name = models.CharField(
        max_length=100, verbose_name="商品名称", db_index=True
    )
    color = models.CharField(
        max_length=20, choices=ColorChoices.choices,
        default=ColorChoices.NONE, blank=True, verbose_name="商品颜色"
    )
    color_hex = models.CharField(
        max_length=7, blank=True, default='',
        verbose_name="颜色代码(如:#FF0000)",
        validators=[validate_color_hex]
    )
    category = models.ForeignKey(
        ProductCategory, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name="商品分类",
        db_index=True, related_name='products'
    )
    supplier = models.ForeignKey(
        'Supplier', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name="供应商",
        db_index=True, related_name='products'
    )
    unit = models.CharField(max_length=20, default="个", verbose_name="单位")
    stock = models.IntegerField(default=0, verbose_name="库存数量", db_index=True)
    account = models.ForeignKey(
        'Account', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name="关联账户",
        db_index=True, related_name='products'
    )
    cost_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,  # ✅ 添加默认值
        verbose_name="成本价"
    )
    sell_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        default=0,  # ✅ 添加默认值
        verbose_name="售价"
    )
    
    remark = models.TextField(null=True, blank=True, verbose_name="备注")
    is_active = models.BooleanField(default=True, verbose_name="是否启用", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间", db_index=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = 'inventory_product'
        verbose_name = "商品"
        verbose_name_plural = "商品信息"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['brand', 'name'], name='product_brand_name_idx'),
            models.Index(fields=['category', 'code'], name='product_category_code_idx'),
        ]

    def __str__(self):
        """显示商品：编号 + 名称 + 完整分类路径 + 颜色"""
        color_part = f" [{self.get_color_display()}]" if self.color else ""
        
        # 获取完整分类路径
        if self.category:
            if hasattr(self.category, 'get_full_path'):
                category_path = self.category.get_full_path()
            else:
                # 手动构建分类路径
                path_parts = []
                cat = self.category
                while cat:
                    path_parts.insert(0, cat.name)
                    cat = cat.parent
                category_path = ' / '.join(path_parts)
            return f"[{self.code}] {self.name} ({category_path}){color_part}"
        
        return f"[{self.code}] {self.name}{color_part}"

    def get_color_display_value(self):
        """获取颜色显示值（用于admin显示）"""
        if self.color_hex:
            return mark_safe(
                '<span style="display:inline-block;width:20px;height:20px;background:{};border-radius:4px;"></span> {}'.format(
                    self.color_hex, self.get_color_display()
                )
            )
        return self.get_color_display()
    get_color_display_value.short_description = '颜色'

    # 编号生成方法
    def _generate_code_with_category(self):
        if not self.category:
            return None
        last_product = Product.objects.filter(
            category=self.category, code__isnull=False
        ).order_by('-code').first()
        if last_product and last_product.code:
            match = re.search(r'(\d{4})$', last_product.code)
            if match:
                try:
                    last_num = int(match.group(1))
                    new_num = last_num + 1
                    return f"{self.category.get_full_code()}{new_num:04d}"
                except (ValueError, TypeError):
                    pass
        return f"{self.category.get_full_code()}0001"

    def _generate_code_global(self):
        last_product = Product.objects.filter(code__isnull=False).order_by('-id').first()
        if last_product and last_product.code:
            match = re.search(r'(\d{8})$', last_product.code)
            if match:
                try:
                    last_num = int(match.group(1))
                    new_num = last_num + 1
                    return f"{new_num:08d}"
                except (ValueError, TypeError):
                    pass
        count = Product.objects.count()
        return f"{count + 1:08d}"

    def generate_code(self):
        if self.category:
            code = self._generate_code_with_category()
            if code:
                return code
        return self._generate_code_global()

    def clean(self):
        super().clean()
        
        # 确保数值字段有值
        if self.cost_price is None:
            self.cost_price = 0
        if self.sell_price is None:
            self.sell_price = 0
            
        if self.sell_price is not None and self.sell_price < self.cost_price:
            raise ValidationError({'sell_price': '售价不能低于成本价'})
        if self.stock < 0:
            raise ValidationError({'stock': '库存数量不能为负数'})
        if self.color_hex and not self.color:
            raise ValidationError({'color': '选择颜色后才可以填写颜色代码'})

    def save(self, *args, **kwargs):
        # 设置默认值
        if self.cost_price is None:
            self.cost_price = 0
        if self.sell_price is None:
            self.sell_price = 0
            
        if not self.code:
            self.code = self.generate_code()
        self.full_clean()
        super().save(*args, **kwargs)

    def update_stock(self, quantity: int):
        new_stock = self.stock + quantity
        if new_stock < 0:
            raise ValueError(f"库存不足，当前库存: {self.stock}，无法减少 {abs(quantity)}")
        self.stock = new_stock
        self.save(update_fields=['stock', 'updated_at'])

    def is_available(self) -> bool:
        return self.is_active and self.stock > 0

    @classmethod
    def get_active_products(cls):
        return cls.objects.filter(is_active=True)

    @classmethod
    def get_products_with_low_stock(cls, threshold: int = 10):
        return cls.objects.filter(is_active=True, stock__lte=threshold)


# ================== SKU 系统 ==================
class ProductAttribute(models.Model):
    """商品属性"""
    name = models.CharField(max_length=50, verbose_name="属性名称")

    class Meta:
        db_table = 'inventory_product_attribute'
        verbose_name = "商品属性"
        verbose_name_plural = "商品属性列表"

    def __str__(self):
        return self.name


class ProductAttributeValue(models.Model):
    """商品属性值"""
    attribute = models.ForeignKey(
        ProductAttribute, on_delete=models.CASCADE,
        related_name='values', verbose_name="属性"
    )
    value = models.CharField(max_length=50, verbose_name="属性值")

    class Meta:
        db_table = 'inventory_product_attribute_value'
        verbose_name = "商品属性值"
        verbose_name_plural = "商品属性值列表"

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


class ProductSKU(models.Model):
    """SKU 表"""
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        related_name='skus', verbose_name="商品"
    )
    attributes = models.JSONField(verbose_name="属性组合")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="售价")
    stock = models.IntegerField(default=0, verbose_name="库存数量")
    code = models.CharField(max_length=50, unique=True, verbose_name="SKU编号")
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sell_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = 'inventory_product_sku'
        verbose_name = "商品SKU"
        verbose_name_plural = "商品SKU列表"

    def __str__(self):
        return f"{self.product.name} - {self.attributes} ({self.code})"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = str(uuid.uuid4())[:8]
        super().save(*args, **kwargs)