class IndexField:
    def __init__(self, index_name: str, field_name: str, unique: bool = False) -> None:
        self.index_name = index_name
        self.field_name = field_name
        self.unique = unique

    @property
    def _rtx_001data(self):
        return self.index_name, self.field_name, self.unique