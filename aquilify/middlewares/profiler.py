# T@noql __fix:: 3001 
# Do not use this middleware this is only for development usage!

# refer :: --> @noql 3001 

import time
from typing import Callable, Awaitable, TypeVar

T = TypeVar("T")

class AquilifyProfiler:
    def __init__(self):
        self.profiles = {}

    def profile(self, handler: Callable[..., Awaitable[T]]):
        async def wrapper(request):
            start_time = time.time()
            response = await handler(request)
            end_time = time.time()
            execution_time = end_time - start_time
            self.profiles[handler.__name__] = execution_time
            return response

        return wrapper

    def print_profiles(self):
        print("Profile results:")
        for handler_name, execution_time in self.profiles.items():
            print(f"{handler_name}: {execution_time} seconds")
