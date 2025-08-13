-- Инициализация базы данных для сервиса учета инвестиций
-- Выполняется при первом запуске PostgreSQL контейнера

-- Создаем расширения
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Создаем пользователя для приложения (если не существует)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'investment_app') THEN
        CREATE ROLE investment_app WITH LOGIN PASSWORD 'secure_app_password';
    END IF;
END
$$;

-- Предоставляем права
GRANT CONNECT ON DATABASE investment_db TO investment_app;
GRANT USAGE ON SCHEMA public TO investment_app;
GRANT CREATE ON SCHEMA public TO investment_app;

-- Создаем схему для аудита
CREATE SCHEMA IF NOT EXISTS audit;
GRANT USAGE ON SCHEMA audit TO investment_app;
GRANT CREATE ON SCHEMA audit TO investment_app;

-- Создаем enum типы
DO $$
BEGIN
    -- Enum для типов инструментов
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'instrument_type') THEN
        CREATE TYPE instrument_type AS ENUM (
            'equity',
            'bond', 
            'etf',
            'currency',
            'commodity',
            'crypto',
            'custom'
        );
    END IF;

    -- Enum для типов транзакций
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'transaction_type') THEN
        CREATE TYPE transaction_type AS ENUM (
            'buy',
            'sell',
            'dividend',
            'coupon',
            'tax',
            'fee',
            'deposit',
            'withdrawal',
            'split',
            'spin_off',
            'merger'
        );
    END IF;

    -- Enum для типов кэшфлоу
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'cashflow_type') THEN
        CREATE TYPE cashflow_type AS ENUM (
            'dividend',
            'coupon',
            'interest',
            'rental',
            'other'
        );
    END IF;

    -- Enum для типов целей
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'goal_type') THEN
        CREATE TYPE goal_type AS ENUM (
            'capital',
            'passive_income',
            'expense_ratio'
        );
    END IF;

    -- Enum для типов алертов
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'alert_type') THEN
        CREATE TYPE alert_type AS ENUM (
            'price_move',
            'threshold',
            'event',
            'dividend',
            'goal_progress'
        );
    END IF;

    -- Enum для каналов уведомлений
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'notification_channel') THEN
        CREATE TYPE notification_channel AS ENUM (
            'email',
            'push',
            'telegram',
            'webhook'
        );
    END IF;

    -- Enum для статуса импорта
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'import_status') THEN
        CREATE TYPE import_status AS ENUM (
            'pending',
            'processing',
            'completed',
            'failed',
            'cancelled'
        );
    END IF;

    -- Enum для источников импорта
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'import_source') THEN
        CREATE TYPE import_source AS ENUM (
            'csv',
            'xlsx',
            'xls',
            'pdf',
            'api_tinkoff',
            'api_binance',
            'manual'
        );
    END IF;

    -- Enum для типов счетов
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'account_type') THEN
        CREATE TYPE account_type AS ENUM (
            'broker',
            'ira',
            'pension',
            'savings',
            'checking',
            'crypto_exchange',
            'other'
        );
    END IF;

    -- Enum для статуса уведомлений
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'notification_status') THEN
        CREATE TYPE notification_status AS ENUM (
            'pending',
            'sent',
            'failed',
            'read'
        );
    END IF;
END
$$;

-- Создаем функцию для обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Создаем функцию для аудита
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit.audit_log (
            table_name,
            operation,
            row_id,
            new_data,
            changed_by,
            changed_at
        ) VALUES (
            TG_TABLE_NAME,
            TG_OP,
            NEW.id,
            row_to_json(NEW),
            current_user,
            CURRENT_TIMESTAMP
        );
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit.audit_log (
            table_name,
            operation,
            row_id,
            old_data,
            new_data,
            changed_by,
            changed_at
        ) VALUES (
            TG_TABLE_NAME,
            TG_OP,
            NEW.id,
            row_to_json(OLD),
            row_to_json(NEW),
            current_user,
            CURRENT_TIMESTAMP
        );
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit.audit_log (
            table_name,
            operation,
            row_id,
            old_data,
            changed_by,
            changed_at
        ) VALUES (
            TG_TABLE_NAME,
            TG_OP,
            OLD.id,
            row_to_json(OLD),
            current_user,
            CURRENT_TIMESTAMP
        );
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Настройки для производительности
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '512MB';
ALTER SYSTEM SET effective_cache_size = '2GB';
ALTER SYSTEM SET work_mem = '16MB';
ALTER SYSTEM SET maintenance_work_mem = '256MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- Перезагружаем конфигурацию
SELECT pg_reload_conf();
