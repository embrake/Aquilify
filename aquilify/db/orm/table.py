from .column import Column, ColumnType


class TableMeta(type):
    def __getattribute__(cls, item: str) -> ColumnType | object:

        """
        A function to change the class of a column to that.

        :param item: Variable key
        :return: Replaced object or standard object
        """

        data = super().__getattribute__(item)
        if isinstance(data, Column):
            return ColumnType(cls.__tablename__, item, data.type, data.options)

        return data


class Table(object, metaclass=TableMeta):
    __tablename__ = "null"

    def __init__(self, **values) -> None:

        """
        Row initialization for a table with given parameters.

        :param values: The values that the table takes
        """

        self.values = values

    @classmethod
    def columns(cls) -> dict[str, ColumnType]:

        """
        Returns all columns defined in the new table.

        :return: Defined columns
        """

        return {attribute: getattr(cls, attribute)
                for attribute in dir(cls)
                if isinstance(getattr(cls, attribute), ColumnType)}


class DynamicTable(object):
    def __init__(self, name: str, columns: dict[str, Column | ColumnType]) -> None:

        """
        Dynamic table initializer.

        :param name: Table name
        :param columns: Table columns
        """

        self.__tablename__ = name

        for key, column in columns.items():
            self.add(key, column)

    def add(self, key: str, column: Column | ColumnType) -> None:

        """
        Adds a new column to the table.

        :param key: Column name
        :param column: Column object
        :return: Nothing
        """

        self.__setattr__(key, ColumnType(self.__tablename__, key, column.type, column.options))

    def columns(self) -> dict[str, ColumnType]:

        """
        Returns all columns defined in the new table.

        :return: Defined columns
        """

        return {attribute: getattr(self, attribute)
                for attribute in dir(self)
                if isinstance(getattr(self, attribute), ColumnType)}

    def __call__(self, **values) -> Table:

        """
        Row initialization for a dynamic table with given parameters.

        :param values: The values that the table takes
        :return: Initialized table object
        """

        class TempTable(Table):
            __tablename__ = self.__tablename__

        for key, column in self.columns().items():
            setattr(TempTable, key, column)

        return TempTable(**values)
