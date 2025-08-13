"""
Интеграционные тесты базы данных.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database_sync import engine, get_db
from app.models.user import User
from app.models.portfolio import Portfolio


class TestDatabaseConnection:
    """Тесты подключения к базе данных."""

    def test_database_connection(self):
        """Тест подключения к базе данных."""
        with engine.begin() as conn:
            result = conn.execute(text("SELECT 1 as test_value"))
            row = result.fetchone()
            assert row[0] == 1

    def test_database_session(self):
        """Тест создания сессии базы данных."""
        db = next(get_db())
        try:
            # Проверяем что сессия создается
            assert isinstance(db, Session)
            
            # Проверяем что можем выполнить запрос
            result = db.execute(text("SELECT 1 as test_value"))
            row = result.fetchone()
            assert row[0] == 1
        finally:
            db.close()

    def test_database_tables_exist(self):
        """Тест что таблицы существуют в базе данных."""
        db = next(get_db())
        try:
            # Проверяем что основные таблицы существуют
            tables_to_check = [
                'users',
                'portfolios',
                'transactions',
                'holdings',
                'instruments'
            ]
            
            for table_name in tables_to_check:
                # Проверяем что можем выполнить SELECT к таблице
                result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                count = result.scalar()
                assert isinstance(count, int)
                
        finally:
            db.close()


class TestUserModel:
    """Интеграционные тесты модели User."""

    def test_create_user(self):
        """Тест создания пользователя."""
        db = next(get_db())
        try:
            # Создаем тестового пользователя
            user = User(
                email="test@example.com",
                username="testuser",
                full_name="Test User",
                hashed_password="hashed_password_here",
                is_active=True
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # Проверяем что пользователь создан
            assert user.id is not None
            assert user.email == "test@example.com"
            assert user.username == "testuser"
            assert user.is_active is True
            
            # Очистка
            db.delete(user)
            db.commit()
            
        finally:
            db.close()

    def test_user_email_uniqueness(self):
        """Тест уникальности email пользователя."""
        db = next(get_db())
        try:
            # Создаем первого пользователя
            user1 = User(
                email="unique@example.com",
                username="user1",
                full_name="User One",
                hashed_password="hashed_password_here"
            )
            db.add(user1)
            db.commit()
            
            # Пытаемся создать второго с тем же email
            user2 = User(
                email="unique@example.com",
                username="user2",
                full_name="User Two",
                hashed_password="hashed_password_here"
            )
            db.add(user2)
            
            # Должна быть ошибка уникальности
            with pytest.raises(Exception):
                db.commit()
                
            db.rollback()
            
            # Очистка
            db.delete(user1)
            db.commit()
            
        finally:
            db.close()


class TestPortfolioModel:
    """Интеграционные тесты модели Portfolio."""

    def test_create_portfolio_with_user(self):
        """Тест создания портфеля с пользователем."""
        db = next(get_db())
        try:
            # Создаем пользователя
            user = User(
                email="portfolio_test@example.com",
                username="portfoliouser",
                full_name="Portfolio User",
                hashed_password="hashed_password_here"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # Создаем портфель
            portfolio = Portfolio(
                name="Test Portfolio",
                description="Test Description",
                user_id=user.id,
                currency="RUB"
            )
            db.add(portfolio)
            db.commit()
            db.refresh(portfolio)
            
            # Проверяем
            assert portfolio.id is not None
            assert portfolio.name == "Test Portfolio"
            assert portfolio.user_id == user.id
            assert portfolio.currency == "RUB"
            
            # Проверяем связь
            assert portfolio.user.email == "portfolio_test@example.com"
            
            # Очистка
            db.delete(portfolio)
            db.delete(user)
            db.commit()
            
        finally:
            db.close()


class TestDatabaseTransactions:
    """Тесты транзакций базы данных."""

    def test_transaction_rollback(self):
        """Тест отката транзакции."""
        db = next(get_db())
        try:
            # Создаем пользователя
            user = User(
                email="rollback_test@example.com",
                username="rollbackuser",
                full_name="Rollback User",
                hashed_password="hashed_password_here"
            )
            db.add(user)
            db.flush()  # Отправляем в БД но не коммитим
            
            user_id = user.id
            assert user_id is not None
            
            # Откатываем транзакцию
            db.rollback()
            
            # Проверяем что пользователь не сохранился
            found_user = db.query(User).filter(User.id == user_id).first()
            assert found_user is None
            
        finally:
            db.close()

    def test_transaction_commit(self):
        """Тест коммита транзакции."""
        db = next(get_db())
        try:
            # Создаем пользователя
            user = User(
                email="commit_test@example.com",
                username="commituser",
                full_name="Commit User",
                hashed_password="hashed_password_here"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            user_id = user.id
            assert user_id is not None
            
            # Создаем новую сессию и проверяем что пользователь есть
            db.close()
            db = next(get_db())
            
            found_user = db.query(User).filter(User.id == user_id).first()
            assert found_user is not None
            assert found_user.email == "commit_test@example.com"
            
            # Очистка
            db.delete(found_user)
            db.commit()
            
        finally:
            db.close()


class TestDatabasePerformance:
    """Тесты производительности базы данных."""

    def test_bulk_insert_performance(self):
        """Тест производительности массовой вставки."""
        import time
        
        db = next(get_db())
        try:
            start_time = time.time()
            
            # Создаем пользователей в bulk
            users = []
            for i in range(100):
                user = User(
                    email=f"bulk_user_{i}@example.com",
                    username=f"bulkuser{i}",
                    full_name=f"Bulk User {i}",
                    hashed_password="hashed_password_here"
                )
                users.append(user)
            
            db.add_all(users)
            db.commit()
            
            end_time = time.time()
            
            # Проверяем что вставка выполнилась быстро (< 5 сек)
            assert (end_time - start_time) < 5.0
            
            # Проверяем количество созданных пользователей
            count = db.query(User).filter(User.email.like("bulk_user_%@example.com")).count()
            assert count == 100
            
            # Очистка
            db.query(User).filter(User.email.like("bulk_user_%@example.com")).delete()
            db.commit()
            
        finally:
            db.close()

    def test_query_performance(self):
        """Тест производительности запросов."""
        import time
        
        db = next(get_db())
        try:
            # Создаем тестовых пользователей
            users = []
            for i in range(50):
                user = User(
                    email=f"query_test_{i}@example.com",
                    username=f"queryuser{i}",
                    full_name=f"Query User {i}",
                    hashed_password="hashed_password_here"
                )
                users.append(user)
            
            db.add_all(users)
            db.commit()
            
            # Тестируем производительность запросов
            start_time = time.time()
            
            for i in range(50):
                user = db.query(User).filter(User.email == f"query_test_{i}@example.com").first()
                assert user is not None
            
            end_time = time.time()
            
            # Проверяем что запросы выполняются быстро
            assert (end_time - start_time) < 2.0
            
            # Очистка
            db.query(User).filter(User.email.like("query_test_%@example.com")).delete()
            db.commit()
            
        finally:
            db.close()
