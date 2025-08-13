from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text, ForeignKey
from datetime import datetime
from app.core.database import Base

class Goal(Base):
    __tablename__ = "goals"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(200), nullable=False)
    target_amount = Column(Numeric(precision=15, scale=2), nullable=False)
    current_amount = Column(Numeric(precision=15, scale=2), default=0)
    target_date = Column(DateTime)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
