import csv
import hashlib
from typing import BinaryIO, List, Optional, Dict, Any
from datetime import datetime, date

from fin import cgd, db, moey
from fin.repositories.factory import RepositoryFactory
from fin.models import Account, AccountKind, Category, Import, Transaction


def import_cgd_transactions(uploaded_file: BinaryIO):
    with db.get_session() as session:
        repos = RepositoryFactory(session)
        account_repo = repos.account_repository()
        category_repo = repos.category_repository()
        transaction_repo = repos.transaction_repository()
        import_repo = repos.import_repository()
        
        account = account_repo.create(Account(name="CGD", kind=AccountKind.BANK))
        file_name = uploaded_file.name
        
        # Read file content as bytes for hashing
        file_content = uploaded_file.read()
        file_sha256 = hashlib.sha256(file_content).hexdigest()
        import_ = import_repo.create(Import(file_name=file_name, sha256=file_sha256))

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
                category = category_repo.create(category)
                transaction.account_id = account.id
                transaction.category_id = category.id
                transaction.import_id = import_.id
                transaction_repo.create(transaction)
                transaction_count += 1
            except ValueError:
                break
        
        if transaction_count == 0:
            raise ValueError("No transactions were found in the file. Please check the file format.")


def import_moey_transactions(uploaded_file: BinaryIO):
    with db.get_session() as session:
        repos = RepositoryFactory(session)
        account_repo = repos.account_repository()
        transaction_repo = repos.transaction_repository()
        import_repo = repos.import_repository()
        
        account = account_repo.create(Account(name="Moey", kind=AccountKind.BANK))
        file_name = uploaded_file.name
        
        # Read file content as bytes for hashing
        file_content = uploaded_file.read()
        file_sha256 = hashlib.sha256(file_content).hexdigest()
        import_ = import_repo.create(Import(file_name=file_name, sha256=file_sha256))

        # For PDF files, we need to pass the file-like object to pdfplumber
        # Reset to beginning and pass the uploaded file directly
        uploaded_file.seek(0)
        transactions = moey.parse_pdf(uploaded_file)
        for transaction in transactions:
            transaction.account_id = account.id
            transaction.import_id = import_.id
            transaction_repo.create(transaction)


# Category Management Services
def create_new_category(name: str) -> bool:
    """Create a new category with the given name."""
    try:
        name = name.strip()
        if not name:
            raise ValueError("Category name cannot be empty")
        
        with db.get_session() as session:
            repos = RepositoryFactory(session)
            category_repo = repos.category_repository()
            category = Category(name=name)
            category_repo.create(category)
        return True
    except Exception as e:
        raise ValueError(f"Failed to create category: {str(e)}")


def get_categories_for_management():
    """Get all categories formatted for UI management (name -> id mapping)."""
    with db.get_session() as session:
        repos = RepositoryFactory(session)
        category_repo = repos.category_repository()
        categories = category_repo.get_all()
        return {cat.name: cat.id for cat in categories}


def get_category_names_list():
    """Get all category names as a simple list."""
    with db.get_session() as session:
        repos = RepositoryFactory(session)
        category_repo = repos.category_repository()
        categories = category_repo.get_all()
        return [cat.name for cat in categories]


def update_existing_category(category_name: str, new_name: str) -> bool:
    """Update a category's name."""
    try:
        new_name = new_name.strip()
        if not new_name:
            raise ValueError("New category name cannot be empty")
        
        with db.get_session() as session:
            repos = RepositoryFactory(session)
            category_repo = repos.category_repository()
            
            category = category_repo.get_by_name(category_name)
            if not category:
                raise ValueError(f"Category '{category_name}' not found")
            
            category_repo.update(category.id, new_name)
        return True
    except Exception as e:
        raise ValueError(f"Failed to update category: {str(e)}")


def delete_existing_category(category_name: str) -> bool:
    """Delete a category by name."""
    try:
        with db.get_session() as session:
            repos = RepositoryFactory(session)
            category_repo = repos.category_repository()
            
            category = category_repo.get_by_name(category_name)
            if not category:
                raise ValueError(f"Category '{category_name}' not found")
            
            category_repo.delete(category.id)
        return True
    except Exception as e:
        raise ValueError(f"Failed to delete category: {str(e)}")


def get_all_accounts():
    """Get all accounts formatted for UI (name -> id mapping)."""
    with db.get_session() as session:
        repos = RepositoryFactory(session)
        account_repo = repos.account_repository()
        accounts = account_repo.get_all()
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
            repos = RepositoryFactory(session)
            transaction_repo = repos.transaction_repository()
            
            transaction = Transaction(
                created_at=date,
                description=description,
                amount_cents=amount_cents,
                account_id=account_id,
                category_id=category_id
            )
            return transaction_repo.create(transaction)
    except Exception as e:
        raise ValueError(f"Failed to create transaction: {str(e)}")


# Analytics Services
def get_category_spending_data(start_date: date, end_date: date) -> List[Dict[str, Any]]:
    """Get category spending data for analytics."""
    with db.get_session() as session:
        repos = RepositoryFactory(session)
        transaction_repo = repos.transaction_repository()
        category_repo = repos.category_repository()
        
        # Get all transactions in date range
        all_transactions = transaction_repo.get_all()
        
        # Filter by date range
        filtered_transactions = []
        for t in all_transactions:
            # Convert datetime to date for comparison
            t_date = t.created_at.date() if isinstance(t.created_at, datetime) else t.created_at
            if start_date <= t_date <= end_date:
                filtered_transactions.append(t)
        
        # Group by category
        category_data = {}
        for transaction in filtered_transactions:
            if transaction.category_id:
                category = category_repo.get_by_id(transaction.category_id)
                category_name = category.name if category else "Unknown"
            else:
                category_name = "Uncategorized"
            
            if category_name not in category_data:
                category_data[category_name] = {
                    'category': category_name,
                    'expenses': 0.0,
                    'income': 0.0,
                    'transaction_count': 0
                }
            
            amount_euros = transaction.amount_cents / 100.0
            if transaction.amount_cents < 0:
                category_data[category_name]['expenses'] += abs(amount_euros)
            else:
                category_data[category_name]['income'] += amount_euros
            
            category_data[category_name]['transaction_count'] += 1
        
        return list(category_data.values())


def get_monthly_spending_trends(start_date: date, end_date: date) -> List[Dict[str, Any]]:
    """Get monthly spending trends by category."""
    with db.get_session() as session:
        repos = RepositoryFactory(session)
        transaction_repo = repos.transaction_repository()
        category_repo = repos.category_repository()
        
        # Get all transactions in date range (expenses only)
        all_transactions = transaction_repo.get_all()
        
        # Filter by date range and expenses only
        expense_transactions = []
        for t in all_transactions:
            t_date = t.created_at.date() if isinstance(t.created_at, datetime) else t.created_at
            if start_date <= t_date <= end_date and t.amount_cents < 0:
                expense_transactions.append(t)
        
        # Group by month and category
        monthly_data = {}
        for transaction in expense_transactions:
            month_key = transaction.created_at.strftime('%Y-%m')
            
            if transaction.category_id:
                category = category_repo.get_by_id(transaction.category_id)
                category_name = category.name if category else "Unknown"
            else:
                category_name = "Uncategorized"
            
            key = (month_key, category_name)
            if key not in monthly_data:
                monthly_data[key] = {
                    'month': month_key,
                    'category': category_name,
                    'expenses': 0.0
                }
            
            monthly_data[key]['expenses'] += abs(transaction.amount_cents / 100.0)
        
        return list(monthly_data.values())


# Transaction Query Services
def get_uncategorized_transactions() -> List[Dict[str, Any]]:
    """Get all uncategorized transactions for UI display."""
    with db.get_session() as session:
        repos = RepositoryFactory(session)
        transaction_repo = repos.transaction_repository()
        account_repo = repos.account_repository()
        
        all_transactions = transaction_repo.get_all()
        uncategorized = []
        
        for t in all_transactions:
            if not t.category_id:
                account = account_repo.get_by_id(t.account_id) if t.account_id else None
                uncategorized.append({
                    'id': t.id,
                    'description': t.description,
                    'amount': t.amount_cents / 100.0,
                    'date': t.created_at.strftime('%Y-%m-%d'),
                    'account': account.name if account else 'Unknown',
                    'current_category': None
                })
        
        return uncategorized


def get_all_transactions_for_ui(category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get all transactions formatted for UI display."""
    with db.get_session() as session:
        repos = RepositoryFactory(session)
        transaction_repo = repos.transaction_repository()
        account_repo = repos.account_repository()
        category_repo = repos.category_repository()
        
        all_transactions = transaction_repo.get_all()
        formatted_transactions = []
        
        for t in all_transactions:
            account = account_repo.get_by_id(t.account_id) if t.account_id else None
            category = category_repo.get_by_id(t.category_id) if t.category_id else None
            category_name = category.name if category else None
            
            # Apply category filter if specified
            if category_filter and category_filter != "All Categories":
                if category_name != category_filter:
                    continue
            
            formatted_transactions.append({
                'id': t.id,
                'description': t.description,
                'amount': t.amount_cents / 100.0,
                'date': t.created_at.strftime('%Y-%m-%d'),
                'account': account.name if account else 'Unknown',
                'current_category': category_name
            })
        
        return formatted_transactions


def get_merchant_groups(uncategorized_only: bool = True) -> List[Dict[str, Any]]:
    """Get transaction groups by merchant/description patterns."""
    with db.get_session() as session:
        repos = RepositoryFactory(session)
        transaction_repo = repos.transaction_repository()
        category_repo = repos.category_repository()
        
        all_transactions = transaction_repo.get_all()
        
        # Filter transactions
        if uncategorized_only:
            transactions = [t for t in all_transactions if not t.category_id]
        else:
            transactions = all_transactions
        
        # Group by merchant (simplified - just use first 20 chars of description)
        merchant_groups = {}
        for t in transactions:
            merchant_key = t.description[:20].strip()
            
            if merchant_key not in merchant_groups:
                category = category_repo.get_by_id(t.category_id) if t.category_id else None
                merchant_groups[merchant_key] = {
                    'merchant': merchant_key,
                    'transaction_count': 0,
                    'total_amount': 0.0,
                    'current_category': category.name if category else None
                }
            
            merchant_groups[merchant_key]['transaction_count'] += 1
            merchant_groups[merchant_key]['total_amount'] += abs(t.amount_cents / 100.0)
        
        return list(merchant_groups.values())


def get_sample_transactions_for_merchant(merchant: str) -> List[Dict[str, Any]]:
    """Get sample transactions for a specific merchant."""
    with db.get_session() as session:
        repos = RepositoryFactory(session)
        transaction_repo = repos.transaction_repository()
        
        all_transactions = transaction_repo.get_all()
        samples = []
        
        for t in all_transactions:
            if t.description.startswith(merchant):
                samples.append({
                    'date': t.created_at.strftime('%Y-%m-%d'),
                    'amount': t.amount_cents / 100.0,
                    'description': t.description
                })
                if len(samples) >= 5:  # Limit to 5 samples
                    break
        
        return samples


def update_transactions_category(transaction_ids: List[int], category_name: str) -> bool:
    """Update multiple transactions to a specific category."""
    try:
        with db.get_session() as session:
            repos = RepositoryFactory(session)
            transaction_repo = repos.transaction_repository()
            category_repo = repos.category_repository()
            
            # Get the category
            category = category_repo.get_by_name(category_name)
            if not category:
                raise ValueError(f"Category '{category_name}' not found")
            
            # Update each transaction
            for transaction_id in transaction_ids:
                transaction = transaction_repo.get_by_id(transaction_id)
                if transaction:
                    transaction.category_id = category.id
                    transaction_repo.update(transaction)
            
            return True
    except Exception as e:
        raise ValueError(f"Failed to update transactions: {str(e)}")


def update_merchant_transactions(merchant: str, category_name: str) -> bool:
    """Update all transactions from a specific merchant to a category."""
    try:
        with db.get_session() as session:
            repos = RepositoryFactory(session)
            transaction_repo = repos.transaction_repository()
            category_repo = repos.category_repository()
            
            # Get the category
            category = category_repo.get_by_name(category_name)
            if not category:
                raise ValueError(f"Category '{category_name}' not found")
            
            # Find and update all matching transactions
            all_transactions = transaction_repo.get_all()
            updated_count = 0
            
            for transaction in all_transactions:
                if transaction.description.startswith(merchant):
                    transaction.category_id = category.id
                    transaction_repo.update(transaction)
                    updated_count += 1
            
            return updated_count > 0
    except Exception as e:
        raise ValueError(f"Failed to update merchant transactions: {str(e)}")


def get_common_uncategorized_patterns() -> List[Dict[str, Any]]:
    """Get common patterns in uncategorized transaction descriptions."""
    with db.get_session() as session:
        repos = RepositoryFactory(session)
        transaction_repo = repos.transaction_repository()
        
        # Get all uncategorized transactions
        all_transactions = transaction_repo.get_all()
        uncategorized = [t for t in all_transactions if not t.category_id]
        
        # Simple pattern matching logic
        pattern_counts = {}
        for transaction in uncategorized:
            description = transaction.description.upper()
            
            # Check for common merchant patterns
            if 'AMAZON' in description:
                pattern = 'AMAZON'
            elif 'STARBUCKS' in description:
                pattern = 'STARBUCKS'
            elif 'UBER' in description:
                pattern = 'UBER'
            elif any(word in description for word in ['GROCERY', 'MARKET', 'SUPERMARKET']):
                pattern = 'GROCERY/MARKET'
            elif any(word in description for word in ['RESTAURANT', 'CAFE', 'PIZZA']):
                pattern = 'RESTAURANTS'
            elif any(word in description for word in ['GAS', 'FUEL', 'PETROL']):
                pattern = 'GAS/FUEL'
            elif 'ATM' in description:
                pattern = 'ATM'
            elif any(word in description for word in ['PHARMACY', 'DRUGSTORE']):
                pattern = 'PHARMACY'
            else:
                # Use first 10 characters as pattern
                pattern = description[:10].strip()
            
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        # Filter patterns with at least 2 occurrences and sort by count
        result = []
        for pattern, count in pattern_counts.items():
            if count >= 2:
                result.append({
                    'pattern': pattern,
                    'count': count
                })
        
        # Sort by count descending and limit to 8
        result.sort(key=lambda x: x['count'], reverse=True)
        return result[:8]


def count_pattern_matches(pattern: str, case_sensitive: bool = False, apply_to_all: bool = False) -> int:
    """Count how many transactions match a pattern."""
    with db.get_session() as session:
        repos = RepositoryFactory(session)
        transaction_repo = repos.transaction_repository()
        
        all_transactions = transaction_repo.get_all()
        
        # Filter to uncategorized if needed
        if not apply_to_all:
            transactions = [t for t in all_transactions if not t.category_id]
        else:
            transactions = all_transactions
        
        # Count matches
        count = 0
        for transaction in transactions:
            description = transaction.description
            search_pattern = pattern
            
            if not case_sensitive:
                description = description.lower()
                search_pattern = search_pattern.lower()
            
            if search_pattern in description:
                count += 1
        
        return count


def apply_pattern_rule(pattern: str, category_name: str, case_sensitive: bool = False, apply_to_all: bool = False) -> int:
    """Apply a pattern rule to categorize matching transactions."""
    try:
        with db.get_session() as session:
            repos = RepositoryFactory(session)
            transaction_repo = repos.transaction_repository()
            category_repo = repos.category_repository()
            
            # Get the category
            category = category_repo.get_by_name(category_name)
            if not category:
                raise ValueError(f"Category '{category_name}' not found")
            
            all_transactions = transaction_repo.get_all()
            
            # Filter to uncategorized if needed
            if not apply_to_all:
                transactions = [t for t in all_transactions if not t.category_id]
            else:
                transactions = all_transactions
            
            # Apply pattern matching and update
            updated_count = 0
            search_pattern = pattern
            
            for transaction in transactions:
                description = transaction.description
                compare_description = description
                compare_pattern = search_pattern
                
                if not case_sensitive:
                    compare_description = description.lower()
                    compare_pattern = search_pattern.lower()
                
                if compare_pattern in compare_description:
                    transaction.category_id = category.id
                    transaction_repo.update(transaction)
                    updated_count += 1
            
            return updated_count
    except Exception as e:
        raise ValueError(f"Failed to apply pattern rule: {str(e)}")