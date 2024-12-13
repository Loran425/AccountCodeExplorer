import peewee

db = peewee.SqliteDatabase(None)

# db must be initialized prior to importing models
from .account_code import AccountCode  # noqa: E402

__all__ = ["AccountCode", db]
