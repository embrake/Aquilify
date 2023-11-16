import asyncio
import os
import stat
import shutil
import json
import tempfile
import hashlib
import logging
import difflib
from contextlib import asynccontextmanager
from typing import List

class AsyncFiles:
    def __init__(self, loop=None):
        """
        Initialize the AsyncFiles class.

        Args:
            loop (asyncio.AbstractEventLoop, optional): The asyncio event loop to use. If not provided, the default
            event loop will be used.

        Attributes:
            loop (asyncio.AbstractEventLoop): The asyncio event loop.
            logger (logging.Logger): Logger for logging operations.

        """
        self.loop = loop or asyncio.get_event_loop()
        self.logger = logging.getLogger('AsyncFiles')
        self.logger.setLevel(logging.DEBUG)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass

    async def open(self, file_path, mode='r', buffering=-1, encoding=None, errors=None, newline=None, closefd=True):
        """
        Asynchronously open a file.

        Args:
            file_path (str): The path to the file to be opened.
            mode (str, optional): The mode in which the file is opened.
            buffering (int, optional): The buffering policy to use.
            encoding (str, optional): The character encoding to use.
            errors (str, optional): How encoding and decoding errors are to be handled.
            newline (str, optional): How newlines are handled when reading and writing files.
            closefd (bool, optional): If True, the underlying file descriptor is closed when the file is closed.

        Returns:
            asyncio.Future: A future representing the opened file.

        Raises:
            IOError: If the file cannot be opened.

        """
        try:
            return await asyncio.to_thread(open, file_path, mode, buffering, encoding, errors, newline, closefd)
        except OSError as e:
            self.logger.error(f"Failed to open {file_path}: {e}")
            raise IOError(f"Failed to open {file_path}: {e}")

    async def read(self, file_path):
        """
        Asynchronously read the contents of a file.

        Args:
            file_path (str): The path to the file to be read.

        Returns:
            str: The content of the file as a string.

        Raises:
            IOError: If the file cannot be opened or read.

        """
        try:
            with await self.open(file_path, 'r') as file:
                return await self.loop.run_in_executor(None, file.read)
        except IOError as e:
            self.logger.error(f"Failed to read {file_path}: {e}")
            raise e

    async def read_lines(self, file_path):
        """
        Asynchronously read the lines of a text file.

        Args:
            file_path (str): The path to the text file to be read.

        Returns:
            list: A list of lines read from the file.

        Raises:
            IOError: If the file cannot be opened or read.

        """
        lines = []
        try:
            with await self.open(file_path, 'r') as file:
                for line in file:
                    lines.append(line.rstrip('\n'))
        except IOError as e:
            self.logger.error(f"Failed to read lines from {file_path}: {e}")
            raise e
        return lines

    async def read_binary(self, file_path):
        """
        Asynchronously read the binary contents of a file.

        Args:
            file_path (str): The path to the binary file to be read.

        Returns:
            bytes: The binary content of the file.

        Raises:
            IOError: If the file cannot be opened or read.

        """
        try:
            with await self.open(file_path, 'rb') as file:
                return await self.loop.run_in_executor(None, file.read)
        except IOError as e:
            self.logger.error(f"Failed to read binary data from {file_path}: {e}")
            raise e

    async def write(self, file_path, data):
        """
        Asynchronously write data to a file.

        Args:
            file_path (str): The path to the file to write data to.
            data (str or bytes): The data to be written.

        Raises:
            IOError: If the file cannot be opened or written to.
            ValueError: If the data type is unsupported.

        """
        try:
            if isinstance(data, str):
                # If data is a string, open the file in text mode
                mode = 'w'
            elif isinstance(data, bytes):
                # If data is bytes, open the file in binary mode
                mode = 'wb'
            else:
                raise ValueError("Data must be a string or bytes")

            await asyncio.to_thread(self._write, file_path, data, mode)
        except IOError as e:
            self.logger.error(f"Failed to write data to {file_path}: {e}")
            raise e

    def _write(self, file_path, data, mode):
        try:
            with open(file_path, mode) as file:
                file.write(data)
        except IOError as e:
            self.logger.error(f"Failed to write data to {file_path}: {e}")
            raise e

    async def append(self, file_path, data):
        """
        Asynchronously append data to a file.

        Args:
            file_path (str): The path to the file to append data to.
            data (str or bytes): The data to be appended.

        Raises:
            IOError: If the file cannot be opened or written to.
            
        """
        try:
            await self.loop.run_in_executor(None, lambda: self._append(file_path, data))
        except IOError as e:
            self.logger.error(f"Failed to append data to {file_path}: {e}")
            raise e

    def _append(self, file_path, data):
        with open(file_path, 'a') as file:
            file.write(data)

    async def close(self, file):
        """
        Asynchronously close a file.

        Args:
            file: The file to be closed.

        Raises:
            IOError: If the file cannot be closed.

        """
        try:
            await file.close()
        except Exception as e:
            self.logger.error(f"Failed to close file: {e}")
            raise IOError(f"Failed to close file: {e}")

    async def copy(self, source, destination, overwrite=False):
        """
        Asynchronously copy a file.

        Args:
            source (str): The path to the source file.
            destination (str): The path to the destination file.
            overwrite (bool, optional): If True, overwrite the destination file if it already exists.

        Raises:
            IOError: If the source file cannot be copied or if the destination file already exists and `overwrite` is False.

        """
        if os.path.exists(destination) and not overwrite:
            self.logger.error(f"Destination file {destination} already exists and overwrite is set to False.")
            raise IOError(f"Destination file {destination} already exists and overwrite is set to False.")
        try:
            await asyncio.to_thread(shutil.copy2, source, destination)
        except IOError as e:
            self.logger.error(f"Failed to copy {source} to {destination}: {e}")
            raise e

    async def move(self, source, destination, overwrite=False):
        """
        Asynchronously move or rename a file.

        Args:
            source (str): The path to the source file.
            destination (str): The path to the destination file.
            overwrite (bool, optional): If True, overwrite the destination file if it already exists.

        Raises:
            IOError: If the source file cannot be moved or if the destination file already exists and `overwrite` is False.

        """
        if os.path.exists(destination) and not overwrite:
            self.logger.error(f"Destination file {destination} already exists and overwrite is set to False.")
            raise IOError(f"Destination file {destination} already exists and overwrite is set to False.")
        try:
            await asyncio.to_thread(shutil.move, source, destination)
        except IOError as e:
            self.logger.error(f"Failed to move {source} to {destination}: {e}")
            raise e

    async def remove(self, file_path):
        """
        Asynchronously remove a file.

        Args:
            file_path (str): The path to the file to be removed.

        Raises:
            IOError: If the file cannot be removed.

        """
        try:
            await asyncio.to_thread(os.remove, file_path)
        except OSError as e:
            self.logger.error(f"Failed to remove {file_path}: {e}")
            raise IOError(f"Failed to remove {file_path}: {e}")

    async def listdir(self, directory):
        """
        Asynchronously list the contents of a directory.

        Args:
            directory (str): The path to the directory to be listed.

        Returns:
            list: A list of file and directory names in the specified directory.

        Raises:
            IOError: If the directory cannot be listed.

        """
        try:
            return await asyncio.to_thread(os.listdir, directory)
        except OSError as e:
            self.logger.error(f"Failed to list directory {directory}: {e}")
            raise IOError(f"Failed to list directory {directory}: {e}")

    async def get_file_info(self, file_path):
        """
        Asynchronously retrieve file information.

        Args:
            file_path (str): The path to the file.

        Returns:
            dict: A dictionary containing file information including size, permissions, is_directory, and last_modified.

        Raises:
            IOError: If file information cannot be retrieved.

        """
        try:
            file_stat = await asyncio.to_thread(os.stat, file_path)
            return {
                'size': file_stat[stat.ST_SIZE],
                'permissions': oct(file_stat[stat.ST_MODE] & 0o777),
                'is_directory': os.path.isdir(file_path),
                'last_modified': file_stat[stat.ST_MTIME]
            }
        except OSError as e:
            self.logger.error(f"Failed to retrieve file info for {file_path}: {e}")
            raise IOError(f"Failed to retrieve file info for {file_path}: {e}")

    async def change_permissions(self, file_path, permissions):
        """
        Asynchronously change the permissions of a file.

        Args:
            file_path (str): The path to the file.
            permissions (str): The new permissions in octal format (e.g., '0755').

        Raises:
            IOError: If the permissions cannot be changed.

        """
        try:
            await asyncio.to_thread(os.chmod, file_path, int(permissions, 8))
        except OSError as e:
            self.logger.error(f"Failed to change permissions for {file_path}: {e}")
            raise IOError(f"Failed to change permissions for {file_path}: {e}")

    async def create_directory(self, directory_path):
        """
        Asynchronously create a directory.

        Args:
            directory_path (str): The path to the directory to be created.

        Raises:
            IOError: If the directory cannot be created.

        """
        try:
            await asyncio.to_thread(os.makedirs, directory_path, exist_ok=True)
        except OSError as e:
            self.logger.error(f"Failed to create directory {directory_path}: {e}")
            raise IOError(f"Failed to create directory {directory_path}: {e}")

    async def rename(self, old_path, new_path, overwrite=False):
        """
        Asynchronously rename or move a file or directory.

        Args:
            old_path (str): The path to the old file or directory.
            new_path (str): The path to the new file or directory.
            overwrite (bool, optional): If True, overwrite the destination if it already exists.

        Raises:
            IOError: If the file or directory cannot be renamed.

        """
        if os.path.exists(new_path) and not overwrite:
            self.logger.error(f"Destination {new_path} already exists and overwrite is set to False.")
            raise IOError(f"Destination {new_path} already exists and overwrite is set to False.")
        try:
            await asyncio.to_thread(os.rename, old_path, new_path)
        except OSError as e:
            self.logger.error(f"Failed to rename {old_path} to {new_path}: {e}")
            raise IOError(f"Failed to rename {old_path} to {new_path}: {e}")

    async def is_file(self, file_path):
        """
        Asynchronously check if a path points to a file.

        Args:
            file_path (str): The path to check.

        Returns:
            bool: True if the path points to a file, False otherwise.

        Raises:
            IOError: If the check fails.

        """
        try:
            return await asyncio.to_thread(os.path.isfile, file_path)
        except OSError as e:
            self.logger.error(f"Failed to check if {file_path} is a file: {e}")
            raise IOError(f"Failed to check if {file_path} is a file: {e}")

    async def is_directory(self, dir_path):
        """
        Asynchronously check if a path points to a directory.

        Args:
            dir_path (str): The path to check.

        Returns:
            bool: True if the path points to a directory, False otherwise.

        Raises:
            IOError: If the check fails.

        """
        try:
            return await asyncio.to_thread(os.path.isdir, dir_path)
        except OSError as e:
            self.logger.error(f"Failed to check if {dir_path} is a directory: {e}")
            raise IOError(f"Failed to check if {dir_path} is a directory: {e}")

    async def listdir_recursive(self, directory):
        """
        Asynchronously list the contents of a directory recursively.

        Args:
            directory (str): The path to the directory to be listed.

        Yields:
            Tuple[str, list, list]: A tuple containing the directory path, list of subdirectories, and list of files in that directory.

        Raises:
            IOError: If the directory cannot be listed.

        """
        async def async_scandir(directory):
            with os.scandir(directory) as entries:
                for entry in entries:
                    yield entry

        async for entry in async_scandir(directory):
            if entry.is_dir():
                async for root, dirs, files in self.listdir_recursive(entry.path):
                    yield root, dirs, files
            elif entry.is_file():
                yield directory, [], [entry.name]

    @asynccontextmanager
    async def lock(self, file_path, mode='w', timeout=None):
        """
        Asynchronously acquire and release a file lock.

        Args:
            file_path (str): The path to the file to be locked.
            mode (str, optional): The mode in which the file should be opened during locking.
            timeout (float, optional): The maximum time to wait for the lock.

        Yields:
            file: A file object representing the locked file.

        Raises:
            IOError: If the lock cannot be acquired or released.

        """
        lock_file_path = f"{file_path}.lock"
        await self.write(lock_file_path, "")
        lock_file = None
        try:
            lock_file = open(lock_file_path, mode)
            yield lock_file
        except IOError as e:
            self.logger.error(f"Failed to acquire lock for {file_path}: {e}")
            raise e
        finally:
            if lock_file:
                lock_file.close()
            await self.remove(lock_file_path)

    async def read_json(self, file_path, default=None):
        """
        Asynchronously read and parse JSON data from a file.

        Args:
            file_path (str): The path to the JSON file to be read.
            default: The default value to return if the file cannot be read or parsed.

        Returns:
            dict: The parsed JSON data, or the default value if parsing fails.

        """
        try:
            content = await self.read(file_path)
            return json.loads(content) if content else default
        except (IOError, json.JSONDecodeError):
            return default

    async def write_json(self, file_path, data):
        """
        Asynchronously write data as JSON to a file.

        Args:
            file_path (str): The path to the file where JSON data will be written.
            data: The data to be written as JSON.

        Raises:
            IOError: If the file cannot be opened or JSON data cannot be written.

        """
        try:
            json_data = json.dumps(data, indent=4)
            await self.write(file_path, json_data)
        except (IOError, json.JSONDecodeError) as e:
            self.logger.error(f"Failed to write JSON data to {file_path}: {e}")
            raise e

    @asynccontextmanager
    async def temp_file(self, mode='w+b', buffering=-1, encoding=None, errors=None, newline=None):
        """
        Asynchronously create and manage a temporary file.

        Args:
            mode (str, optional): The mode in which the temporary file should be opened.
            buffering (int, optional): The buffering policy to use.
            encoding (str, optional): The character encoding to use.
            errors (str, optional): How encoding and decoding errors are to be handled.
            newline (str, optional): How newlines are handled when reading and writing the temporary file.

        Yields:
            file: A file object representing the temporary file.

        Raises:
            IOError: If the temporary file cannot be created or managed.

        """
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, next(tempfile._get_candidate_names()))

        try:
            # Create a temporary file synchronously
            with open(temp_file_path, mode) as temp_file:
                yield temp_file
        except IOError as e:
            self.logger.error(f"Failed to create temporary file {temp_file_path}: {e}")
            raise e
        finally:
            # Remove the temporary file after closing it
            await self.remove(temp_file_path)

    async def file_type(self, file_path):
        """
        Asynchronously determine the type of a file (text or binary).

        Args:
            file_path (str): The path to the file to be checked.

        Returns:
            str: The file type, either 'text' or 'binary'.

        Raises:
            IOError: If the file type cannot be determined.

        """
        try:
            is_text = await asyncio.to_thread(self.is_text_file, file_path)
            return 'text' if is_text else 'binary'
        except IOError as e:
            self.logger.error(f"Failed to determine file type of {file_path}: {e}")
            raise e

    def is_text_file(self, file):
        """
        Determine if a file is a text file.

        Args:
            file: The file to be checked.

        Returns:
            bool: True if the file is a text file, False otherwise.

        """
        try:
            # Check if the file is binary by reading the first 1024 bytes
            data = file.read(1024)
            is_binary = b'\x00' in data
            file.seek(0)  # Reset file pointer
            return not is_binary
        except Exception:
            return False

    async def calculate_checksum(self, file_path, algorithm='md5'):
        """
        Asynchronously calculate the checksum of a file.

        Args:
            file_path (str): The path to the file for which the checksum will be calculated.
            algorithm (str, optional): The checksum algorithm to use (e.g., 'md5', 'sha1', 'sha256').

        Returns:
            str: The hexadecimal checksum of the file.

        Raises:
            IOError: If the checksum cannot be calculated.

        """
        try:
            with open(file_path, 'rb') as file:
                hasher = hashlib.new(algorithm)
                while True:
                    data = file.read(65536)
                    if not data:
                        break
                    hasher.update(data)
                return hasher.hexdigest()
        except IOError as e:
            self.logger.error(f"Failed to calculate checksum for {file_path}: {e}")
            raise e

    async def compare_files(self, file_path1, file_path2):
        """
        Asynchronously compare the contents of two files using the unified diff format.

        Args:
            file_path1 (str): The path to the first file for comparison.
            file_path2 (str): The path to the second file for comparison.

        Returns:
            list: A list of strings representing the differences between the files in unified diff format.

        Raises:
            IOError: If the files cannot be compared.

        """
        try:
            async with await self.open(file_path1, 'rb') as file1, await self.open(file_path2, 'rb') as file2:
                differ = difflib.Differ()
                lines1 = await asyncio.to_thread(file1.readlines)
                lines2 = await asyncio.to_thread(file2.readlines)
                return list(differ.compare(lines1, lines2))
        except IOError as e:
            self.logger.error(f"Failed to compare files {file_path1} and {file_path2}: {e}")
            raise e

    async def copy_files(self, source_files, destination_directory, overwrite=False):
        """
        Copy a list of files to a destination directory.

        Args:
            source_files (list of str): List of source file paths to copy.
            destination_directory (str): Destination directory path.
            overwrite (bool, optional): Whether to overwrite existing files in the destination directory.

        Raises:
            IOError: If any of the source files cannot be copied or the destination directory cannot be created.

        Returns:
            list of str: List of paths to the copied files in the destination directory.
        """
        copied_files = []
        try:
            await self.create_directory(destination_directory)
            for source_file in source_files:
                file_name = os.path.basename(source_file)
                destination_file = os.path.join(destination_directory, file_name)
                await self.copy(source_file, destination_file, overwrite)
                copied_files.append(destination_file)
        except IOError as e:
            self.logger.error(f"Failed to copy files to {destination_directory}: {e}")
            raise e
        return copied_files

    async def move_files(self, source_files, destination_directory, overwrite=False):
        """
        Move a list of files to a destination directory.

        Args:
            source_files (list of str): List of source file paths to move.
            destination_directory (str): Destination directory path.
            overwrite (bool, optional): Whether to overwrite existing files in the destination directory.

        Raises:
            IOError: If any of the source files cannot be moved or the destination directory cannot be created.

        Returns:
            list of str: List of paths to the moved files in the destination directory.
        """
        moved_files = []
        try:
            await self.create_directory(destination_directory)
            for source_file in source_files:
                file_name = os.path.basename(source_file)
                destination_file = os.path.join(destination_directory, file_name)
                await self.move(source_file, destination_file, overwrite)
                moved_files.append(destination_file)
        except IOError as e:
            self.logger.error(f"Failed to move files to {destination_directory}: {e}")
            raise e
        return moved_files

    async def delete_directory_recursive(self, directory_path):
        """
        Recursively delete a directory and its contents.

        Args:
            directory_path (str): Directory path to delete.

        Raises:
            IOError: If the directory and its contents cannot be deleted.

        Returns:
            None
        """
        try:
            await asyncio.to_thread(shutil.rmtree, directory_path)
        except IOError as e:
            self.logger.error(f"Failed to delete directory {directory_path}: {e}")
            raise e
        
    async def create_symlink(self, source_file, symlink_path):
        """
        Create a symbolic link (symlink) to a file.

        Args:
            source_file (str): Source file path.
            symlink_path (str): Path for the symbolic link to be created.

        Raises:
            IOError: If the symbolic link cannot be created.

        Returns:
            None
        """
        try:
            await asyncio.to_thread(os.symlink, source_file, symlink_path)
        except IOError as e:
            self.logger.error(f"Failed to create symlink from {source_file} to {symlink_path}: {e}")
            raise e

    async def read_lines_chunked(self, file_path, chunk_size=1024):
        """
        Read lines from a file in chunks.

        Args:
            file_path (str): File path to read lines from.
            chunk_size (int, optional): Size of each read chunk.

        Yields:
            str: Lines read from the file.

        Raises:
            IOError: If the file cannot be opened or read.
        """
        try:
            async with await self.open(file_path, 'r') as file:
                while True:
                    chunk = await self.loop.run_in_executor(None, file.read, chunk_size)
                    if not chunk:
                        break
                    lines = chunk.splitlines()
                    for line in lines:
                        yield line
        except IOError as e:
            self.logger.error(f"Failed to read lines from {file_path}: {e}")
            raise e

    async def search_in_file(self, file_path, search_text):
        """
        Search for a specific text in a file and return the matching lines.

        Args:
            file_path (str): File path to search in.
            search_text (str): Text to search for.

        Returns:
            list of str: Lines containing the search text.

        Raises:
            IOError: If the file cannot be opened or read.
        """
        matching_lines = []
        try:
            async for line in self.read_lines(file_path):
                if search_text in line:
                    matching_lines.append(line)
        except IOError as e:
            self.logger.error(f"Failed to search in {file_path}: {e}")
            raise e
        return matching_lines

    async def count_lines(self, file_path):
        """
        Count the number of lines in a file.

        Args:
            file_path (str): File path to count lines in.

        Returns:
            int: Number of lines in the file.

        Raises:
            IOError: If the file cannot be opened or read.
        """
        line_count = 0
        try:
            async for _ in self.read_lines(file_path):
                line_count += 1
        except IOError as e:
            self.logger.error(f"Failed to count lines in {file_path}: {e}")
            raise e
        return line_count
    
    async def hash_file(self, file_path: str, algorithm: str = 'sha256') -> str:
        """
        Asynchronously calculate the hash of a file using a specified algorithm.

        Args:
            file_path (str): The path to the file to be hashed.
            algorithm (str, optional): The hash algorithm to use (e.g., 'md5', 'sha1', 'sha256').

        Returns:
            str: The hexadecimal representation of the file's hash.

        Raises:
            IOError: If the file cannot be read or the hash cannot be calculated.

        """
        try:
            hasher = hashlib.new(algorithm)
            with await self.open(file_path, 'rb') as file:
                while True:
                    data = await self.loop.run_in_executor(None, file.read, 4096)
                    if not data:
                        break
                    hasher.update(data)
            return hasher.hexdigest()
        except Exception as e:
            self.logger.error(f"Failed to hash {file_path} using {algorithm}: {e}")
            raise IOError(f"Failed to hash {file_path} using {algorithm}: {e}")

    async def diff_files(self, file1_path: str, file2_path: str) -> List[str]:
        """
        Asynchronously compute the differences between two text files.

        Args:
            file1_path (str): The path to the first text file.
            file2_path (str): The path to the second text file.

        Returns:
            list: A list of strings representing the differences between the files.

        Raises:
            IOError: If the files cannot be read or the differences cannot be computed.

        """
        try:
            file1_content = await self.read_lines(file1_path)
            file2_content = await self.read_lines(file2_path)

            differ = difflib.Differ()
            diff = list(differ.compare(file1_content, file2_content))

            return diff
        except Exception as e:
            self.logger.error(f"Failed to compute differences between {file1_path} and {file2_path}: {e}")
            raise IOError(f"Failed to compute differences between {file1_path} and {file2_path}: {e}")

