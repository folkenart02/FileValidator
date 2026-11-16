from __future__ import annotations

from ..registry import registry
from .base import AbstractRule, Validation, Severity
from ..env import UNREAL_AVAILABLE, ASSET_CLASS_STATIC_MESH


if UNREAL_AVAILABLE:
    import unreal

def _load_static_mesh(asset_path: str):
    """Load a StaticMesh asset from the given path."""
    try:
        # Assume the provided asset_path is already the Unreal virtual path
        # (e.g. "/Game/..."). Do not attempt to convert disk paths here; the
        # `UnrealContext` adapter is responsible for mapping disk paths to
        # virtual /Game/ paths when necessary.
        obj = unreal.EditorAssetLibrary.load_asset(asset_path)
        
    except Exception:
        unreal.log_warning(f"[Validator] Warning: Could not load asset at {asset_path}. It may not be a valid StaticMesh.")
        return None
    
    if obj is None:
        return None
    
    if not isinstance(obj, unreal.StaticMesh):
        unreal.log_warning(f"[Validator] Warning: Asset at {asset_path} is not a StaticMesh.")
        return None
    unreal.log(f"[Validator] Loaded StaticMesh asset at {asset_path}.")
    return obj

@registry.register
class PolygonCountRule(AbstractRule):
    name= "Polygon Count" 
    category = "StaticMesh"
    severity = Severity.WARNING

    def validate(self, asset_path: str) -> Validation:
        if not UNREAL_AVAILABLE:
            return self._make_skipped(asset_path, "Unreal Engine is not available.")
        
        env_prefixes = tuple(self.config.get("env.prefixes", {}).keys())
        chr_prefixes = tuple(self.config.get("chr.prefixes", {}).keys())

        # Safely load mesh utilizing your newly-patched _load_static_mesh function!
        mesh = _load_static_mesh(asset_path)
        # Prefer the mesh object's reported name when available; fallback to
        # the asset path's trailing name if necessary. Naming/prefix logic
        # and path-to-/Game/ translation should be handled by `UnrealContext`.
        mesh_name = None
        if mesh is not None:
            try:
                mesh_name = mesh.get_name()
            except Exception:
                try:
                    mesh_name = mesh.get_fname()
                except Exception:
                    mesh_name = None
        if not mesh_name:
            mesh_name = (asset_path.replace("\\", "/").split("/")[-1].replace(".uasset", ""))

        if mesh is None:
            return self._make_skipped(
                asset_path, 
                f"Asset at {asset_path} is not a valid {ASSET_CLASS_STATIC_MESH} or could not be loaded.", 
                severity=Severity.INFO
            )
        
        triangle_count = 0
        
        if hasattr(mesh, "get_num_source_models") and mesh.get_num_source_models() > 0:
            source_model = mesh.get_source_model(0)
            if source_model:
                mesh_desc = source_model.get_mesh_description()
                if mesh_desc:
                    triangle_count = mesh_desc.get_triangle_count()

        if triangle_count == 0 and hasattr(mesh, "get_num_triangles") and mesh.get_num_lods() > 0:
            triangle_count = mesh.get_num_triangles(0)

        max_allowed_triangles_chr = self.config.get("max_allowed_triangles.chr", 10000)
        max_allowed_triangles_env = self.config.get("max_allowed_triangles.env", 5000)

        if mesh_name.startswith(env_prefixes):
            if triangle_count > max_allowed_triangles_env:
                return self._make_result(
                    asset_path,
                    passed=False,
                    message=f"StaticMesh '{mesh_name}' has {triangle_count} source triangles, which exceeds the limit of {max_allowed_triangles_env} for environment meshes."
                )
            return self._make_result(
                asset_path,
                passed=True,
                message=f"StaticMesh '{mesh_name}' has {triangle_count} source triangles, which is within the limit of {max_allowed_triangles_env} for environment meshes."
            )
        
        if mesh_name.startswith(chr_prefixes):
            if triangle_count > max_allowed_triangles_chr:
                return self._make_result(
                    asset_path,
                    passed=False,
                    message=f"StaticMesh '{mesh_name}' has {triangle_count} source triangles, which exceeds the limit of {max_allowed_triangles_chr} for character meshes."
                )
            return self._make_result(
                asset_path,
                passed=True,
                message=f"StaticMesh '{mesh_name}' has {triangle_count} source triangles, which is within the limit of {max_allowed_triangles_chr} for character meshes."
            )
        
        return self._make_skipped(
            asset_path,
            reason=f"StaticMesh '{mesh_name}' does not match any known prefix pattern (env or chr).",
            severity=Severity.INFO
        )
            
@registry.register
class MaterialCountRule(AbstractRule):

    name= "Material Count" 
    category = "StaticMesh"
    severity = Severity.WARNING

    def validate(self, asset_path: str) -> Validation:
        """Get the number of materials assigned to the StaticMesh."""
        if not UNREAL_AVAILABLE:
            return self._make_skipped(asset_path, "Unreal Engine is not available.")
        
        mesh = _load_static_mesh(asset_path)
        mesh_name = None
        if mesh is not None:
            try:
                mesh_name = mesh.get_name()
            except Exception:
                try:
                    mesh_name = mesh.get_fname()
                except Exception:
                    mesh_name = None
        if not mesh_name:
            mesh_name = (asset_path.replace("\\", "/").split("/")[-1].replace(".uasset", ""))
        env_prefixes = tuple(self.config.get("env.prefixes", {}).keys())
        chr_prefixes = tuple(self.config.get("chr.prefixes", {}).keys())
        max_chr_materials = self.config.get("max_materials.chr", 4)
        max_env_materials = self.config.get("max_materials.env", 3)

        if mesh is None:
            return self._make_skipped(asset_path, f"Asset at {asset_path} is not a valid {ASSET_CLASS_STATIC_MESH} or could not be loaded.", severity=Severity.INFO)

        mesh_mtls = len([m.material_slot_name for m in mesh.static_materials])
        
        if mesh_name.startswith(env_prefixes):
            if mesh_mtls > max_env_materials:
                return self._make_result(
                    asset_path,
                    passed=False,
                    message=f"StaticMesh '{mesh_name}' has {mesh_mtls} materials, which exceeds the limit of {max_env_materials} for environment meshes."
                )
            return self._make_result(
                asset_path,
                passed=True,
                message=f"StaticMesh '{mesh_name}' has {mesh_mtls} materials, which is within the limit of {max_env_materials} for environment meshes."
            )
        
        if mesh_name.startswith(chr_prefixes):
            if mesh_mtls > max_chr_materials:
                return self._make_result(
                    asset_path,
                    passed=False,
                    message=f"StaticMesh '{mesh_name}' has {mesh_mtls} materials, which exceeds the limit of {max_chr_materials} for character meshes."
                )
            return self._make_result(
                asset_path,
                passed=True,
                message=f"StaticMesh '{mesh_name}' has {mesh_mtls} materials, which is within the limit of {max_chr_materials} for character meshes."
            )
        
        return self._make_skipped(
            asset_path,
            reason=f"StaticMesh '{mesh_name}' does not match any known prefix pattern (env or chr).",
            severity=Severity.INFO
        )
        
        

        
