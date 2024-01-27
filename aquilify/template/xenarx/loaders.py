import os

from .template import Template
from .errors import TemplateLoadError


# Loads templates from the file system. Assumes files are utf-8 encoded. Compiled templates are
# cached in memory, so they only need to be compiled once. Templates are *not* automatically
# recompiled if the underlying template file changes.
#
# A FileLoader instance should be initialized with a path to a base template directory:
#
#     loader = FileLoader('/path/to/base/dir')
#
# Multiple base directories can be specified:
#
#     loader = FileLoader('/path/to/base/dir1', '/path/to/base/dir2')
#
# The loader instance can then be called with a filename string. The loader will return the
# template object corresponding the template file or raise a TemplateLoadError if no file can
# be located. Note that the filename string may include subdirectory paths:
#
#     template = loader('foo.txt')
#     template = loader('subdir/foo.txt')
#
class FileLoader:

    def __init__(self, *base_dirs):
        self.base_dirs = base_dirs
        self.cache = {}

    def __call__(self, filename):
        if filename in self.cache:
            return self.cache[filename]

        paths = [os.path.join(base_dir, filename) for base_dir in self.base_dirs]
    
        for path in paths:
            if os.path.isfile(path):
                try:
                    with open(path, encoding='utf-8') as file:
                        template_string = file.read()
                except OSError as err:
                    msg = f"FileLoader cannot load the template file '{path}'."
                    raise TemplateLoadError(msg) from err

                template = Template(template_string, filename)
                self.cache[filename] = template
                return template

        msg = f"FileLoader cannot locate the template file '{filename}'."
        raise TemplateLoadError(msg)


# Like FileLoader but templates are automatically recompiled if the underlying template file
# is modified.
class FileReloader:

    def __init__(self, *base_dirs):
        self.base_dirs = base_dirs
        self.cache = {}

    def __call__(self, filename):
        paths = [os.path.join(dirs, filename) for base_dir in self.base_dirs for dirs in base_dir]
        
        for path in paths:
            if os.path.isfile(path):
                mtime = os.path.getmtime(path)

                if filename in self.cache and mtime == self.cache[filename][0]:
                    return self.cache[filename][1]

                try:
                    with open(path, encoding='utf-8') as file:
                        template_string = file.read()
                except OSError as err:
                    msg = f"FileReloader cannot load the template file '{path}'."
                    raise TemplateLoadError(msg) from err

                template = Template(template_string, filename)
                self.cache[filename] = (mtime, template)
                return template

        msg = f"FileReloader cannot locate the template file '{filename}'."
        raise TemplateLoadError(msg)


# Loads templates from a dictionary of template strings. Templates are compiled once and cached for
# future use.
class DictLoader:

    def __init__(self, template_strings):
        self.templates = {}
        self.template_strings = template_strings

    def __call__(self, name):
        if name in self.templates:
            return self.templates[name]
        elif name in self.template_strings:
            template = Template(self.template_strings[name], name)
            self.templates[name] = template
            return template
        msg = f"DictLoader has no entry matching the template name '{name}'."
        raise TemplateLoadError(msg)