import csv
import hashlib
from typing import BinaryIO

from fin import cgd, db, moey, repository as repo
from fin.models import Account, AccountKind, Category, Import, Transaction


def import_cgd_transactions(uploaded_file: BinaryIO):
    with db.get_session() as session:
        account = repo.create_account(session, Account(name="CGD", kind=AccountKind.BANK))
        file_name = uploaded_file.name
        
        # Read file content as bytes for hashing
        file_content = uploaded_file.read()
        file_sha256 = hashlib.sha256(file_content).hexdigest()
        import_ = repo.create_import(session, Import(file_name=file_name, sha256=file_sha256))

        # Decode bytes to text for CSV processing
        file_text = file_content.decode('latin1')
        lines = file_text.split('\n')
        
        # Skip the first 6 lines
        content_lines = lines[6:]
        
        # Create CSV reader from the remaining lines
        reader = csv.DictReader(content_lines, delimiter='\t', strict=True)
        
        # Process transactions (skip last 2 footer lines by breaking on ValueError)
        transaction_count = 0
        for row in reader:
            try:
                transaction = cgd.parse_transaction(row)
                category = cgd.parse_category(row)
                category = repo.create_category(session, category)
                transaction.account_id = account.id
                transaction.category_id = category.id
                transaction.import_id = import_.id
                repo.create_transaction(session, transaction)
                transaction_count += 1
            except ValueError:
                break
        
        if transaction_count == 0:
            raise ValueError("No transactions were found in the file. Please check the file format.")


def import_moey_transactions(uploaded_file: BinaryIO):
    with db.get_session() as session:
        account = repo.create_account(session, Account(name="Moey", kind=AccountKind.BANK))
        file_name = uploaded_file.name
        
        # Read file content as bytes for hashing
        file_content = uploaded_file.read()
        file_sha256 = hashlib.sha256(file_content).hexdigest()
        import_ = repo.create_import(session, Import(file_name=file_name, sha256=file_sha256))

        # For PDF files, we need to pass the file-like object to pdfplumber
        # Reset to beginning and pass the uploaded file directly
        uploaded_file.seek(0)
        transactions = moey.parse_pdf(uploaded_file)
        for transaction in transactions:
            transaction.account_id = account.id
            transaction.import_id = import_.id
            repo.create_transaction(session, transaction)


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


def get_all_accounts():
    """Get all accounts formatted for UI (name -> id mapping)."""
    with db.get_session() as session:
        accounts = repo.get_all_accounts(session)
        return {acc.name: acc.id for acc in accounts}


def create_manual_transaction(date, description: str, amount: float, account_id: int, category_id: int | None = None) -> Transaction:
    """Create a manual transaction."""
    try:
        description = description.strip()
        if not description:
            raise ValueError("Description cannot be empty")
        
        # Convert amount from euros to cents
        amount_cents = int(amount * 100)
        
        with db.get_session() as session:
            transaction = Transaction(
                created_at=date,
                description=description,
                amount_cents=amount_cents,
                account_id=account_id,
                category_id=category_id
            )
            return repo.create_transaction(session, transaction)
    except Exception as e:
        raise ValueError(f"Failed to create transaction: {str(e)}")