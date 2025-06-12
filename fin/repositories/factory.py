"""
Repository factory for creating repository instances.
"""

from sqlmodel import Session

from .account import AccountRepository
from .category import CategoryRepository
from .transaction import TransactionRepository
from .import_ import ImportRepository


class RepositoryFactory:
    """Factory for creating repository instances."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def account_repository(self) -> AccountRepository:
        """Create an Account repository instance."""
        return AccountRepository(self.session)
    
    def category_repository(self) -> CategoryRepository:
        """Create a Category repository instance."""
        return CategoryRepository(self.session)
    
    def transaction_repository(self) -> TransactionRepository:
        """Create a Transaction repository instance."""
        return TransactionRepository(self.session)
    
    def import_repository(self) -> ImportRepository:
        """Create an Import repository instance."""
        return ImportRepository(self.session) 