class MagicFilter(object):
    def __init__(self, query: str, variables: tuple = None, parameters: dict[str, object] = None) -> None:

        """
        Magic filter used for advanced processing of sql queries

        :param query: Initial query
        :param variables: Query variables
        :param parameters: Parameters saved after writing the query to a new expression
        """

        self.query = query

        self.variables = variables or tuple()
        self.parameters = parameters or dict()

    @staticmethod
    def _serialize_variable(variable: object) -> tuple:
        if isinstance(variable, MagicFilter):
            return variable.variables
        else:
            return (variable,)

    @staticmethod
    def _serialize_query(query: object) -> str:
        if isinstance(query, MagicFilter):
            return query.query
        else:
            return "?"

    @staticmethod
    def _wrap_query(query: str, wrap: bool) -> str:
        return f"({query})" if wrap else query

    def _get_expression(self, other: object, operator: str, *, wrap: bool = False) -> "MagicFilter":
        return MagicFilter(
            f"{self._wrap_query(self.query, wrap)} "
            f"{operator} "
            f"{self._wrap_query(self._serialize_query(other), wrap)}",

            (*self.variables, *self._serialize_variable(other)), self.parameters
        )

    def _invert_expression(self) -> "MagicFilter":
        return MagicFilter(
            f"NOT ({self.query})", self.variables, self.parameters
        )

    def __eq__(self, other: object) -> "MagicFilter":
        return self._get_expression(other, "=")

    def __ne__(self, other: object) -> "MagicFilter":
        return self._get_expression(other, "!=")

    def __ge__(self, other: object) -> "MagicFilter":
        return self._get_expression(other, ">=")

    def __gt__(self, other: object) -> "MagicFilter":
        return self._get_expression(other, ">")

    def __le__(self, other: object) -> "MagicFilter":
        return self._get_expression(other, "<=")

    def __lt__(self, other: object) -> "MagicFilter":
        return self._get_expression(other, "<")

    def __and__(self, other: object) -> "MagicFilter":
        return self._get_expression(other, "AND", wrap=True)

    def __or__(self, other: object) -> "MagicFilter":
        return self._get_expression(other, "OR", wrap=True)

    def __invert__(self) -> "MagicFilter":
        return self._invert_expression()
