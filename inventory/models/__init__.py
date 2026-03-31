# inventory/models/__init__.py
"""模型模块 - 按业务模块分组"""

# 基础模型
from .base import BaseModel

# 核心业务
from .core import (
    Product, ColorChoices, validate_color_hex,
    ProductCategory, ProductAttribute, ProductAttributeValue, ProductSKU
)

# 交易相关
from .transaction import (
    StockIn, Sale, Repair, RepairItem, Expense
)

# 参与方
from .party import (
    Supplier, Store, Staff
)

# 财务
from .finance import (
    Account, Transaction, IncomeType, ExpenseType
)

# 建账
from .accounting import (
    InitialAccounting
)

__all__ = [
    'BaseModel',
    'Product', 'ColorChoices', 'validate_color_hex',
    'ProductCategory', 'ProductAttribute', 'ProductAttributeValue', 'ProductSKU',
    'StockIn', 'Sale', 'Repair', 'RepairItem', 'Expense',
    'Supplier', 'Store', 'Staff',
    'Account', 'Transaction', 'IncomeType', 'ExpenseType',
    'InitialAccounting',
]