from __future__ import annotations

from typing import TYPE_CHECKING

try:
    import unreal

    UNREAL_VERSION: str | None = (
        unreal.SystemLibrary.get_engine_version()[:5]
    )
    UNREAL_AVAILABLE: bool = True
except:
    unreal=None
    UNREAL_VERSION:str |None=None
    UNREAL_AVAILABLE: bool = False

if TYPE_CHECKING:
    import unreal


ASSET_CLASS_STATIC_MESH="StaticMesh"
ASSET_CLASS_TEXTURE_2D="Texture2D"
ASSET_CLASS_MATERIAL="Material"
ASSET_CLASS_NIAGARA="NiagaraSystem"
ASSET_CLASS_SKELETON="Skeleton"
ASSET_CLASS_ANIM="AnimSequence"

def get_content_dir()->str|None:
    if not UNREAL_AVAILABLE:
        return None
    return unreal.Paths.project_content_dir()


def get_project_dir() -> str | None:

    if not UNREAL_AVAILABLE:
        return None
    return unreal.Paths.project_dir()

def get_selected_assets()->list:
    if not UNREAL_AVAILABLE:
        return []
    return list(unreal.EditorUtilityLibrary.get_selected_assets())

def is_editor()->bool:
    if not UNREAL_AVAILABLE:
        return False
    return unreal.is_editor()

def log_env_status()->None:
    if not UNREAL_AVAILABLE:
        return False
    return 

