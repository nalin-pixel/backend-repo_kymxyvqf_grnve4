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
from typing import Optional
from datetime import datetime

# Example schemas (replace with your own):

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

# Attendance app schemas

class LoginEvent(BaseModel):
    """
    Login events for audit and email notifications
    Collection name: "loginevent"
    """
    email: str = Field(..., description="User email who attempted to login")
    success: bool = Field(True, description="Whether login was successful")
    message: Optional[str] = Field(None, description="Additional message or error detail")
    ip: Optional[str] = Field(None, description="Client IP address if available")
    user_agent: Optional[str] = Field(None, description="Client user agent if available")
    at: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp (UTC)")
