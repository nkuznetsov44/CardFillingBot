from marshmallow_dataclass import class_schema
from entities import Fill, Category, Income


FillSchema = class_schema(Fill)
CategorySchema = class_schema(Category)
IncomeSchema = class_schema(Income)
