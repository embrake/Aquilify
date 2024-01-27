
class AXORMException(Exception):
    pass


class ModelException(Exception):
    pass


class FieldException(Exception):
    pass


class ObjectNotExists(Exception):
    pass


class InvalidConfiguration(AXORMException):
    pass


class ConnectionError(AXORMException):
    pass

class SQLExecutionError(AXORMException):
    pass