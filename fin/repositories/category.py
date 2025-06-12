"""
Category repository implementation.
"""

from typing import List, Optional
from sqlmodel import Session, select

from fin.models import Category


class CategoryRepository:
    """SQLModel implementation of Category repository."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, category: Category) -> Category:
        """Create a new category or return existing one with the same name."""
        existing = self.get_by_name(category.name)
        if existing:
            return existing
        
        self.session.add(category)
        self.session.commit()
        self.session.refresh(category)
        return category
    
    def get_by_id(self, category_id: int) -> Optional[Category]:
        """Get category by ID."""
        statement = select(Category).where(Category.id == category_id)
        result = self.session.exec(statement)
        return result.first()
    
    def get_by_name(self, name: str) -> Optional[Category]:
        """Get category by name."""
        statement = select(Category).where(Category.name == name)
        result = self.session.exec(statement)
        return result.first()
    
    def get_all(self) -> List[Category]:
        """Get all categories."""
        statement = select(Category)
        result = self.session.exec(statement)
        return result.all()
    
    def update(self, category_id: int, new_name: str) -> Category:
        """Update a category's name."""
        category = self.get_by_id(category_id)
        if not category:
            raise ValueError(f"Category with id {category_id} not found")
        
        category.name = new_name
        self.session.add(category)
        self.session.commit()
        self.session.refresh(category)
        return category
    
    def delete(self, category_id: int) -> bool:
        """Delete a category by ID."""
        category = self.get_by_id(category_id)
        if not category:
            return False
        
        self.session.delete(category)
        self.session.commit()
        return True