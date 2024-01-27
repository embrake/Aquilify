"""
A subpackage containing the logic behind each of the core statements that can be executed in AQUILIFY_SQLite_ORM.
"""

from .create_table import CreateTable
from .insert_into import InsertInto
from .select import Select
from .set import Set
from .statement import Statement
from .delete_from import DeleteFrom
from .drop_table import DropTable
from .pragma import Pragma
from .create_index import CreateIndex