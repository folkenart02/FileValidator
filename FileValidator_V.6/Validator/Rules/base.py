
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from ..config import Config

class Severity(Enum):

    ERROR="Error"
    WARNING="Warning"
    INFO="Info"


@dataclass
class Validation :
    asset_path : str
    category : str
    rules : str
    message : str
    severity : Severity
    passed : bool
    skipped: bool = field(default=False)

    def __str__(self)->str:
        status = "PASS" if self.passed else "FAIL"
        icon = ""if self.passed else "χ"
        return(
            f"[{status}{icon} [{self.severity.value:<7}]]"
            f"{self.rules:>25} {Path(self.asset_path).name}\n"
            f"{self.message}"
        )

class AbstractRule(ABC):
    name: str =""
    category: str = ""
    severity:Severity = Severity.ERROR

    def __init__(self, config:"Config")-> None:
        self.config=config

    @abstractmethod
    def validate(self, asset_path: str)->Validation:
        ...

    def _make_result(
        self,
        asset_path: str,
        passed: bool,
        message: str,
        severity: Severity | None = None,
    ) -> Validation:
        return Validation(
            asset_path=asset_path,
            category=self.category,
            rules=self.name,
            severity=(
                severity
                if severity is not None
                else (Severity.INFO if passed else self.severity)
            ),
            message=message,
            passed=passed,
        )
    
    def _make_skipped(self, asset_path: str, reason:str, severity: Severity | None = None,)-> Validation:
        return Validation(
            asset_path=asset_path,
            rules=self.name,
            category=self.category,
            severity=(severity if severity is not None else self.severity),
            message=f"[Skipped] {reason}",
            passed=True,
            skipped=True,
        )