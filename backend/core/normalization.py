import os
import json
from typing import Dict, Any, Optional, List

_catalog_cache: Optional[Dict[str, Any]] = None
_alias_map: Dict[str, str] = {}


def _load_catalog() -> Dict[str, Any]:
    global _catalog_cache, _alias_map
    if _catalog_cache is not None:
        return _catalog_cache

    catalog_path = os.path.join(os.path.dirname(__file__), "metric_catalog.json")
    if os.path.exists(catalog_path):
        with open(catalog_path, "r", encoding="utf-8") as f:
            _catalog_cache = json.load(f)
    else:
        _catalog_cache = {"metrics": [], "presets": []}

    _alias_map.clear()
    for metric in _catalog_cache.get("metrics", []):
        standard_name = metric["standard_name"]
        _alias_map[standard_name.lower()] = standard_name
        for alias in metric.get("aliases", []):
            _alias_map[alias.lower()] = standard_name

    return _catalog_cache


def normalize_metric_name(raw_name: str) -> Optional[str]:
    _load_catalog()
    key = raw_name.strip().lower()
    return _alias_map.get(key)


def get_metric_info(standard_name: str) -> Optional[Dict[str, Any]]:
    _load_catalog()
    for metric in _catalog_cache.get("metrics", []):
        if metric["standard_name"] == standard_name:
            return metric
    return None


def convert_unit(value: float, from_unit: str, to_unit: str, standard_name: str) -> float:
    if from_unit == to_unit:
        return value

    info = get_metric_info(standard_name)
    if info is None:
        return value

    alt_units = info.get("alt_units", {})
    if from_unit in alt_units and to_unit == info.get("unit"):
        rule = alt_units[from_unit]
        return round(value * rule["factor"] + rule.get("offset", 0), 2)

    if to_unit in alt_units and from_unit == info.get("unit"):
        rule = alt_units[to_unit]
        if rule["factor"] != 0:
            return round((value - rule.get("offset", 0)) / rule["factor"], 2)
        return value

    return value


def check_is_abnormal(value: float, ref_min: Optional[float], ref_max: Optional[float]) -> bool:
    if ref_min is not None and value < ref_min:
        return True
    if ref_max is not None and value > ref_max:
        return True
    return False


def validate_medical_range(value: float, standard_name: str) -> bool:
    info = get_metric_info(standard_name)
    if info is None:
        return True
    medical_max = info.get("medical_max")
    if medical_max is not None and value > medical_max:
        return False
    return True


def get_presets() -> List[Dict[str, Any]]:
    _load_catalog()
    return _catalog_cache.get("presets", [])
