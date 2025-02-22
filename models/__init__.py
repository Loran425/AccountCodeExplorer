import peewee

db = peewee.SqliteDatabase(None)

# db must be initialized prior to importing models
from .account_code import AccountCode, AccountCodeIndex  # noqa: E402

__all__ = ["AccountCode", "AccountCodeIndex", db]
