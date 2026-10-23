from typing import Literal

from pydantic import BaseModel, Field, model_validator

Product = Literal["notebook", "pen", "lanyard", "marker", "folder", "badge"]


class LineItem(BaseModel):
    product: Product
    quantity: int = Field(ge=1, le=1000)


class Requirements(BaseModel):
    items: list[LineItem] = Field(min_length=1, max_length=6)
    budget_paise: int = Field(ge=100, le=10_000_000)
    deadline_hours: float = Field(gt=0, le=168)
    location: str = Field(default="Bengaluru campus", min_length=2, max_length=120)
    title: str = Field(default="Workshop supplies", min_length=1, max_length=100)

    @model_validator(mode="after")
    def unique_products(self):
        if len({item.product for item in self.items}) != len(self.items):
            raise ValueError("Combine duplicate products into one line item.")
        return self


class QuoteRequest(BaseModel):
    requirements: Requirements


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=3000)


class ConfirmRequest(BaseModel):
    option_id: str = Field(min_length=1, max_length=100)


class StockUpdate(BaseModel):
    stock: int = Field(ge=0, le=10000)


class AvailabilityUpdate(BaseModel):
    active: bool


class TrackingUpdate(BaseModel):
    status: Literal["packing", "dispatched", "delivered"]
    note: str = Field(default="", max_length=300)
