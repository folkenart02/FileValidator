from __future__ import annotations

import fnmatch

from ..registry import registry
from .base import AbstractRule, Validation, Severity
from ..env import UNREAL_AVAILABLE, ASSET_CLASS_MATERIAL

if UNREAL_AVAILABLE:
    import unreal
else:
    unreal = None


def _load_material(asset_path: str):
    if not UNREAL_AVAILABLE or unreal is None:
        return None

    try:
        mat = unreal.EditorAssetLibrary.load_asset(asset_path)
    except Exception:
        return None

    if mat is None or not isinstance(mat, unreal.Material):
        return None
    return mat


@registry.register
class LargeTextures(AbstractRule):
    name = "Large texture in Material"
    category = "material"
    severity = Severity.WARNING

    def validate(self, asset_path:str)->Validation:
        if not UNREAL_AVAILABLE:
            return self._make_skipped(asset_path, "Unreal Engine is not available")
        
        mat=_load_material(asset_path)
        if mat is None:
            return self._make_skipped(asset_path, "Asset is not material or could not be loaded")
        
        if self.config.get("material_skip_engine_materials", True):
            if asset_path.startswith("/Engine/") or asset_path.startswith("Engine/"):
                return self._make_skipped(
                    asset_path,
                    "Skipping engine material assets from project content validation.",
                    severity=Severity.INFO,
                )

        textures = []
        try:
            asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
        except Exception:
            asset_registry = None
            return self._make_skipped(asset_path, f"Asset registry could not be loaded")

        # Ensure we look up the internal package path correctly
        package_path = asset_path.split(".")[0]
        dependencies = []
        if asset_registry is not None:
            try:
                dependency_options = unreal.AssetRegistryDependencyOptions()
                dependencies = asset_registry.get_dependencies(package_path, dependency_options)
            except Exception:
                dependencies = []
                return self._make_skipped(asset_path, f"Asset dependencies could not be loaded")

        max_txt_size = self.config.get("txt_size_limit", 30)
        normal_map_patterns = self.config.get(
            "material_exempt_patterns",
            ["*_N", "*_Normal", "*_normal", "*_nrm"],
        )

        def is_normal_map(texture_name: str) -> bool:
            return any(fnmatch.fnmatch(texture_name, pattern) for pattern in normal_map_patterns)

        for dep in dependencies:
            dep_str = str(dep)
            # Skip engine or plugin content if you only want to check project assets
            if dep_str.startswith("/Engine/"):
                continue

            try:
                dep_asset = unreal.EditorAssetLibrary.load_asset(dep_str)
            except Exception:
                continue

            if dep_asset and isinstance(dep_asset, unreal.Texture):
                texture_name = dep_asset.get_name() if hasattr(dep_asset, "get_name") else str(dep_asset)
                if is_normal_map(texture_name):
                    continue
                textures.append(dep_asset)
                
        # Remove duplicate references
        textures = list(set(textures))

        # 2. Calculate sizes and evaluate against limits
        total_bytes = 0
        over_budget_textures = []
        bytes_to_mb = 1024 * 1024

        for texture in textures:
            if not hasattr(texture, "blueprint_get_memory_size"):
                continue

            try:
                bytes_size = texture.blueprint_get_memory_size()
            except Exception:
                continue

            if bytes_size is None:
                continue

            mb_size = bytes_size / bytes_to_mb
            total_bytes += bytes_size

            if mb_size > max_txt_size:
                texture_name = getattr(texture, "get_name", lambda: str(texture))()
                over_budget_textures.append((texture_name, mb_size))

        if over_budget_textures:
            texture_list = ", ".join(
                f"{name} ({size:.1f} MB)" for name, size in over_budget_textures
            )
            return self._make_result(
                asset_path,
                passed=False,
                message=(
                    f"Material '{mat.get_name() if hasattr(mat, 'get_name') else str(mat)}' references "
                    f"{len(over_budget_textures)} oversized texture(s): {texture_list}. "
                    f"Limit is {max_txt_size} MB each."
                ),
            )

        return self._make_result(
            asset_path,
            passed=True,
            message=(
                f"Material '{mat.get_name() if hasattr(mat, 'get_name') else str(mat)}' has {len(textures)} texture(s) "
                f"and none exceed {max_txt_size} MB."
            ),
        )

