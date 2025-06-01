from datetime import datetime

from fin.models import Category, Transaction


FIELDNAMES = [
    'Data mov. ',
    'Data valor ',
    'Descrição ',
    'Débito ',
    'Crédito ',
    'Saldo contabilístico ',
    'Saldo disponível ',
    'Categoria '
]


def parse_category(row: dict) -> Category:
    return Category(name=row['Categoria '])


def parse_transaction(row: dict) -> Transaction:
    credit = _parse_amount_cents(row['Crédito '])
    debit = _parse_amount_cents(row['Débito '])
    if credit and debit:
        raise ValueError(f"Both credit and debit are present for row: {row}")
    amount_cents = credit or -debit
    created_at = datetime.strptime(row['Data mov. '], '%d-%m-%Y')
    return Transaction(
        created_at=created_at,
        description=row['Descrição '],
        amount_cents=amount_cents
    )


def _parse_amount_cents(amount_field: str) -> int | None:
    if amount_field == '':
        return None
    # after stripping the thousand and decimal separators, we get the amount in cents.
    return int(amount_field.replace('.', '').replace(',', ''))