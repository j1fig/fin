"""
Tests for Transaction repository.
"""

from fin.models import Account, AccountKind, Category, Transaction


# Transaction Repository Tests
def test_create_transaction(repository_factory):
    """Test creating a new transaction."""
    account_repo = repository_factory.account_repository()
    category_repo = repository_factory.category_repository()
    transaction_repository = repository_factory.transaction_repository()

    account = account_repo.create(Account(name="Test Bank", kind=AccountKind.BANK))
    category = category_repo.create(Category(name="Food"))
    
    transaction = Transaction(
        description="Grocery shopping",
        amount_cents=2500,
        account_id=account.id,
        category_id=category.id
    )
    
    created = transaction_repository.create(transaction)
    
    assert created.id is not None
    assert created.description == "Grocery shopping"
    assert created.amount_cents == 2500
    assert created.account_id == account.id
    assert created.category_id == category.id


def test_get_transactions_by_account_id(repository_factory):
    """Test getting transactions by account ID."""
    transaction_repository = repository_factory.transaction_repository()
    account_repo = repository_factory.account_repository()
    
    account1 = account_repo.create(Account(name="Bank 1", kind=AccountKind.BANK))
    account2 = account_repo.create(Account(name="Bank 2", kind=AccountKind.BANK))
    
    transaction1 = Transaction(description="T1", amount_cents=100, account_id=account1.id)
    transaction2 = Transaction(description="T2", amount_cents=200, account_id=account1.id)
    transaction3 = Transaction(description="T3", amount_cents=300, account_id=account2.id)
    
    transaction_repository.create(transaction1)
    transaction_repository.create(transaction2)
    transaction_repository.create(transaction3)
    
    account1_transactions = transaction_repository.get_by_account_id(account1.id)
    
    assert len(account1_transactions) == 2
    descriptions = [t.description for t in account1_transactions]
    assert "T1" in descriptions
    assert "T2" in descriptions
    assert "T3" not in descriptions


def test_get_transactions_by_category_id(repository_factory):
    """Test getting transactions by category ID."""
    transaction_repository = repository_factory.transaction_repository()
    category_repo = repository_factory.category_repository()
    
    category1 = category_repo.create(Category(name="Food"))
    category2 = category_repo.create(Category(name="Transport"))
    
    transaction1 = Transaction(description="T1", amount_cents=100, category_id=category1.id)
    transaction2 = Transaction(description="T2", amount_cents=200, category_id=category1.id)
    transaction3 = Transaction(description="T3", amount_cents=300, category_id=category2.id)
    
    transaction_repository.create(transaction1)
    transaction_repository.create(transaction2)
    transaction_repository.create(transaction3)
    
    food_transactions = transaction_repository.get_by_category_id(category1.id)
    
    assert len(food_transactions) == 2
    descriptions = [t.description for t in food_transactions]
    assert "T1" in descriptions
    assert "T2" in descriptions
    assert "T3" not in descriptions