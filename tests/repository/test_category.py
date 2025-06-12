"""
Tests for Category repository.
"""

import pytest

from fin.models import Category

@pytest.fixture
def category_repository(repository_factory):
    """Fixture for category repository."""
    return repository_factory.category_repository()

# Category Repository Tests
def test_create_category(category_repository):
    """Test creating a new category."""
    category = Category(name="Food")
    
    created_category = category_repository.create(category)
    
    assert created_category.id is not None
    assert created_category.name == "Food"
    assert created_category.created_at is not None


def test_create_duplicate_category_returns_existing(category_repository):
    """Test that creating a duplicate category returns the existing one."""
    category1 = Category(name="Food")
    category2 = Category(name="Food")
    
    created1 = category_repository.create(category1)
    created2 = category_repository.create(category2)
    
    assert created1 == created2


def test_update_category(category_repository):
    """Test updating a category's name."""
    category = Category(name="Food")
    created = category_repository.create(category)
    
    category_repository.update(created.id, "Groceries")
    
    updated = category_repository.get_by_name("Groceries")
    assert updated.name == "Groceries"
    assert updated.id == created.id


def test_update_category_not_found(category_repository):
    """Test updating a non-existent category."""
    
    with pytest.raises(ValueError, match="Category with id 999 not found"):
        category_repository.update(999, "New Name")


def test_delete_category(category_repository):
    """Test deleting a category."""
    category = Category(name="Food")
    created = category_repository.create(category)
    
    category_repository.delete(created.id)
    
    assert category_repository.get_by_id(created.id) is None