"""
Tests for Account repository.
"""

from fin.models import Account, AccountKind


# Account Repository Tests
def test_create_account(repository_factory):
    """Test creating a new account."""
    repo = repository_factory.account_repository()
    account = Account(name="Test Bank", kind=AccountKind.BANK)
    
    created_account = repo.create(account)
    
    assert created_account.id is not None
    assert created_account.name == "Test Bank"
    assert created_account.kind == AccountKind.BANK
    assert created_account.created_at is not None


def test_create_duplicate_account_returns_existing(repository_factory):
    """Test that creating a duplicate account returns the existing one."""
    repo = repository_factory.account_repository()
    account1 = Account(name="Test Bank", kind=AccountKind.BANK)
    account2 = Account(name="Test Bank", kind=AccountKind.CREDIT)
    
    created1 = repo.create(account1)
    created2 = repo.create(account2)
    
    assert created1 == created2


def test_get_account_by_id(repository_factory):
    """Test getting account by ID."""
    repo = repository_factory.account_repository()
    account = Account(name="Test Bank", kind=AccountKind.BANK)
    created = repo.create(account)
    
    found = repo.get_by_id(created.id)
    
    assert found is not None
    assert found.id == created.id
    assert found.name == "Test Bank"


def test_get_account_by_id_not_found(repository_factory):
    """Test getting account by non-existent ID."""
    repo = repository_factory.account_repository()
    
    found = repo.get_by_id(999)
    
    assert found is None


def test_get_account_by_name(repository_factory):
    """Test getting account by name."""
    repo = repository_factory.account_repository()
    account = Account(name="Test Bank", kind=AccountKind.BANK)
    created = repo.create(account)
    
    found = repo.get_by_name("Test Bank")
    
    assert found is not None
    assert found.id == created.id
    assert found.name == "Test Bank"


def test_get_account_by_name_not_found(repository_factory):
    """Test getting account by non-existent name."""
    repo = repository_factory.account_repository()
    
    found = repo.get_by_name("Non-existent Bank")
    
    assert found is None


def test_get_all_accounts(repository_factory):
    """Test getting all accounts."""
    repo = repository_factory.account_repository()
    account1 = Account(name="Bank 1", kind=AccountKind.BANK)
    account2 = Account(name="Bank 2", kind=AccountKind.CREDIT)
    
    repo.create(account1)
    repo.create(account2)
    
    all_accounts = repo.get_all()
    
    assert len(all_accounts) == 2
    names = [acc.name for acc in all_accounts]
    assert "Bank 1" in names
    assert "Bank 2" in names


def test_update_account(repository_factory):
    """Test updating an account."""
    repo = repository_factory.account_repository()
    account = Account(name="Test Bank", kind=AccountKind.BANK)
    created = repo.create(account)
    
    created.name = "Updated Bank"
    repo.update(created)
    
    updated = repo.get_by_name("Updated Bank")
    assert updated.name == "Updated Bank"
    assert updated.id == created.id


def test_delete_account(repository_factory):
    """Test deleting an account."""
    repo = repository_factory.account_repository()
    account = Account(name="Test Bank", kind=AccountKind.BANK)
    created = repo.create(account)
    
    repo.delete(created.id)
    
    assert repo.get_by_id(created.id) is None


def test_delete_account_not_found(repository_factory):
    """Test deleting a non-existent account."""
    repo = repository_factory.account_repository()
    
    repo.delete(999)
    
    assert repo.get_by_id(999) is None