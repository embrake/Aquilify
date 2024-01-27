import typing

JsonType = (
    typing.Union[str, int, float, bool, None, 
    typing.Dict[str, typing.Union[str, int, float, bool, None]], 
    typing.List[typing.Union[str, int, float, bool, None]]]
)