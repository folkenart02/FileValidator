from __future__ import annotations
from typing import Type
from .Rules.base import AbstractRule, Severity

class RuleRegistry:

    _instance: "RuleRegistry | None" = None

    def __new__(cls)->"RuleRegistry":
        if cls._instance is None:
            cls._instance=super().__new__(cls)
        return cls._instance

    def __init__(self)->None:
        if not hasattr(self, "_initialized"):
            self._rules: dict[str,Type[AbstractRule]]={}
            self._initialized=True
        

    def register(self, cls: "Type[AbstractRule]") -> "Type[AbstractRule]":
        if not cls.name:
            raise ValueError(
                f"Rule class {cls.__name__} must declare a non-empty"
                f"'name' class attribute before being registered"
            )
        
        if not cls.category:
            raise ValueError(
                f"Rule class {cls.__name__} must declare a non-empty"
                f"'category' class attribute before being registered"
            )
        
        if cls.name in self._rules and self._rules[cls.name] is not cls:
            raise ValueError(
                f"Rule class {cls.__name__} is already registered by"
                f"{self._rules[cls.name].__name__}"
                f"Each rule must have a unique name"
            )
        self._rules[cls.name]=cls
        return cls

    def get_rules(self,
        category: str| None=None,
        severity: Severity | None=None
        )-> list[Type[AbstractRule]]:
        rules : list[Type[AbstractRule]]=list(self._rules.values())
        if category is not None:
            cat_lower=category.lower()
            rules=[r for r in rules if r.category.lower()==cat_lower]
        if severity is not None:
            rules=[r for r in rules if r.severity==severity]
        return rules
    

    def discover(self, package_path: str | None=None)->None:
        import importlib
        import pkgutil
        from . import Rules as rules_pkg

        for _, module_name, _ in pkgutil.iter_modules(rules_pkg.__path__):
            if module_name=="base":
                continue
            importlib.import_module(f".Rules.{module_name}", package=__package__)
            
            
    def list_rules(self)-> dict[str, Type[AbstractRule]]:
            return dict(self._rules)
        
    def _len(self)-> int:
        return len(self._rules)

    def __repr__(self)-> str:
        return f"RuleRegistry(rules={list(self._rules.keys())})"

registry=RuleRegistry()    
        