import typing
from collections import defaultdict

class SignalHandler:
    async def handle_signal(self, sender, *args, **kwargs):
        raise NotImplementedError("Subclasses must implement the handle_signal method.")

class Connection:
    def __init__(self, handler, priority=0):
        self.handler = handler
        self.priority = priority

    def __repr__(self):
        return f"Connection(handler={self.handler_repr()}, priority={self.priority})"

    def __eq__(self, other):
        return isinstance(other, Connection) and self.handler == other.handler and self.priority == other.priority

    def __hash__(self):
        return hash((self.handler, self.priority))

    def handler_repr(self):
        return f"{getattr(self.handler, '__name__', repr(self.handler))} ({type(self.handler).__name__})"

class Signal:
    def __init__(self):
        self.connections = set()
        self.received_signals = []
        self.sender_handler_mapping = defaultdict(set)

    def connect(self, handler: typing.Union[typing.Callable, SignalHandler], priority: int = 0) -> None:
        if not (callable(handler) or isinstance(handler, SignalHandler)):
            raise TypeError("Handler must be callable or subclass of SignalHandler.")
        
        existing_connection = next((conn for conn in self.connections if conn.handler == handler), None)

        if existing_connection:
            existing_connection.priority = priority
        else:
            connection = Connection(handler, priority)
            self._add_connection(connection)

    def _add_connection(self, connection: Connection) -> None:
        self.connections.add(connection)
        self.sender_handler_mapping[connection.handler].add(connection)

    def disconnect(self, handler: typing.Optional[typing.Callable] = None, priority: typing.Optional[int] = None) -> None:
        connections_to_remove = {conn for conn in self.connections if (handler is None or conn.handler == handler) and (priority is None or conn.priority == priority)}
        self._remove_connections(connections_to_remove)

    def disconnect_all(self) -> None:
        self._remove_connections(set(self.connections))

    def _remove_connections(self, connections_to_remove: typing.Set[Connection]) -> None:
        self.connections -= connections_to_remove
        for connection in connections_to_remove:
            self.sender_handler_mapping[connection.handler].remove(connection)

    async def __call__(self, sender: str, *args, **kwargs) -> typing.List[typing.Any]:
        results = []
        exceptions = []

        for connection in sorted(self.connections, key=lambda x: x.priority, reverse=True):
            try:
                result = await self._call_handler(connection, sender, *args, **kwargs)
                results.append(result)
            except Exception as e:
                exceptions.append((connection, e))
                self._remove_connections({connection})

        self._reinsert_connections()

        formatted_args = args[0] if len(args) == 1 else args
        self.received_signals.append({'sender': sender, 'results': results, 'exceptions': exceptions, 'args': formatted_args})
        return results

    async def _call_handler(self, connection: Connection, sender: str, *args, **kwargs) -> typing.Any:
        if isinstance(connection.handler, SignalHandler):
            return await connection.handler.handle_signal(sender, *args, **kwargs)
        else:
            return await connection.handler(sender, *args, **kwargs)

    def _reinsert_connections(self) -> None:
        for connection in self.connections:
            self.sender_handler_mapping[connection.handler].add(connection)

    def receive(self, sender: typing.Optional[str] = None,
                handler: typing.Optional[typing.Union[typing.Callable, SignalHandler]] = None,
                args_filter: typing.Optional[typing.Callable] = None,
                results_filter: typing.Optional[typing.Callable] = None) -> typing.List[typing.Dict[str, typing.Any]]:
        filtered_signals = [signal for signal in self.received_signals if 
                            (sender is None or signal['sender'] == sender) and
                            (handler is None or handler in self.sender_handler_mapping and
                             any(conn.priority == handler for conn in self.sender_handler_mapping[handler])) and
                            (args_filter is None or args_filter(signal['args'])) and
                            (results_filter is None or results_filter(signal['results']))]

        return filtered_signals

    def disconnect_sender(self, sender: str) -> None:
        connections_to_remove = {conn for conn in self.connections if any(signal['sender'] == sender for signal in self.received_signals)}
        self._remove_connections(connections_to_remove)

    def disconnect_handler(self, handler: typing.Optional[typing.Union[typing.Callable, SignalHandler]] = None) -> None:
        connections_to_remove = {conn for conn in self.connections if conn.handler == handler}
        self._remove_connections(connections_to_remove)

    def clear_received_signals(self) -> None:
        self.received_signals.clear()

    def __str__(self) -> str:
        return f"Signal(connections={len(self.connections)}, received_signals={len(self.received_signals)})"

signals = Signal()