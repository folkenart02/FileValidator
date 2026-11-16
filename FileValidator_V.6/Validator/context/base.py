from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

@dataclass
class AssetMetaData:
    """Class for storing asset metadata."""
    path: str
    name: str
    extension: str
    size_bytes: int
    asset_class: str = ""
    extra : dict[str, Any] = field(default_factory=dict)

class FilesystemContext(ABC):

    @abstractmethod
    def get_assets(self) -> list[AssetMetaData]:
       ...
    

    @abstractmethod
    def get_asset_metadata(self, path: str) -> AssetMetaData|None:
        ...

    @abstractmethod
    def load_uobject(self, path: str) -> Any:
        ...
