from pydantic import BaseModel


class UserInput(BaseModel):
    username: str


class SubcategoryCount(BaseModel):
    title: str
    subcategories_count: int


class TopProducts(BaseModel):
    product_name: str
    category_name: str
    total_quantity: int


class ClientOrderSum(BaseModel):
    name: str
    total_sum: float
