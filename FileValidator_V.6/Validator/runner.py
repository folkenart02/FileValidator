from __future__ import annotations
import os
import sys
from pathlib import Path
from typing import Type, Iterable
import json
from collections import defaultdict

#-------------
#Local Imports
#-------------
from .config import Config
from .Rules.base import AbstractRule, Validation, Severity
from .registry import registry
from .env import UNREAL_AVAILABLE, log_env_status
from .context import FilesystemContext

_SEVERITY_ICON: dict[Severity, str] = {
    Severity.ERROR: "χ",
    Severity.WARNING: "⚐",
    Severity.INFO: "i",
}

class ValidationRunner:

    def __init__(
    self,
    config: Config,
    category: str | None=None,
    severity: Severity | None=None,
    asset_type: str | None = None,
    rules: list[Type[AbstractRule]] | None = None,
    ) -> None:
        self.config = config
        self.asset_type=asset_type
        
        if rules is not None:
            self.rules=[R(config) for R in rules]
        else:
            registry.discover()
            rule_classes=registry.get_rules(category=category, severity=severity)
            if not rule_classes:
                print(
                    f"[ValidationRunner] Warning registry returned no rules"
                    f"(category={category!r}, severity={severity!r})"
                    f"Registered: {list(registry.list_rules().keys())}"
                )
            self.rules=[R(config) for R in rule_classes]

        for rule in self.rules:
            rule.asset_type=self.asset_type




    #PUBLIC API
    def validate_asset(self, path:str)->list[Validation]:
        return [rule.validate(path) for rule in self.rules]

    def validate_directory (self, directory:str)->list[Validation]:
        from .env import UNREAL_AVAILABLE

        log_env_status()

        asset_paths: list[str]=[]

        unreal_path = not os.path.isdir(directory) and directory.startswith("/")
        if unreal_path:
            if not UNREAL_AVAILABLE:
                raise ValueError(
                    f"{directory} is an Unreal content path but Unreal Engine"
                    f"is not available. Run inside Unreal Editor, or supply a"
                    f"real filesystem directory."
                )
            import unreal as ue
            aaset_paths = list(ue.EditorAssetLibrary.list_assets(directory, recursive=True))
        else:
            if not os.path.isdir(directory):
                raise ValueError (f"Not a valid directory: {directory}")
            for root, _dirs, files in os.walk(directory):
                for filename in sorted(files):
                    asset_paths.append(os.path.join(root,filename))

        results: list[Validation]= []
        for path in asset_paths:
            results.extend(self.validate_asset(path))
        return results

    def validate_context(self, context: FilesystemContext)->list[Validation]:
        log_env_status()
        results: list[Validation] = []
        for meta in context.get_assets():
            asset_path = meta.path
            # If this is a virtual /Game/ path (Unreal asset), skip filesystem-only rules
            is_unreal_asset = isinstance(asset_path, str) and asset_path.startswith("/Game/")
            for rule in self.rules:
                if is_unreal_asset and rule.category == "FileSystem":
                    # filesystem rules rely on os.path and real files; skip for virtual assets
                    continue
                try:
                    results.append(rule.validate(asset_path))
                except Exception as exc:
                    # Turn unexpected exceptions into a Validation result to avoid breaking the run
                    results.append(
                        Validation(
                            asset_path=asset_path,
                            category=rule.category,
                            rules=rule.name,
                            message=f"[Runner] Rule raised exception: {exc}",
                            severity=Severity.ERROR,
                            passed=False,
                        )
                    )
        return results

    def filter_results(
        self,
        results: Iterable[Validation],
        severity: Severity | str | None = None,
        category: str | None = None,
        include_passed: bool = False,
    ) -> list[Validation]:
        filtered: list[Validation] = []
        severity_key = severity.value if isinstance(severity, Severity) else severity
        for result in results:
            if not include_passed and result.passed:
                continue
            if severity_key is not None:
                severity_value = result.severity.value.lower()
                if severity_value != str(severity_key).lower():
                    continue
            if category is not None and result.category.lower() != str(category).lower():
                continue
            filtered.append(result)
        return filtered

    def build_report(
        self,
        results: list[Validation],
        severity: Severity | str | None = None,
        category: str | None = None,
        include_passed: bool = False,
    ) -> dict[str, object]:
        filtered = self.filter_results(
            results,
            severity=severity,
            category=category,
            include_passed=include_passed,
        )

        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed
        failed_filtered = [r for r in filtered if not r.passed]

        sev_counts: dict[Severity, int] = {s: 0 for s in Severity}
        for result in filtered:
            if not result.passed:
                sev_counts[result.severity] += 1

        grouped: dict[str, list[Validation]] = defaultdict(list)
        for result in failed_filtered:
            grouped[result.asset_path].append(result)

        return {
            "total_checks": total,
            "passed": passed,
            "failed": failed,
            "severity_counts": {severity.value: sev_counts[severity] for severity in (Severity.ERROR, Severity.WARNING, Severity.INFO)},
            "failures": [
                {
                    "asset_path": asset_path,
                    "results": [
                        {
                            "severity": failure.severity.value,
                            "rule": failure.rules,
                            "category": failure.category,
                            "message": failure.message,
                        }
                        for failure in asset_failures
                    ],
                }
                for asset_path, asset_failures in grouped.items()
            ],
        }

    def json_parser(self, results: list[Validation], output_path: str | os.PathLike[str] | None = None) -> str:
        data = [
            {
                "asset_path": result.asset_path,
                "category": result.category,
                "rules": result.rules,
                "message": result.message,
                "severity": result.severity.value,
                "passed": result.passed,
            }
            for result in results
        ]

        target_path = Path(output_path or "ValidationResults.json")
        if not target_path.is_absolute():
            target_path = (Path.cwd() / target_path).resolve()

        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, indent=2)

        return str(target_path)


    def Summary(
        self,
        results: list[Validation],
        severity: Severity | str | None = None,
        category: str | None = None,
        show_passed: bool = False,
        verbose: bool = False,
        quiet: bool = False,
    )->None:
        if not results:
            print("No validation results to display")
            return

        report = self.build_report(
            results,
            severity=severity,
            category=category,
            include_passed=show_passed,
        )
        total = report["total_checks"]
        passed = report["passed"]
        failed = report["failed"]
        sev_counts = report["severity_counts"]

        if quiet:
            return

        print("\n" + "="*72)
        print("Validation Summary")
        print("="*72)
        print(f"Total checks : {total:>5}")
        print(f"Passed       : {passed:>5}")
        print(f"Failed       : {failed:>5}")
        for sev in (Severity.ERROR, Severity.WARNING, Severity.INFO):
            count = sev_counts[sev.value]
            if count:
                print(f"{_SEVERITY_ICON[sev]} {sev.value:<9}: {count}")
        print("\n" + "="*72)

        failures = report["failures"]
        if not failures:
            print("All assets passed every check.")
            return

        print("FAILURES (Grouped by asset):")
        for asset in failures:
            asset_path = asset["asset_path"]
            print(f"\n{asset_path}:")
            for failure in asset["results"]:
                icon = _SEVERITY_ICON[Severity(failure["severity"])]
                print(
                    f"    {icon}  [{failure['severity']}]"
                    f" {failure['category']}:{failure['rule']} - {failure['message']}"
                )

        if show_passed and verbose:
            print("\nPASSED RESULTS:")
            for result in self.filter_results(results, include_passed=True):
                if result.passed:
                    print(f"    [PASS] {result.rules}: {result.asset_path}")

