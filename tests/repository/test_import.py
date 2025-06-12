"""
Tests for Import repository.
"""

import pytest

from fin.models import Import


@pytest.fixture
def import_repository(repository_factory):
    """Fixture for import repository."""
    return repository_factory.import_repository()


# Import Repository Tests
def test_create_import(import_repository):
    """Test creating a new import."""
    import_ = Import(file_name="test.pdf", sha256="abc123")
    
    created = import_repository.create(import_)
    
    assert created.id is not None
    assert created.file_name == "test.pdf"
    assert created.sha256 == "abc123"
    assert created.created_at is not None


def test_create_duplicate_import_raises_error(import_repository):
    """Test that creating duplicate import raises ValueError."""
    import1 = Import(file_name="test1.pdf", sha256="abc123")
    import2 = Import(file_name="test2.pdf", sha256="abc123")
    
    import_repository.create(import1)
    
    with pytest.raises(ValueError, match="Import test2.pdf with sha256 abc123 already exists"):
        import_repository.create(import2)


def test_get_import_by_sha256(import_repository):
    """Test getting import by SHA256."""
    import_ = Import(file_name="test.pdf", sha256="abc123")
    created = import_repository.create(import_)
    
    found = import_repository.get_by_sha256("abc123")
    
    assert found is not None
    assert found.id == created.id
    assert found.file_name == "test.pdf" 