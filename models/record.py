from models.db import db
from datetime import datetime


class FinancialRecord(db.Model):
    __tablename__ = "financial_records"

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(20), nullable=False)       # income or expense
    category = db.Column(db.String(50), nullable=False)   # e.g. salary, rent, food
    date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.String(300), nullable=True)
    is_deleted = db.Column(db.Boolean, default=False)     # soft delete
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "amount": self.amount,
            "type": self.type,
            "category": self.category,
            "date": self.date.isoformat(),
            "notes": self.notes,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat()
        }
