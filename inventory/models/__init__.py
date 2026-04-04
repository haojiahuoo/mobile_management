# inventory/models/__init__.py
"""模型模块 - 按业务模块分组"""

from .base import BaseModel
from .core import (
    Product, ColorChoices, validate_color_hex,
    ProductCategory, ProductAttribute, ProductAttributeValue, ProductSKU
)
from .transaction import StockIn, Sale, Repair, RepairItem, Expense
from .party import Supplier, Store, Staff
from .finance import Account, Transaction, IncomeType, ExpenseType
from .accounting import InitialAccounting
from .purchase import (
    PurchaseOrder, PurchaseOrderItem,
    PurchaseReceipt, PurchaseReceiptItem,
    PurchaseReturn, PurchaseReturnItem
)
from .stock import Stock, StockRecord, StockCheck, StockCheckItem, StockTransfer, StockTransferItem

from .sale import (
    SaleOrder, SaleOrderItem, SaleDelivery, SaleDeliveryItem,
    SaleReturn, SaleReturnItem
)

__all__ = [
    'BaseModel',
    'Product', 'ColorChoices', 'validate_color_hex',
    'ProductCategory', 'ProductAttribute', 'ProductAttributeValue', 'ProductSKU',
    'StockIn', 'Sale', 'Repair', 'RepairItem', 'Expense',
    'Supplier', 'Store', 'Staff',
    'Account', 'Transaction', 'IncomeType', 'ExpenseType',
    'InitialAccounting',
    'PurchaseOrder', 'PurchaseOrderItem',
    'PurchaseReceipt', 'PurchaseReceiptItem',
    'PurchaseReturn', 'PurchaseReturnItem',
    'Stock', 'StockRecord', 'StockCheck', 'StockCheckItem', 'StockTransfer', 'StockTransferItem',
]