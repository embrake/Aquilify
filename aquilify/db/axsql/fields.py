"""
AQUILIFY_SQLite_ORM is a lightweight, zero-dependency ORM for SQLite in Python.

AQUILIFY_SQLite_ORM is an SQLite ORM for python, designed to be as lightweight, intuitive, and simple to use as possible.
It is designed to closely mimic SQL syntax whilst remaining as pythonic as possible
to save developers valuable time (and brain cells) when interacting with SQLite databases,
by building reusable SQLite query objects using method-chaining, and abstracting away
SQLite's connection and cursor system with a single context manager.
"""

from .types import (
    Integer as Integer,
    String as String,
    Type as Type,
    Boolean as Boolean,
    Date as Date,
    Time as Time,
    BlobField as BlobField,
    Float as Float,
    Types as Types,
    VarcharField as VarcharField,
    AutoField as AutoField,
    BigintField as BigintField,
    CharField as CharField,
    RealField as RealField,
    IndexField as IndexField,
    Field as Field
)