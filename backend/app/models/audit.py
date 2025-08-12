# Модель аудита
from app.core.database import Base
class AuditLog(Base):
    __tablename__ = "audit_logs"
    pass
