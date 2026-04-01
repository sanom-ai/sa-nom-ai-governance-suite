import json
from pathlib import Path

from sa_nom_governance.alignment.constitution_models import AlignmentPrinciple, RegionalConstitution


class RegionalConstitutionRegistry:
    def __init__(self, catalog_dir: Path) -> None:
        self.catalog_dir = catalog_dir
        self._catalog = self._load_catalog()

    def list_regions(self) -> list[dict[str, object]]:
        return [
            {
                "region_id": item.region_id,
                "display_name": item.display_name,
                "geography_scope": item.geography_scope,
                "default_locale": item.default_locale,
                "constitutional_version": item.constitutional_version,
                "principles_total": len(item.principles),
                "values": list(item.values),
            }
            for item in self._catalog.values()
        ]

    def load(self, region_id: str) -> RegionalConstitution:
        try:
            return self._catalog[region_id]
        except KeyError as exc:
            available = ", ".join(sorted(self._catalog)) or "none"
            raise KeyError(f"Unknown regional constitution: {region_id}. Available regions: {available}") from exc

    def build_snapshot(self) -> dict[str, object]:
        regions = self.list_regions()
        return {
            "summary": {
                "regions_total": len(regions),
                "principles_total": sum(int(item["principles_total"]) for item in regions),
            },
            "regions": regions,
        }

    def _load_catalog(self) -> dict[str, RegionalConstitution]:
        if not self.catalog_dir.exists():
            return {}
        items: dict[str, RegionalConstitution] = {}
        for path in sorted(self.catalog_dir.glob('*.json')):
            constitution = self._load_constitution(path)
            items[constitution.region_id] = constitution
        return items

    def _load_constitution(self, path: Path) -> RegionalConstitution:
        raw = json.loads(path.read_text(encoding='utf-8'))
        for field_name in [
            "region_id",
            "display_name",
            "geography_scope",
            "default_locale",
            "constitutional_version",
        ]:
            if not raw.get(field_name):
                raise ValueError(f"Regional constitution {path.name} is missing required field: {field_name}")
        principles_raw = raw.get("principles", [])
        if not isinstance(principles_raw, list) or not principles_raw:
            raise ValueError(f"Regional constitution {path.name} must define at least one principle")
        principles: list[AlignmentPrinciple] = []
        for item in principles_raw:
            for field_name in ["principle_id", "title", "category", "description"]:
                if not item.get(field_name):
                    raise ValueError(f"Regional constitution {path.name} has a principle missing: {field_name}")
            principles.append(
                AlignmentPrinciple(
                    principle_id=str(item["principle_id"]),
                    title=str(item["title"]),
                    category=str(item["category"]),
                    description=str(item["description"]),
                    weight=str(item.get("weight", "supporting")),
                    keywords=[str(value) for value in item.get("keywords", [])],
                )
            )
        return RegionalConstitution(
            region_id=str(raw["region_id"]),
            display_name=str(raw["display_name"]),
            geography_scope=str(raw["geography_scope"]),
            default_locale=str(raw["default_locale"]),
            constitutional_version=str(raw["constitutional_version"]),
            values=[str(value) for value in raw.get("values", [])],
            communication_posture={str(key): str(value) for key, value in dict(raw.get("communication_posture", {})).items()},
            regulatory_sources=[str(value) for value in raw.get("regulatory_sources", [])],
            principles=principles,
            notes=str(raw.get("notes", "")),
            safe_claim=str(raw.get("safe_claim", "")),
        )
