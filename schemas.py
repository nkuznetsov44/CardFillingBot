from marshmallow_dataclass import class_schema
from entities import Fill, Category


FillSchema = class_schema(Fill)
CategorySchema = class_schema(Category)
