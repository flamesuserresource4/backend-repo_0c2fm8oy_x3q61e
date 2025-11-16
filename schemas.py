"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Example schemas (you can keep these or remove later):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Ticketing app schemas

class Event(BaseModel):
    """
    Events collection schema
    Collection name: "event"
    """
    title: str
    description: Optional[str] = None
    date: datetime
    venue: str
    rows: int = Field(..., gt=0, description="Number of seat rows")
    cols: int = Field(..., gt=0, description="Number of seats per row")
    price: float = Field(..., ge=0)

class Seat(BaseModel):
    """
    Seats collection schema (one document per seat per event)
    Collection name: "seat"
    """
    event_id: str
    row: str
    number: int
    status: str = Field("available", description="available | reserved | booked")

class Booking(BaseModel):
    """
    Bookings collection schema
    Collection name: "booking"
    """
    event_id: str
    seat_ids: List[str]
    name: str
    email: str
    total_amount: float
    status: str = Field("confirmed")
