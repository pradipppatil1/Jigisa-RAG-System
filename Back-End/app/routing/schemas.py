"""
Pydantic schemas for the Semantic Router module.
"""

from pydantic import BaseModel
from typing import Optional


class RoutingResult(BaseModel):
    """Structured result returned by the RoutingService."""
    route_name: Optional[str] = None
    confidence: float = 0.0
    is_authorized: bool = False
    message: Optional[str] = None
    collections: list[str] = []


class RouteQueryRequest(BaseModel):
    """Request body for the /route endpoint."""
    query: str
    user_role: str
