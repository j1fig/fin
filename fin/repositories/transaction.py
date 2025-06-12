"""
Transaction repository implementation.
"""

from typing import List, Optional
from sqlmodel import Session, select

from fin.models import Transaction


class TransactionRepository:
    """SQLModel implementation of Transaction repository."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, transaction: Transaction) -> Transaction:
        """Create a new transaction."""
        self.session.add(transaction)
        self.session.commit()
        self.session.refresh(transaction)
        return transaction
    
    def get_by_id(self, transaction_id: int) -> Optional[Transaction]:
        """Get transaction by ID."""
        statement = select(Transaction).where(Transaction.id == transaction_id)
        result = self.session.exec(statement)
        return result.first()
    
    def get_by_account_id(self, account_id: int) -> List[Transaction]:
        """Get all transactions for a specific account."""
        statement = select(Transaction).where(Transaction.account_id == account_id)
        result = self.session.exec(statement)
        return result.all()
    
    def get_by_category_id(self, category_id: int) -> List[Transaction]:
        """Get all transactions for a specific category."""
        statement = select(Transaction).where(Transaction.category_id == category_id)
        result = self.session.exec(statement)
        return result.all()
    
    def get_by_import_id(self, import_id: int) -> List[Transaction]:
        """Get all transactions for a specific import."""
        statement = select(Transaction).where(Transaction.import_id == import_id)
        result = self.session.exec(statement)
        return result.all()
    
    def get_all(self) -> List[Transaction]:
        """Get all transactions."""
        statement = select(Transaction)
        result = self.session.exec(statement)
        return result.all()
    
    def update(self, transaction: Transaction) -> Transaction:
        """Update an existing transaction."""
        self.session.add(transaction)
        self.session.commit()
        self.session.refresh(transaction)
        return transaction
    
    def delete(self, transaction_id: int) -> bool:
        """Delete a transaction by ID."""
        transaction = self.get_by_id(transaction_id)
        if not transaction:
            return False
        
        self.session.delete(transaction)
        self.session.commit()
        return True