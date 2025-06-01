import csv

from fin import cgd, db, repository as repo
from fin.models import Account, AccountKind


def import_cgd_transactions(file_path: str):
    with db.get_session() as session:
        account = repo.create_account(session, Account(name="CGD", kind=AccountKind.BANK))

        with open(file_path, 'r', encoding='latin-1') as file:
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