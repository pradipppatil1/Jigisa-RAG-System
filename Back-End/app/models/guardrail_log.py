"""
SQLAlchemy model for the guardrail_logs table.

Every guardrail trigger (blocked, warning, or allowed) is persisted
here for auditability and analytics.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func

from app.core.database import Base


class GuardrailLog(Base):
    __tablename__ = "guardrail_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user_id = Column(String(100), nullable=True, comment="Unique user identifier")
    user_role = Column(String(50), nullable=True, comment="Role of the user at check time")
    query = Column(Text, nullable=True, comment="Original user query (scrubbed if PII)")
    guardrail_name = Column(String(100), nullable=False, comment="Name of the guardrail triggered")
    guardrail_type = Column(String(20), nullable=False, comment="input or output")
    status = Column(String(20), nullable=False, comment="blocked, allowed, or warning")
    reason = Column(Text, nullable=True, comment="Detailed reason for the guardrail result")

    def __repr__(self):
        return (
            f"<GuardrailLog(id={self.id}, guardrail='{self.guardrail_name}', "
            f"type='{self.guardrail_type}', status='{self.status}')>"
        )
