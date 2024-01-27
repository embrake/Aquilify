"""
The module containing each of the different default types in AQUILIFY_SQLite_ORM as an Enum.
"""

from enum import Enum
from .blob import BlobField
from .boolean import Boolean
from .date import Date
from .float import Float
from .integer import Integer
from .string import String
from .time import Time
from .varchar import VarcharField
from .auto import AutoField
from .bigint import BigintField
from .char import CharField
from .real import RealField

Types = Enum("Types", {sql_type.__name__: sql_type for sql_type in (
    BlobField, Boolean, Date, Float, Integer, String, Time, VarcharField, AutoField, BigintField, RealField, CharField
    )})
