import os
import json
from typing import Any

#DEFAULTS, in case there is no need to modify the rules

DEFAULTS: dict [str, Any] = {
    "env.Max_filesizeMB": 60,
    "chr.Max_filesizeMB": 100,
    "max_filename_length": 70,
    "naming_patterns": r"^[A-Z][a-zA-Z0-9_]+$",
    "env.prefixes": {
        "EnvT_":[".png", ".tga", ".exr", ".jpg"],
        "EnvM_":[".uasset", ".fbx", ".gltf", ".usd"],
        "EnvMTL_":[".uasset"]
    },
    "chr.prefixes": {
        "ChrT_":[".png", ".tga", ".exr", ".jpg"],
        "ChrM_":[".uasset", ".fbx"],
        "ChrMTL_":[".uasset"],
        "SM_":[".uasset"]
    },
    "blueprint_prefixes":{
        "BP_":[".uasset"],
    },
    "error_unkown_ext":True,
    "forbidden_folders" : ["temp"],
    "max_allowed_triangles.env": 5000,
    "max_allowed_triangles.chr": 10000,
    "max_materials.chr": 4,
    "max_materials.env": 3,
    "txt_size_limit": 30,
    "material_skip_engine_materials": True,
    "material_exempt_patterns": ["*_N", "*_Normal", "*_normal", "*_nrm"],
    "verbose": False,
    "quiet": False,
    "show_passed": False,
    "output_json": True,
    "output_path": "ValidationResults.json",
    "severity_filter": None,
}



class Config:

    def __init__(self, path: str | None = None) -> None:
        self._data: dict[str, Any] = dict(DEFAULTS)
        self._load_json(path)
        self._load_env()

    def _load_json(self, path:str | None) -> None:

        if path is None:
            return
        try:
            with open(path, "r", encoding="utf-8") as fh:
                overrides = json.load(fh)
            if not isinstance(overrides, dict):
                raise ValueError(
                    f"Config JSON must be an object (dict)."
                    f"got {type(overrides).__name__}"
                )
            self._data.update(overrides)
            print(f"[CONFIG] Loaded overrides from: {path}")

        except FileNotFoundError:
            print(
                f"[CONFIG] Warning: config file not fount at {path}"
                f"  - Using defaults."
            )
        except(json.JSONDecodeError, ValueError) as exc:
            print(
                f"[CONFIG] Warning: could not parse '{path}': {exc}"
                f"  - Using defaults."
            )

    def _load_env(self)->None:
        prefix= "VALIDATOR"
        for env_key, raw_value in os.environ.items():
            if not env_key.startswith(prefix):
                continue

            config_key = env_key[len(prefix):].lower()
            if config_key=="config_path":
                continue
            self._data[config_key]=self._coerce(config_key, raw_value)

    def _coerce(self, key:str, raw:str)->Any:
        if key not in DEFAULTS:
            return raw
        defaults = DEFAULTS[key]
        try:
            if isinstance(defaults, bool):
                return raw.strip().lower() in ("1", "true", "yes", "on")
            if isinstance(defaults, int):
                return int(raw)
            if isinstance(defaults, float):
                return float(raw)
            if isinstance(defaults, (list, dict)):
                return json.loads(raw)
            if defaults is None:
                return raw.strip()
        except (ValueError, json.JSONDecodeError) as exc:
            print(
                f"[CONFIG] Warning: could not coerce env var"
                f"{key}={raw!r}: {exc}  -keeping raw string"
            )
        return raw
    

    #PUBLIC INTERFACE

    def get(self, key:str, default: Any = None)-> Any:
        return self._data.get(key, default)

    def __getitem__(self, key:str, default: Any = None)-> Any:
        return self._data[key]

    def __contains__(self, key:str)->bool:
        return key in self._data

    def __repr__(self)->str:
        return f"Config({self._data!r})"




