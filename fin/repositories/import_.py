"""
Import repository implementation.
"""

from typing import List, Optional
from sqlmodel import Session, select

from fin.models import Import


class ImportRepository:
    """SQLModel implementation of Import repository."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, import_: Import) -> Import:
        """Create a new import. Raises ValueError if SHA256 already exists."""
        existing = self.get_by_sha256(import_.sha256)
        if existing:
            raise ValueError(f"Import {import_.file_name} with sha256 {import_.sha256} already exists")
        
        self.session.add(import_)
        self.session.commit()
        self.session.refresh(import_)
        return import_
    
    def get_by_id(self, import_id: int) -> Optional[Import]:
        """Get import by ID."""
        statement = select(Import).where(Import.id == import_id)
        result = self.session.exec(statement)
        return result.first()
    
    def get_by_sha256(self, sha256: str) -> Optional[Import]:
        """Get import by SHA256 hash."""
        statement = select(Import).where(Import.sha256 == sha256)
        result = self.session.exec(statement)
        return result.first()
    
    def get_all(self) -> List[Import]:
        """Get all imports."""
        statement = select(Import)
        result = self.session.exec(statement)
        return result.all()
    
    def delete(self, import_id: int) -> bool:
        """Delete an import by ID."""
        import_ = self.get_by_id(import_id)
        if not import_:
            return False
        
        self.session.delete(import_)
        self.session.commit()
        return True 