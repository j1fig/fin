from sqlmodel import SQLModel, select

from fin.models import Account, Category, Transaction, Import
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


def create_import(session: Session, import_: Import):
    # if import already exists, fail here - this prevents duplicate imports for now.
    statement = select(Import).where(Import.sha256 == import_.sha256)
    result = session.exec(statement)
    existing_import = result.first()
    if existing_import:
        raise ValueError(f"Import {import_.file_name} with sha256 {import_.sha256} already exists")
    session.add(import_)
    session.commit()
    session.refresh(import_)
    return import_


def create_category(session: Session, category: Category):
    return _create_if_not_exists(session, category, category.name)


def update_category(session: Session, category_id: int, new_name: str):
    statement = select(Category).where(Category.id == category_id)
    result = session.exec(statement)
    category = result.first()
    if not category:
        raise ValueError(f"Category with id {category_id} not found")
    category.name = new_name
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def delete_category(session: Session, category_id: int):
    statement = select(Category).where(Category.id == category_id)
    result = session.exec(statement)
    category = result.first()
    if not category:
        raise ValueError(f"Category with id {category_id} not found")
    session.delete(category)
    session.commit()
    return True


def get_all_categories(session: Session):
    statement = select(Category)
    result = session.exec(statement)
    return result.all()


def create_account(session: Session, account: Account):
    return _create_if_not_exists(session, account, account.name)


def get_all_accounts(session: Session):
    statement = select(Account)
    result = session.exec(statement)
    return result.all()


def create_transaction(session: Session, transaction: Transaction):
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    return transaction