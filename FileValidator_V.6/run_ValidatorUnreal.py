from __future__ import annotations

import sys
from pathlib import Path

_STEP_DIR = Path(__file__).resolve().parent
if str(_STEP_DIR) not in sys.path:
    sys.path.insert(0, str(_STEP_DIR))


for _k in [k for k in sys.modules if k=="validator" or k.lower().startswith("validator")]:
    del sys.modules[_k]

from Validator.env import UNREAL_AVAILABLE

if not UNREAL_AVAILABLE:
    raise RuntimeError(
        "run_ValidatorUnreal.py must be run from inside Unreal Editor .\n"
        "For standalone / filesystem validation use run_Validator.py"
    )

import unreal

from Validator.config import Config
from Validator.runner import ValidationRunner
from Validator.Rules.base import Severity
from Validator.context.unreal import UnrealContext

# Use the project's Content/Global folder as the default context root
CONTENT_PATH = "/Game/Global"

unreal.log(f"[Validator] Starting validation on (virtual): {CONTENT_PATH}")

config = Config(path=None)
runner = ValidationRunner(config)

if not runner.rules:
    unreal.log_warning("[Validator] No rules matched.  Check validator/rules/ folder")
else:
    unreal.log(f"[Validator] Rules active: {[type(r).__name__ for r in runner.rules]}")

# Instantiate the UnrealContext adapter and run context-based validation.
ctx = UnrealContext(asset_path=CONTENT_PATH)
unreal.log(f"[Validator] UnrealContext created for: {ctx.asset_path}")

# Debug: check what assets the context found
assets = ctx.get_assets()
unreal.log(f"[Validator] Found {len(assets)} assets in context")
if assets:
    unreal.log(f"[Validator] First asset: {assets[0].name} ({assets[0].asset_class})")

results = runner.validate_context(ctx)
unreal.log(f"[Validator] Validation complete: {len(results)} results")

for result in results:
    if not result.passed:
        unreal.log_error(str(result))

runner.Summary(results)
validator_dir = str(_STEP_DIR)
json_output_path = runner.json_parser(results, output_path=Path(validator_dir) / "ValidationResults.json")
unreal.log(f"[Validator] JSON results saved to: {json_output_path}")

error_count = sum(1 for r in results if not r.passed and r.severity is Severity.ERROR)
if error_count:
    unreal.log_error(f"[Validator] {error_count} ERROR(s) found. See Output Log for details.")
else:
    unreal.log("[Validator] Validation complete - no errors found.")

