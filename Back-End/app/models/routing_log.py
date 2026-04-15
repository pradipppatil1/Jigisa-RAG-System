"""
SQLAlchemy model for the routing_logs table.

Every query that passes through the Semantic Router is persisted here
for auditability and analytics.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.sql import func

from app.core.database import Base


class RoutingLog(Base):
    __tablename__ = "routing_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user_id = Column(String(100), nullable=True, comment="Unique user identifier")
    user_role = Column(String(50), nullable=False, comment="Role of the user at query time")
    query = Column(Text, nullable=False, comment="Original user query")
    route_selected = Column(String(100), nullable=True, comment="Route classified by the router")
    confidence = Column(Float, nullable=True, comment="Router confidence score")
    is_authorized = Column(Boolean, nullable=False, default=False, comment="Whether the user was allowed access")
    message = Column(Text, nullable=True, comment="Response message or denial reason")

    def __repr__(self):
        return (
            f"<RoutingLog(id={self.id}, user_role='{self.user_role}', "
            f"route='{self.route_selected}', authorized={self.is_authorized})>"
        )
