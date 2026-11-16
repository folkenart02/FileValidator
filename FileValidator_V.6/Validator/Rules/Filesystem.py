from .base import AbstractRule, Severity, Validation
import os
from ..registry import registry


@registry.register
class Filesizing(AbstractRule):
    name = "FileSize"
    category = "FileSystem"
    severity = Severity.ERROR

    def validate(self, asset_path: str) -> Validation:

        if not os.path.isfile(asset_path):
            return self._make_result(
                asset_path,
                passed=False,
                message=(
                    f"File does not exist or is not a regular file: '{asset_path}'"
                    F"Cannot determine file size"
                ),
            )
        max_chrMB=self.config.get("chr.Max_filesizeMB")
        max_envMB=self.config.get("env.Max_filesizeMB")
        
        size_bytes= os.path.getsize(asset_path)
        size_mb=size_bytes/(1024*1024)

        filename = os.path.basename(asset_path)
        env_prefixes = tuple(self.config.get("env.prefixes", {}).keys())
        chr_prefixes = tuple(self.config.get("chr.prefixes", {}).keys())
        is_env_file = filename.startswith(env_prefixes)
        is_chr_file = filename.startswith(chr_prefixes)
        asset_type_filter = getattr(self, "asset_type", None)

        if not is_env_file and not is_chr_file:
            return self._make_skipped(
                asset_path,
                severity=Severity.WARNING,
                reason=(
                    f"File size validation skipped: prefix unrecognized "
                    f"for '{filename}'"
                ),
            )
        
        #ENV logic
        if is_env_file and asset_type_filter != "chr":
            if size_mb > max_envMB:
                return self._make_result(
                    asset_path,
                    passed=False,
                    message=f"File size is {size_mb:.2f}MB -- Exceeds the {max_envMB} MB limit"

                )
            
            return self._make_result(
                asset_path,
                passed=True,
                message=f"File size {size_mb:.2f} MB is within the {max_envMB} MB limit",
            )
    
        #CHR logic
        if is_chr_file and asset_type_filter != "env":
            if size_mb > max_chrMB:
                return self._make_result(
                    asset_path,
                    passed=False,
                    message=f"File size is {size_mb:.2f}MB -- Exceeds the {max_chrMB} MB limit"
                )
            
            return self._make_result(
                asset_path,
                passed=True,
                message=f"File size {size_mb:.2f} MB is within the {max_chrMB} MB limit",
            )
        

        
        

@registry.register
class ExtensionRules(AbstractRule):
    name = "Extensions"
    category = "FileSystem"
    severity = Severity.ERROR

    
    def validate(self, asset_path: str) -> Validation:
        _, ext = os.path.splitext(asset_path)
        ext_lower = ext.lower()

        env_valid_extension: dict[str] = self.config.get("env.prefixes", {})
        chr_valid_extension: dict[str] = self.config.get("chr.prefixes", {})
        bp_valid_extension: dict[str] = self.config.get("blueprint_prefixes", {})
        error_unknown_ext = self.config.get("error_unkown_ext", True)

        filename = os.path.basename(asset_path)
        env_prefixes = tuple(env_valid_extension.keys())
        chr_prefixes = tuple(chr_valid_extension.keys())
        bp_prefixes = tuple(bp_valid_extension.keys())

        is_env_file = filename.startswith(env_prefixes)
        is_chr_file = filename.startswith(chr_prefixes)
        is_bp_file = filename.startswith(bp_prefixes)
        asset_type_filter = getattr(self, "asset_type", None)

        if is_env_file and asset_type_filter != "chr":
            env_allowed_extensions = []
            prefix_key = None
            for key, allowed_extensions in env_valid_extension.items():
                if filename.startswith(key):
                    prefix_key = key
                    env_allowed_extensions = allowed_extensions
                    break

            if prefix_key is not None and ext_lower not in env_allowed_extensions:
                return self._make_result(
                    asset_path,
                    passed=False,
                    severity=Severity.ERROR if error_unknown_ext else Severity.WARNING,
                    message=(
                        f"Extension {ext_lower} is not allowed for prefix {prefix_key}. "
                        f"Allowed: {env_allowed_extensions}"
                    ),
                )

            return self._make_result(
                asset_path,
                passed=True,
                message=f"Extension {ext_lower} is allowed",
            )

        elif is_chr_file and asset_type_filter != "env":
            chr_allowed_extensions = []
            prefix_key = None
            for key, allowed_extensions in chr_valid_extension.items():
                if filename.startswith(key):
                    prefix_key = key
                    chr_allowed_extensions = allowed_extensions
                    break

            if prefix_key is not None and ext_lower not in chr_allowed_extensions:
                return self._make_result(
                    asset_path,
                    passed=False,
                    severity=Severity.ERROR if error_unknown_ext else Severity.WARNING,
                    message=(
                        f"Extension {ext_lower} is not allowed for prefix {prefix_key}. "
                        f"Allowed: {chr_allowed_extensions}"
                    ),
                )

            return self._make_result(
                asset_path,
                passed=True,
                message=f"Extension {ext_lower} is allowed",
            )
        
        elif is_bp_file:
            bp_allowed_extensions = []
            prefix_key = None
            for key, allowed_extensions in bp_valid_extension.items():
                if filename.startswith(key):
                    prefix_key = key
                    bp_allowed_extensions = allowed_extensions
                    break

            if prefix_key is not None and ext_lower not in bp_allowed_extensions:
                return self._make_result(
                    asset_path,
                    passed=False,
                    severity=Severity.ERROR if error_unknown_ext else Severity.WARNING,
                    message=(
                        f"Extension {ext_lower} is not allowed for prefix {prefix_key}. "
                        f"Allowed: {bp_allowed_extensions}"
                    ),
                )

            return self._make_result(
                asset_path,
                passed=True,
                message=f"Extension {ext_lower} is allowed",
            )

        else:
            all_valid_extensions = []
            for ext_list in list(chr_valid_extension.values()) + list(env_valid_extension.values()):
                all_valid_extensions.extend(ext_list)

            if ext_lower not in all_valid_extensions:
                return self._make_result(
                    asset_path,
                    passed=False,
                    severity=Severity.ERROR if error_unknown_ext else Severity.WARNING,
                    message=(
                        f"Extension {ext_lower} is not allowed by any configured prefix rule; "
                        "please revise filetype."
                    ),
                )

            return self._make_result(
                asset_path,
                passed=False,
                severity=Severity.WARNING,
                message=(
                    f"Extension {ext_lower} is valid, but file naming prefix is unrecognized "
                    f"for '{filename}'."
                ),
            )
        
@registry.register
class ForbiddenFolderRule(AbstractRule):
    name = "ForbiddenFolder"
    category = "FileSystem"
    severity = Severity.ERROR

    def validate(self, asset_path: str) -> Validation:
        normalized = os.path.normpath(asset_path)
        path_parts = normalized.split(os.sep)
        forbidden = [p.lower() for p in self.config.get("forbidden_folders", [])]

        for part in path_parts:
            if part.lower() in forbidden:
                return self._make_result(
                    asset_path,
                    passed=False,
                    message=f"Asset is inside forbidden folder '{part}'"
                )

        return self._make_result(
            asset_path,
            passed=True,
            message="No forbidden folder found in asset path"
        )
