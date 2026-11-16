from __future__ import annotations

from typing import Any

from .base import AssetMetaData, FilesystemContext
from ..env import UNREAL_AVAILABLE

if UNREAL_AVAILABLE:
    import unreal

class UnrealContext(FilesystemContext):

    def __init__(self, asset_path: str ="/Game/") -> None:
        # If Unreal is not available, preserve the original behavior and
        # raise here so callers know this context requires the Editor.
        if not UNREAL_AVAILABLE:
            raise ImportError(
                "Unreal Context requires Unreal Editor to be running"
                "\nUse the FilesystemContext for non-Unreal environments"
            )

        # Store the requested asset path for use when running inside the Editor.
        self.asset_path = asset_path
        
    def get_assets(self) -> list[AssetMetaData]:
        # If running inside Unreal Editor, list assets via the Editor API.
        # Otherwise return an empty list (no-op) so callers can decide
        # whether to fall back to disk-based scanning.
        results: list[AssetMetaData] = []
        if not UNREAL_AVAILABLE:
            return results

        asset_paths = unreal.EditorAssetLibrary.list_assets(self.asset_path, recursive=True)
        for ap in asset_paths:
            meta = self._build_metadata_from_path(ap)
            if meta is not None:
                results.append(meta)
        return results
    
    def get_asset_metadata(self, path: str) -> AssetMetaData|None:

        return self._build_metadata_from_path(path)
    
    def load_uobject(self, path: str) -> Any:
        try:
            return unreal.EditorAssetLibrary.load_asset(path)
        except Exception:
            return None
    
    def _build_metadata_from_path(self, ap: str) -> AssetMetaData|None:
        try:
            data=unreal.EditorAssetLibrary.find_asset_data(ap)
        except Exception:
            return None
        
        if not data.is_valid():
            return None
        
        asset_class: str = str(data.asset_class_path.asset_name)
        asset_name: str = str(data.asset_name)

        return AssetMetaData(
            path=ap,
            name=asset_name,
            extension=".uasset",
            size_bytes=0,
            asset_class=asset_class,
            extra={"asset_data": data}
        )
    
    def __repr__(self) -> str:
        return f"UnrealContext asset_path={self.asset_path!r}"

