from contextlib import AbstractContextManager
import sqlite3
from enum import Enum

from .exceptions import SessionExecuteError

class IsolationLevel(Enum):
    DEFERRED = "DEFERRED"
    IMMEDIATE = "IMMEDIATE"
    EXCLUSIVE = "EXCLUSIVE"

class TransactionContextManager(AbstractContextManager):
    def __init__(self, db_connection, isolation_level=IsolationLevel.DEFERRED):
        self._db_connection = db_connection
        self._isolation_level = isolation_level
        self._nested = 0
        self._completed = False

    def __enter__(self):
        self._nested += 1
        if self._nested == 1:
            self._db_connection.execute(f"BEGIN {self._isolation_level.value} TRANSACTION")
        else:
            self._db_connection.execute(f"SAVEPOINT sp_{self._nested}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._nested -= 1
        if self._nested == 0:
            if exc_type is None and not self._completed:
                self.commit()
            else:
                self.rollback()

    def commit(self):
        """Manually commit the transaction."""
        if not self._completed:
            try:
                self._db_connection.execute("COMMIT")
                self._completed = True
            except sqlite3.Error as e:
                raise SessionExecuteError(f"Error committing transaction: {e}") from e

    def rollback(self):
        """Manually roll back the transaction."""
        if not self._completed:
            try:
                self._db_connection.execute("ROLLBACK")
                self._completed = True
            except sqlite3.Error as e:
                raise SessionExecuteError(f"Error rolling back transaction: {e}") from e

    def __call__(self, isolation_level=IsolationLevel.DEFERRED):
        """Allows chaining transaction context managers."""
        return TransactionContextManager(self._db_connection, isolation_level)
