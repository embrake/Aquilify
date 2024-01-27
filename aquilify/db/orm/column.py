from .filters import MagicFilter


class Column(MagicFilter):
    def __init__(self, type: str, not_null: bool = False, default: object = None, autoincrement: bool = False,
                 unique: bool = False, primary_key: bool = False, check: str = None) -> None:

        """
        Standard class for creating a column object.

        :param type: Data type
        :param not_null: Causes the column to not be NULL
        :param default: Sets the default value for the insert
        :param autoincrement: Causes a unique number to be generated automatically
        :param unique: Ensures that all values in a column are distinct
        :param primary_key: Uniquely identifies each entry in a table
        :param check: Used to limit the range of values that can be placed in a column
        """

        super().__init__("")

        self.type = type
        self.options = self._serialize_options(
            not_null, default, autoincrement, unique, primary_key, check
        )

    @staticmethod
    def _serialize_options(not_null: bool = False, default: object = None, autoincrement: bool = False,
                           unique: bool = False, primary_key: bool = False, check: str = None) -> str:

        options = []
        if not_null:
            options.append("NOT NULL")
        if primary_key:
            options.append("PRIMARY KEY")
        if autoincrement:
            options.append("AUTOINCREMENT")
        if unique:
            options.append("UNIQUE")
        if default:
            options.append(f"DEFAULT {default}")
        if check:
            options.append(f"CHECK({check})")

        return " ".join(options)


class ColumnType(MagicFilter):
    def __init__(self, table: str, name: str, type: str, options: str = "") -> None:

        """
        System class used to store additional column values.

        :param table: Parent table name
        :param name: Column name
        :param type: Column type
        :param options: Column options
        """

        super().__init__(f"{table}.{name}", parameters={"table": table})

        self.table = table
        self.name = name
        self.type = type
        self.options = options

    def serialize(self) -> str:
        """
        Function to serialize basic steam.

        :return: Serialized string
        """

        return f"{self.name} {self.type.upper()} {self.options}".strip()