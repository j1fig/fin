import csv
from typing import TextIO

from fin import cgd, db, repository as repo
from fin.models import Account, AccountKind, Category


def import_cgd_transactions(uploaded_file: TextIO):
    with db.get_session() as session:
        account = repo.create_account(session, Account(name="CGD", kind=AccountKind.BANK))

        with uploaded_file as file:
            # Skip the first 6 lines
            for _ in range(6):
                file.readline()
            # This still reads the header line.
            # reader = csv.DictReader(file, fieldnames=cgd.FIELDNAMES, delimiter='\t', strict=True)
            reader = csv.DictReader(file, delimiter='\t', strict=True)
            # Skip the last 2 footer lines
            for row in reader:
                try:
                    transaction = cgd.parse_transaction(row)
                    category = cgd.parse_category(row)
                    category = repo.create_category(session, category)
                    transaction.account_id = account.id
                    transaction.category_id = category.id
                    repo.create_transaction(session, transaction)
                except ValueError:
                    break


# Category Management Services
def create_new_category(name: str) -> bool:
    """Create a new category with the given name."""
    try:
        name = name.strip()
        if not name:
            raise ValueError("Category name cannot be empty")
        
        with db.get_session() as session:
            category = Category(name=name)
            repo.create_category(session, category)
        return True
    except Exception as e:
        raise ValueError(f"Failed to create category: {str(e)}")


def get_categories_for_management():
    """Get all categories formatted for UI management (name -> id mapping)."""
    with db.get_session() as session:
        categories = repo.get_all_categories(session)
        return {cat.name: cat.id for cat in categories}


def get_category_names_list():
    """Get all category names as a simple list."""
    with db.get_session() as session:
        categories = repo.get_all_categories(session)
        return [cat.name for cat in categories]


def update_existing_category(category_name: str, new_name: str) -> bool:
    """Update a category's name."""
    try:
        new_name = new_name.strip()
        if not new_name:
            raise ValueError("New category name cannot be empty")
        
        with db.get_session() as session:
            categories = repo.get_all_categories(session)
            category_id = None
            for cat in categories:
                if cat.name == category_name:
                    category_id = cat.id
                    break
            
            if category_id is None:
                raise ValueError(f"Category '{category_name}' not found")
            
            repo.update_category(session, category_id, new_name)
        return True
    except Exception as e:
        raise ValueError(f"Failed to update category: {str(e)}")


def delete_existing_category(category_name: str) -> bool:
    """Delete a category by name."""
    try:
        with db.get_session() as session:
            categories = repo.get_all_categories(session)
            category_id = None
            for cat in categories:
                if cat.name == category_name:
                    category_id = cat.id
                    break
            
            if category_id is None:
                raise ValueError(f"Category '{category_name}' not found")
            
            repo.delete_category(session, category_id)
        return True
    except Exception as e:
        raise ValueError(f"Failed to delete category: {str(e)}")