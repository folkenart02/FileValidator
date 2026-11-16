import re
from .base import AbstractRule, Severity, Validation
import os
from ..registry import registry

@registry.register
class NamingRule(AbstractRule):
    name = "Naming"
    category = "Naming"
    severity = Severity.WARNING


    def validate(self, asset_path: str) -> Validation:
        filename=os.path.basename(asset_path)
        stem, ext=os.path.splitext(filename)
        ext_lower=ext.lower()

        pattern:str=self.config.get("naming_patterns")
        if not re.fullmatch(pattern,stem):
            return self._make_result(
                asset_path,
                passed=False,
                message=(
                        f"Stem {stem} does not match naming {pattern}. "
                        "Expected PascalCase with optional underscores. "
                        "Example: CHM_MainCharacter"
                    ),
            )
        
        max_len=self.config.get("max_filename_length")

        if len(filename)>max_len:
            return self._make_result(
                asset_path,
                passed=False,
                message=f"Filename {filename} size exceeds max filename length {max_len}",
            )
        
        return self._make_result(
            asset_path,
            passed=True,
            message=f"Filename {filename} size is within max filename length"
        )
            