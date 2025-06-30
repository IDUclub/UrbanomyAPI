import json
from pathlib import Path
from typing import Dict, Set

_CFG_PATH = Path(__file__).resolve().parent.parent / "config" / "zone_mapping.json"

with _CFG_PATH.open("r", encoding="utf-8") as _f:
    _cfg = json.load(_f)

zone_mapping: Dict[str, int] = _cfg["zone_mapping"]
"""Mapping from Urbanomy library land-use names to UrbanDB zone_type_id."""

VALID_ZONE_TYPE_IDS: Set[int] = set(_cfg["valid_zone_type_ids"])
"""Allowed zone_type_id values for incoming FeatureCollection."""
