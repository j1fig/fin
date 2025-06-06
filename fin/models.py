from datetime import datetime, timezone
import enum

from sqlmodel import DateTime, Field, SQLModel, Column, Enum


class AccountKind(enum.StrEnum):
    CASH =      "cash"
    CREDIT =    "credit"
    BANK =      "bank"


class Account(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key = True)
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False
        ),
        default_factory=lambda: datetime.now(timezone.utc)
    )

    name: str = Field(unique=True, index=True)
    kind: AccountKind = Field(
        sa_column=Column(
            Enum(AccountKind)
        )
    )


class Category(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key = True)
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False
        ),
        default_factory=lambda: datetime.now(timezone.utc)
    )

    name: str = Field(unique=True, index=True)


class RecurringRule(SQLModel, table=True):
    __tablename__ = "recurring_rule"

    id: int | None = Field(default=None, primary_key = True)
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False
        ),
        default_factory=lambda: datetime.now(timezone.utc)
    )

    name: str = Field(unique=True, index=True)
    description: str
    amount_cents: int  # amount (EUR cents) - SQLite doesn't support Decimal types and we don't want to lose precision.
    category_id: int | None = Field(default=None, foreign_key="account.id")
    account_id: int | None = Field(default=None, foreign_key="category.id")


class Transaction(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False
        ),
        default_factory=lambda: datetime.now(timezone.utc)
    )

    description: str
    amount_cents: int  # amount (EUR cents) - SQLite doesn't support Decimal types and we don't want to lose precision.
    category_id: int | None = Field(default=None, foreign_key="category.id")
    account_id: int | None = Field(default=None, foreign_key="account.id")
    recurring_rule_id: int | None = Field(default=None, foreign_key="recurring_rule.id")
    import_id: int | None = Field(default=None, foreign_key="import.id")


class Import(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False
        ),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    file_name: str
    sha256: str = Field(unique=True)