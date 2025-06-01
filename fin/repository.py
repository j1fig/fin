from sqlmodel import SQLModel, select

from fin.models import Account, Category, Transaction
from fin.db import Session


def _create_if_not_exists(session: Session, instance: SQLModel, name: str):
    Model = type(instance)
    statement = select(Model).where(Model.name == name)
    result = session.exec(statement)
    existing_model = result.first()
    if existing_model:
        return existing_model
    session.add(instance)
    session.commit()
    session.refresh(instance)
    return instance


def create_category(session: Session, category: Category):
    return _create_if_not_exists(session, category, category.name)


def create_account(session: Session, account: Account):
    return _create_if_not_exists(session, account, account.name)


def create_transaction(session: Session, transaction: Transaction):
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    return transaction