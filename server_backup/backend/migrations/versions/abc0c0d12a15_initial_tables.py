"""Initial tables

Revision ID: abc0c0d12a15
Revises: 
Create Date: 2025-08-11 23:21:44.412555+03:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'abc0c0d12a15'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    
    # Создаем типы enum
    account_type_enum = sa.Enum(
        'broker', 'ira', 'pension', 'savings', 'checking', 'crypto_exchange', 'other',
        name='accounttype'
    )
    instrument_type_enum = sa.Enum(
        'equity', 'bond', 'etf', 'currency', 'commodity', 'crypto', 'custom',
        name='instrumenttype'
    )
    transaction_type_enum = sa.Enum(
        'buy', 'sell', 'dividend', 'coupon', 'tax', 'fee', 'deposit', 'withdrawal', 'split', 'spin_off', 'merger',
        name='transactiontype'
    )
    
    account_type_enum.create(op.get_bind())
    instrument_type_enum.create(op.get_bind())
    transaction_type_enum.create(op.get_bind())
    
    # Создаем таблицу пользователей
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('locale', sa.String(length=10), nullable=False, server_default='ru'),
        sa.Column('timezone', sa.String(length=50), nullable=False, server_default='Europe/Moscow'),
        sa.Column('base_currency', sa.String(length=3), nullable=False, server_default='RUB'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    
    # Создаем индексы для пользователей
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_email', 'users', ['email'])
    
    # Создаем таблицу портфелей
    op.create_table(
        'portfolios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('base_currency', sa.String(length=3), nullable=False, server_default='RUB'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
    )
    
    # Создаем индексы для портфелей
    op.create_index('ix_portfolios_id', 'portfolios', ['id'])
    op.create_index('ix_portfolios_owner_id', 'portfolios', ['owner_id'])
    
    # Создаем таблицу инструментов
    op.create_table(
        'instruments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ticker', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('instrument_type', instrument_type_enum, nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('lot', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Создаем индексы для инструментов
    op.create_index('ix_instruments_id', 'instruments', ['id'])
    op.create_index('ix_instruments_ticker', 'instruments', ['ticker'])


def downgrade() -> None:
    """Downgrade schema."""
    
    # Удаляем таблицы в обратном порядке
    op.drop_table('instruments')
    op.drop_table('portfolios')
    op.drop_table('users')
    
    # Удаляем enum типы
    sa.Enum(name='transactiontype').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='instrumenttype').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='accounttype').drop(op.get_bind(), checkfirst=False)