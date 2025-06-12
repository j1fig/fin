"""
Account repository implementation.
"""

from typing import List, Optional
from sqlmodel import Session, select

from fin.models import Account


class AccountRepository:
    """SQLModel implementation of Account repository."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, account: Account) -> Account:
        """Create a new account or return existing one with the same name."""
        existing = self.get_by_name(account.name)
        if existing:
            return existing
        
        self.session.add(account)
        self.session.commit()
        self.session.refresh(account)
        return account
    
    def get_by_id(self, account_id: int) -> Optional[Account]:
        """Get account by ID."""
        statement = select(Account).where(Account.id == account_id)
        result = self.session.exec(statement)
        return result.first()
    
    def get_by_name(self, name: str) -> Optional[Account]:
        """Get account by name."""
        statement = select(Account).where(Account.name == name)
        result = self.session.exec(statement)
        return result.first()
    
    def get_all(self) -> List[Account]:
        """Get all accounts."""
        statement = select(Account)
        result = self.session.exec(statement)
        return result.all()
    
    def update(self, account: Account) -> Account:
        """Update an existing account."""
        self.session.add(account)
        self.session.commit()
        self.session.refresh(account)
        return account
    
    def delete(self, account_id: int) -> bool:
        """Delete an account by ID."""
        account = self.get_by_id(account_id)
        if not account:
            return False
        
        self.session.delete(account)
        self.session.commit()
        return True