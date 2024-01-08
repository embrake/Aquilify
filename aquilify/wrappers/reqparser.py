from . import Request
from ..datastructure.core import MultiDict
from copy import deepcopy

from typing import (
    Any,
    Dict,
    Union,
    Optional,
    List,
    Callable
)

class ReqparserError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:
        return str(self.message)

    def __json__(self) -> str:
        return str(self)

    def __dict__(self) -> dict:
        return {'error': str(self)}

class Reqparser:
    def __init__(self) -> None:
        self.args: List[Dict[str, Union[str, bool, type, str, Any, Callable]]] = []

    def add_argument(
        self,
        name: str,
        required: bool = True,
        location: Union[str, List[str]] = 'json',
        type: type = str,
        help: str = '',
        default: Optional[Any] = None,
        store_missing: Optional[Any] = None,
        trim: bool = False,
        ignore: bool = False,
        choices: Optional[List[Any]] = None,
        error: Optional[str] = None,
        dest: Optional[str] = None,
        validation: Optional[Callable] = None
    ) -> None:
        arg_dict = MultiDict({
            'name': name,
            'required': required,
            'location': location if isinstance(location, list) else [location],
            'type': type,
            'help': help,
            'default': default,
            'store_missing': store_missing,
            'trim': trim,
            'ignore': ignore,
            'choices': choices,
            'error': error,
            'dest': dest if dest else name,
            'validation': validation
        })
        self.args.append(arg_dict)

    async def parse(self, request: Request) -> Dict[str, Any]:
        parsed_args: Dict[str, Any] = {}
        query_data: Dict[str, str] = request.args

        if request.method == 'GET':
            for arg in self.args:
                if 'query' in arg['location']:
                    value = query_data.get(arg['name'])
                    value = self._process_missing_value(arg, value)

                    if not arg['ignore']:
                        value = self._process_value(arg, value)

                    parsed_args[arg['dest']] = value
                else:
                    parsed_args[arg['dest']] = None

        else:
            json_data: Dict[str, Any] = await request.json()
            form_data: Dict[str, str] = await request.form()

            for arg in self.args:
                value = await self._get_value_by_location(request, arg, query_data, json_data, form_data)
                value = self._process_missing_value(arg, value)

                if not arg['ignore']:
                    value = self._process_value(arg, value)

                parsed_args[arg['dest']] = value

        return parsed_args

    async def _get_value_by_location(
        self,
        request: Request,
        arg: Dict[str, Any],
        query_data: Dict[str, str],
        json_data: Dict[str, Any],
        form_data: Dict[str, str]
    ) -> Any:
        for loc in arg['location']:
            if loc == 'query':
                value = query_data.get(arg['name'])
            elif loc == 'headers':
                value = request.headers.get(arg['name'])
            elif loc == 'form':
                value = form_data.get(arg['name'])
            elif loc == 'cookie':
                value = request.cookies.get(arg['name'])
            elif loc == 'json':
                value = json_data.get(arg['name'])
            else:
                raise ReqparserError(f"Invalid Location type: {loc}")

            if value is not None:
                return value

        return None

    def _process_missing_value(self, arg: Dict[str, Any], value: Any) -> Any:
        if value is None:
            if arg['required']:
                raise ReqparserError(arg['error'] if arg['error'] else f"Missing required argument: {arg['name']}. {arg['help']}")
            value = arg['default'] if arg['default'] is not None else arg['store_missing']
        return value

    def _process_value(self, arg: Dict[str, Any], value: Any) -> Any:
        if isinstance(value, str) and arg['trim']:
            value = value.strip()

        if arg['choices'] is not None and value not in arg['choices']:
            raise ReqparserError(arg['error'] if arg['error'] else f"Invalid value for argument '{arg['name']}'. Choose from: {arg['choices']}")

        if arg['type'] is not None:
            value = self._validate_and_convert_value(arg, value)

        return value

    def _validate_and_convert_value(self, arg: Dict[str, Any], value: Any) -> Any:
        if arg['type'] is int:
            try:
                value = int(value)
            except (ValueError, TypeError):
                raise ReqparserError(arg['error'] if arg['error'] else f"Invalid value for argument '{arg['name']}' type")
        elif arg['type'] is float:
            try:
                value = float(value)
            except (ValueError, TypeError):
                raise ReqparserError(arg['error'] if arg['error'] else f"Invalid value for argument '{arg['name']}' type")
            
        validation_function = arg.get('validation')
        if validation_function:
            try:
                validated_value = validation_function(value)
                value = validated_value
            except ValueError as ve:
                raise ReqparserError(str(ve))

        return value
    
    def copy(self) -> 'Reqparser':
        new_reqparser = Reqparser()
        new_reqparser.args = [arg_dict.copy() for arg_dict in self.args]
        return new_reqparser

    def replace_argument(self, name: str, new_argument: Dict[str, Any]) -> None:
        for arg_dict in self.args:
            if arg_dict['name'] == name:
                arg_dict.update(new_argument)

    def remove_argument(self, name: str) -> None:
        self.args = [arg_dict for arg_dict in self.args if arg_dict['name'] != name]
