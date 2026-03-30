from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class PTOSSThresholdBand:
    min: float
    max: float
    label: str
    risk_level: str
    default_action: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PTOSSThresholdBand":
        return cls(
            min=float(data.get("min", 0)),
            max=float(data.get("max", 0)),
            label=str(data.get("label", "")),
            risk_level=str(data.get("risk_level", "unknown")),
            default_action=str(data.get("default_action", "review")),
        )


@dataclass(slots=True)
class PTOSSMetricDefinition:
    metric_id: str
    name: str
    category: str
    description: str
    unit: str
    desired_direction: str
    formula_status: str
    inputs: list[str]
    thresholds: list[PTOSSThresholdBand]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PTOSSMetricDefinition":
        return cls(
            metric_id=str(data.get("metric_id", "")),
            name=str(data.get("name", "")),
            category=str(data.get("category", "")),
            description=str(data.get("description", "")),
            unit=str(data.get("unit", "")),
            desired_direction=str(data.get("desired_direction", "")),
            formula_status=str(data.get("formula_status", "")),
            inputs=[str(item) for item in data.get("inputs", [])],
            thresholds=[PTOSSThresholdBand.from_dict(item) for item in data.get("thresholds", [])],
        )


@dataclass(slots=True)
class PTOSSModeDefinition:
    mode_id: str
    name: str
    intended_for: str
    minimum_focus: list[str]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PTOSSModeDefinition":
        return cls(
            mode_id=str(data.get("mode_id", "")),
            name=str(data.get("name", "")),
            intended_for=str(data.get("intended_for", "")),
            minimum_focus=[str(item) for item in data.get("minimum_focus", [])],
        )


@dataclass(slots=True)
class PTOSSProtocolDefinition:
    protocol_id: str
    sequence: int
    name: str
    produces: list[str]
    gate: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PTOSSProtocolDefinition":
        return cls(
            protocol_id=str(data.get("protocol_id", "")),
            sequence=int(data.get("sequence", 0)),
            name=str(data.get("name", "")),
            produces=[str(item) for item in data.get("produces", [])],
            gate=str(data.get("gate", "")),
        )


@dataclass(slots=True)
class PTOSSIntegrationSurface:
    surface_id: str
    name: str
    outputs: list[str]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PTOSSIntegrationSurface":
        return cls(
            surface_id=str(data.get("surface_id", "")),
            name=str(data.get("name", "")),
            outputs=[str(item) for item in data.get("outputs", [])],
        )


@dataclass(slots=True)
class PTOSSFoundationSpec:
    standard_id: str
    full_name: str
    product_position: str
    status: str
    design_intent: str
    principles: list[str]
    modes: list[PTOSSModeDefinition]
    metrics: list[PTOSSMetricDefinition]
    protocols: list[PTOSSProtocolDefinition]
    integration_surfaces: list[PTOSSIntegrationSurface]
    raw: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PTOSSFoundationSpec":
        identity = data.get("identity", {})
        return cls(
            standard_id=str(identity.get("standard_id", "PT-OSS")),
            full_name=str(identity.get("full_name", "")),
            product_position=str(identity.get("product_position", "")),
            status=str(identity.get("status", "")),
            design_intent=str(identity.get("design_intent", "")),
            principles=[str(item) for item in data.get("principles", [])],
            modes=[PTOSSModeDefinition.from_dict(item) for item in data.get("modes", [])],
            metrics=[PTOSSMetricDefinition.from_dict(item) for item in data.get("metrics", [])],
            protocols=[PTOSSProtocolDefinition.from_dict(item) for item in data.get("protocols", [])],
            integration_surfaces=[PTOSSIntegrationSurface.from_dict(item) for item in data.get("integration_surfaces", [])],
            raw=data,
        )

    def metric_map(self) -> dict[str, PTOSSMetricDefinition]:
        return {item.metric_id: item for item in self.metrics}

    def protocol_map(self) -> dict[str, PTOSSProtocolDefinition]:
        return {item.protocol_id: item for item in self.protocols}

    def integration_surface_map(self) -> dict[str, PTOSSIntegrationSurface]:
        return {item.surface_id: item for item in self.integration_surfaces}


def load_pt_oss_foundation(path: Path) -> PTOSSFoundationSpec:
    data = json.loads(path.read_text(encoding="utf-8"))
    return PTOSSFoundationSpec.from_dict(data)
