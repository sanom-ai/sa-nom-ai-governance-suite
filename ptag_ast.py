from dataclasses import dataclass, field


@dataclass(slots=True)
class PTAGBlock:
    name: str
    body: str


@dataclass(slots=True)
class PTAGDocument:
    source: str
    headers: dict[str, str] = field(default_factory=dict)
    blocks: list[PTAGBlock] = field(default_factory=list)
