"""
Сервис для импорта данных от брокеров.
"""

import csv
import hashlib
import json
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime
from io import StringIO
from abc import ABC, abstractmethod

import pandas as pd
from sqlalchemy.orm import Session

from app.models.transaction import TransactionType
from app.repositories.transaction import TransactionRepository
from app.core.logging import logger


class ImportError(Exception):
    """Ошибка импорта данных."""
    pass


class BrokerImportAdapter(ABC):
    """Абстрактный адаптер для импорта данных брокера."""
    
    @abstractmethod
    def get_broker_name(self) -> str:
        """Возвращает название брокера."""
        pass
    
    @abstractmethod
    def parse_csv(self, csv_content: str) -> List[Dict[str, Any]]:
        """Парсит CSV данные и возвращает стандартизированный список транзакций."""
        pass
    
    @abstractmethod
    def validate_format(self, csv_content: str) -> bool:
        """Проверяет, соответствует ли файл формату данного брокера."""
        pass


class TinkoffImportAdapter(BrokerImportAdapter):
    """Адаптер для импорта отчетов Тинькофф."""
    
    def get_broker_name(self) -> str:
        return "Тинькофф"
    
    def validate_format(self, csv_content: str) -> bool:
        """Проверяет формат Тинькофф по заголовкам."""
        try:
            lines = csv_content.strip().split('\n')
            if len(lines) < 2:
                return False
            
            header = lines[0].lower()
            expected_columns = ['дата', 'время', 'тип', 'инструмент', 'количество', 'цена', 'сумма']
            
            return all(col in header for col in expected_columns[:3])
        except:
            return False
    
    def parse_csv(self, csv_content: str) -> List[Dict[str, Any]]:
        """Парсит CSV отчет Тинькофф."""
        transactions = []
        
        try:
            # Читаем CSV
            df = pd.read_csv(StringIO(csv_content), sep=';')
            
            # Стандартизируем названия колонок
            column_mapping = {
                'Дата': 'date',
                'Время': 'time', 
                'Тип операции': 'operation_type',
                'Инструмент': 'instrument',
                'Тикер': 'ticker',
                'Количество': 'quantity',
                'Цена': 'price',
                'Сумма': 'amount',
                'Валюта': 'currency',
                'Комиссия': 'fee',
                'НКД': 'accrued_interest'
            }
            
            # Переименовываем колонки
            df = df.rename(columns=column_mapping)
            
            for _, row in df.iterrows():
                try:
                    # Парсим дату и время
                    date_str = str(row.get('date', ''))
                    time_str = str(row.get('time', '00:00:00'))
                    
                    if date_str and date_str != 'nan':
                        # Пробуем разные форматы даты
                        for date_format in ['%d.%m.%Y', '%Y-%m-%d', '%d/%m/%Y']:
                            try:
                                date_obj = datetime.strptime(date_str, date_format)
                                break
                            except ValueError:
                                continue
                        else:
                            logger.warning(f"Не удалось распарсить дату: {date_str}")
                            continue
                        
                        # Добавляем время
                        if time_str and time_str != 'nan':
                            try:
                                time_obj = datetime.strptime(time_str, '%H:%M:%S').time()
                                timestamp = datetime.combine(date_obj.date(), time_obj)
                            except ValueError:
                                timestamp = date_obj
                        else:
                            timestamp = date_obj
                    else:
                        continue
                    
                    # Определяем тип операции
                    operation_type = str(row.get('operation_type', '')).lower()
                    transaction_type = self._map_operation_type(operation_type)
                    
                    if not transaction_type:
                        logger.warning(f"Неизвестный тип операции: {operation_type}")
                        continue
                    
                    # Извлекаем данные
                    ticker = str(row.get('ticker', row.get('instrument', ''))).strip()
                    quantity = self._parse_decimal(row.get('quantity'))
                    price = self._parse_decimal(row.get('price'))
                    amount = self._parse_decimal(row.get('amount'))
                    currency = str(row.get('currency', 'RUB')).upper()
                    fee = self._parse_decimal(row.get('fee', 0))
                    
                    # Формируем транзакцию
                    transaction = {
                        'ts': timestamp,
                        'transaction_type': transaction_type,
                        'ticker': ticker if ticker != 'nan' else None,
                        'quantity': quantity,
                        'price': price,
                        'gross': amount,
                        'fee': fee,
                        'currency': currency,
                        'meta': json.dumps({
                            'broker': self.get_broker_name(),
                            'original_operation': operation_type,
                            'raw_data': row.to_dict()
                        }),
                        'source_hash': self._calculate_row_hash(row.to_dict())
                    }
                    
                    transactions.append(transaction)
                    
                except Exception as e:
                    logger.warning(f"Ошибка обработки строки: {e}")
                    continue
        
        except Exception as e:
            raise ImportError(f"Ошибка парсинга CSV Тинькофф: {e}")
        
        return transactions
    
    def _map_operation_type(self, operation: str) -> Optional[TransactionType]:
        """Маппинг типов операций Тинькофф в стандартные типы."""
        mapping = {
            'покупка': TransactionType.BUY,
            'продажа': TransactionType.SELL,
            'дивиденды': TransactionType.DIVIDEND,
            'купон': TransactionType.COUPON,
            'пополнение': TransactionType.DEPOSIT,
            'вывод средств': TransactionType.WITHDRAWAL,
            'комиссия': TransactionType.FEE,
            'налог': TransactionType.TAX,
            'сплит': TransactionType.SPLIT,
        }
        
        for key, value in mapping.items():
            if key in operation:
                return value
        
        return None
    
    def _parse_decimal(self, value) -> Optional[Decimal]:
        """Парсинг числового значения."""
        if value is None or str(value).lower() in ['nan', '', 'none']:
            return None
        
        try:
            # Убираем пробелы и заменяем запятую на точку
            value_str = str(value).replace(' ', '').replace(',', '.')
            return Decimal(value_str)
        except:
            return None
    
    def _calculate_row_hash(self, row_data: Dict[str, Any]) -> str:
        """Вычисляет хеш строки для дедупликации."""
        # Создаем строку из ключевых полей
        key_fields = ['date', 'time', 'operation_type', 'instrument', 'amount']
        hash_string = '|'.join(str(row_data.get(field, '')) for field in key_fields)
        
        return hashlib.new('md5', hash_string.encode(), usedforsecurity=False).hexdigest()


class SberbankImportAdapter(BrokerImportAdapter):
    """Адаптер для импорта отчетов Сбербанк."""
    
    def get_broker_name(self) -> str:
        return "Сбербанк"
    
    def validate_format(self, csv_content: str) -> bool:
        """Проверяет формат Сбербанк."""
        try:
            lines = csv_content.strip().split('\n')
            if len(lines) < 2:
                return False
            
            header = lines[0].lower()
            return 'сбербанк' in header or 'дата сделки' in header
        except:
            return False
    
    def parse_csv(self, csv_content: str) -> List[Dict[str, Any]]:
        """Парсит CSV отчет Сбербанк."""
        # Упрощенная реализация - можно расширить
        transactions = []
        
        try:
            df = pd.read_csv(StringIO(csv_content), sep=';')
            
            # Маппинг колонок Сбербанк
            column_mapping = {
                'Дата сделки': 'date',
                'Время сделки': 'time',
                'Операция': 'operation_type',
                'Код инструмента': 'ticker',
                'Наименование': 'instrument_name',
                'Кол-во': 'quantity',
                'Цена': 'price',
                'Сумма сделки': 'amount',
                'Валюта': 'currency',
                'Комиссия брокера': 'fee'
            }
            
            df = df.rename(columns=column_mapping)
            
            for _, row in df.iterrows():
                # Аналогичная логика как для Тинькофф
                # ... (можно реализовать позже)
                pass
                
        except Exception as e:
            raise ImportError(f"Ошибка парсинга CSV Сбербанк: {e}")
        
        return transactions


class ImportService:
    """Сервис для импорта данных от брокеров."""
    
    def __init__(self, db: Session):
        self.db = db
        self.transaction_repo = TransactionRepository(db)
        
        # Регистрируем адаптеры брокеров
        self.adapters = [
            TinkoffImportAdapter(),
            SberbankImportAdapter(),
            # Можно добавить другие брокеры
        ]
    
    async def import_csv(
        self,
        account_id: int,
        csv_content: str,
        filename: str = ""
    ) -> Dict[str, Any]:
        """Импорт CSV файла с автоматическим определением формата."""
        
        # Определяем формат файла
        adapter = self._detect_broker_format(csv_content)
        if not adapter:
            raise ImportError("Не удалось определить формат файла. Поддерживаются: Тинькофф, Сбербанк")
        
        logger.info(f"Обнаружен формат: {adapter.get_broker_name()}")
        
        # Парсим транзакции
        try:
            parsed_transactions = adapter.parse_csv(csv_content)
        except Exception as e:
            raise ImportError(f"Ошибка парсинга файла {adapter.get_broker_name()}: {e}")
        
        if not parsed_transactions:
            return {
                'broker': adapter.get_broker_name(),
                'total_rows': 0,
                'imported': 0,
                'skipped': 0,
                'errors': [],
                'transactions': []
            }
        
        # Импортируем транзакции с дедупликацией
        result = await self._import_transactions(account_id, parsed_transactions, adapter.get_broker_name())
        
        return result
    
    def _detect_broker_format(self, csv_content: str) -> Optional[BrokerImportAdapter]:
        """Автоматическое определение формата брокера."""
        for adapter in self.adapters:
            if adapter.validate_format(csv_content):
                return adapter
        return None
    
    async def _import_transactions(
        self,
        account_id: int,
        transactions_data: List[Dict[str, Any]],
        broker_name: str
    ) -> Dict[str, Any]:
        """Импорт списка транзакций с дедупликацией."""
        
        imported_count = 0
        skipped_count = 0
        errors = []
        created_transactions = []
        
        for i, tx_data in enumerate(transactions_data):
            try:
                # Проверяем дедупликацию по хешу
                source_hash = tx_data.get('source_hash')
                if source_hash:
                    is_duplicate = self.transaction_repo.deduplicate_by_hash(
                        account_id, source_hash
                    )
                    if is_duplicate:
                        skipped_count += 1
                        logger.debug(f"Пропущена дублирующаяся транзакция: {source_hash}")
                        continue
                
                # Получаем или создаем инструмент
                instrument_id = None
                ticker = tx_data.get('ticker')
                if ticker:
                    instrument_id = await self._get_or_create_instrument(ticker, tx_data)
                
                # Создаем транзакцию
                transaction = self.transaction_repo.create(
                    account_id=account_id,
                    instrument_id=instrument_id,
                    ts=tx_data['ts'],
                    transaction_type=tx_data['transaction_type'],
                    quantity=tx_data.get('quantity'),
                    price=tx_data.get('price'),
                    gross=tx_data['gross'],
                    fee=tx_data.get('fee'),
                    tax=tx_data.get('tax'),
                    currency=tx_data['currency'],
                    fx_rate=tx_data.get('fx_rate'),
                    meta=tx_data.get('meta')
                )
                
                created_transactions.append({
                    'id': transaction.id,
                    'type': transaction.transaction_type.value,
                    'amount': float(transaction.gross),
                    'currency': transaction.currency,
                    'date': transaction.ts.isoformat()
                })
                
                imported_count += 1
                
            except Exception as e:
                error_msg = f"Строка {i+1}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"Ошибка импорта транзакции: {e}")
        
        return {
            'broker': broker_name,
            'total_rows': len(transactions_data),
            'imported': imported_count,
            'skipped': skipped_count,
            'errors': errors,
            'transactions': created_transactions
        }
    
    async def _get_or_create_instrument(
        self,
        ticker: str,
        tx_data: Dict[str, Any]
    ) -> Optional[int]:
        """Получает или создает инструмент."""
        # Упрощенная реализация - возвращаем None
        # В полной версии здесь должен быть поиск/создание в таблице instruments
        
        # TODO: Реализовать InstrumentRepository и логику создания инструментов
        # instrument_repo = InstrumentRepository(self.db)
        # instrument = await instrument_repo.get_by_ticker(ticker)
        # if not instrument:
        #     instrument = await instrument_repo.create(...)
        # return instrument.id
        
        return None
    
    def generate_example_csv(self, broker: str = "tinkoff") -> str:
        """Генерирует пример CSV файла для указанного брокера."""
        
        if broker.lower() == "tinkoff":
            return """Дата;Время;Тип операции;Инструмент;Тикер;Количество;Цена;Сумма;Валюта;Комиссия
01.01.2024;10:00:00;Покупка;Сбербанк;SBER;10;250.50;2505.00;RUB;5.00
02.01.2024;11:30:00;Дивиденды;Сбербанк;SBER;;12.50;125.00;RUB;0.00
03.01.2024;14:15:00;Продажа;Сбербанк;SBER;5;255.00;1275.00;RUB;3.00"""
        
        elif broker.lower() == "sberbank":
            return """Дата сделки;Время сделки;Операция;Код инструмента;Наименование;Кол-во;Цена;Сумма сделки;Валюта;Комиссия брокера
01.01.2024;10:00:00;Покупка ЦБ;SBER;ПАО Сбербанк;10;250.50;2505.00;RUB;5.00
02.01.2024;11:30:00;Дивиденды;SBER;ПАО Сбербанк;;12.50;125.00;RUB;0.00"""
        
        else:
            return "Неподдерживаемый формат брокера"
    
    def get_supported_brokers(self) -> List[str]:
        """Возвращает список поддерживаемых брокеров."""
        return [adapter.get_broker_name() for adapter in self.adapters]
