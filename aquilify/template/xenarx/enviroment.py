from typing import List, Type
from aquilify.template.xenarx import nodes, errors

class Environment:
    """Class representing the environment for Xenarx Template Engine."""

    def __init__(self, extensions: List[Type] = []) -> None:
        """
        Initialize the environment with a list of extensions.

        Args:
            extensions (List[Type]): List of extensions to register in the environment.
        """
        self.extensions: List[Type] = extensions

    def _build_extension(self) -> None:
        """
        Build extensions by registering nodes in the Xenarx Template Engine.
        
        Raises:
            errors.XenarxEngineError: If a valid node key is not present in the extension.
        """
        for extension in self.extensions:
            nodekey = getattr(extension, '__nodekeyword__', None)
            if not nodekey:
                raise errors.XenarxEngineError(
                    """A valid node key is required to register a Node 
                    in Xenarx Template Engine. You can define your node keyword 
                    by adding `__nodekeyword__` in your node class."""
                )

            nodendword = getattr(extension, '__node_endword__', None)
            nodes.register(nodekey, nodendword, extension)
