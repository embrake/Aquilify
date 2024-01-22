import os
import shutil
import asyncio
from aiofiles import open as aio_open
from typing import List, Tuple, Optional

class FileSizeLimitExceeded(Exception):
    pass

class FileSystemStorage:
    def __init__(self, base_location: str) -> None:
        self.base_location = base_location

    async def save(self, name: str, content: bytes) -> None:
        file_path = os.path.join(self.base_location, name)
        async with aio_open(file_path, 'wb') as file:
            await file.write(content)

    async def open(self, name: str, mode='rb'):
        file_path = os.path.join(self.base_location, name)
        return await aio_open(file_path, mode)

    async def read_text(self, name: str) -> str:
        file_path = os.path.join(self.base_location, name)
        async with aio_open(file_path, 'r', encoding='utf-8') as file:
            return await file.read()

    async def write_text(self, name: str, content: str) -> None:
        file_path = os.path.join(self.base_location, name)
        async with aio_open(file_path, 'w', encoding='utf-8') as file:
            await file.write(content)

    async def append_text(self, name: str, content: str) -> None:
        file_path = os.path.join(self.base_location, name)
        async with aio_open(file_path, 'a', encoding='utf-8') as file:
            await file.write(content)

    async def delete(self, name: str) -> None:
        file_path = os.path.join(self.base_location, name)
        try:
            os.remove(file_path)
        except FileNotFoundError:
            pass

    async def exists(self, name: str) -> bool:
        file_path = os.path.join(self.base_location, name)
        return os.path.exists(file_path)

    async def is_file(self, name: str) -> bool:
        file_path = os.path.join(self.base_location, name)
        return os.path.isfile(file_path)

    async def is_dir(self, name: str) -> bool:
        file_path = os.path.join(self.base_location, name)
        return os.path.isdir(file_path)

    async def listdir(self, path: str = '.') -> List[str]:
        directory = os.path.join(self.base_location, path)
        if os.path.isdir(directory):
            return os.listdir(directory)
        return []

    async def rename(self, old_name: str, new_name: str) -> None:
        old_path = os.path.join(self.base_location, old_name)
        new_path = os.path.join(self.base_location, new_name)
        try:
            os.rename(old_path, new_path)
        except FileNotFoundError:
            pass

    async def move(self, old_name: str, new_name: str) -> None:
        old_path = os.path.join(self.base_location, old_name)
        new_path = os.path.join(self.base_location, new_name)
        try:
            shutil.move(old_path, new_path)
        except FileNotFoundError:
            pass

    async def copy(self, old_name: str, new_name: str) -> None:
        old_path = os.path.join(self.base_location, old_name)
        new_path = os.path.join(self.base_location, new_name)
        try:
            shutil.copy2(old_path, new_path)
        except FileNotFoundError:
            pass

    async def mkdir(self, name: str) -> None:
        directory_path = os.path.join(self.base_location, name)
        try:
            os.makedirs(directory_path)
        except FileExistsError:
            pass

    async def stat(self, name: str) -> Optional[os.stat_result]:
        file_path = os.path.join(self.base_location, name)
        try:
            return os.stat(file_path)
        except FileNotFoundError:
            pass

    async def chmod(self, name: str, mode: int) -> None:
        file_path = os.path.join(self.base_location, name)
        try:
            os.chmod(file_path, mode)
        except FileNotFoundError:
            pass

    async def rmtree(self, name: str) -> None:
        directory_path = os.path.join(self.base_location, name)
        try:
            shutil.rmtree(directory_path)
        except FileNotFoundError:
            pass

    async def walk(self, top: str = '.') -> Tuple[List[str], List[str]]:
        top_path = os.path.join(self.base_location, top)
        files = []
        dirs = []
        for root, directories, filenames in os.walk(top_path):
            for directory in directories:
                dirs.append(os.path.relpath(os.path.join(root, directory), self.base_location))
            for filename in filenames:
                files.append(os.path.relpath(os.path.join(root, filename), self.base_location))
        return dirs, files

    async def abspath(self, name: str) -> Optional[str]:
        file_path = os.path.join(self.base_location, name)
        try:
            return os.path.abspath(file_path)
        except FileNotFoundError:
            pass

    async def get_file_size(self, name: str) -> Optional[int]:
        file_path = os.path.join(self.base_location, name)
        try:
            return os.path.getsize(file_path)
        except FileNotFoundError:
            return None

    async def check_file_size(self, name: str, max_size: int) -> None:
        file_size = await self.get_file_size(name)
        if file_size and file_size > max_size:
            raise FileSizeLimitExceeded(f"File '{name}' exceeds the maximum allowed size.")

    async def change_permissions(self, name: str, mode: int) -> None:
        file_path = os.path.join(self.base_location, name)
        try:
            os.chmod(file_path, mode)
        except FileNotFoundError:
            pass

    async def remove(self, name: str) -> None:
        file_path = os.path.join(self.base_location, name)
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, os.remove, file_path)
        except FileNotFoundError:
            pass


