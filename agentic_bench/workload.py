from __future__ import annotations
from dataclasses import dataclass
from typing import List
import json
from pathlib import Path

@dataclass
class PlanningSpec:
    cpu_ms_mean: float
    cpu_ms_jitter: float
    json_kb_mean: float
    json_kb_jitter: float

@dataclass
class MemorySpec:
    ops_per_step: int
    hit_rate: float

@dataclass
class ToolSpec:
    name: str
    p: float
    wait_ms_mean: float
    wait_ms_jitter: float
    json_kb_mean: float
    json_kb_jitter: float

@dataclass
class Workload:
    name: str
    description: str
    planning: PlanningSpec
    memory: MemorySpec
    tools: List[ToolSpec]

    @staticmethod
    def from_json(path: str | Path) -> "Workload":
        obj = json.loads(Path(path).read_text(encoding="utf-8"))
        planning = PlanningSpec(**obj["planning"])
        memory = MemorySpec(**obj["memory"])
        tools = [ToolSpec(**t) for t in obj.get("tools", [])]
        return Workload(
            name=obj.get("name","workload"),
            description=obj.get("description",""),
            planning=planning,
            memory=memory,
            tools=tools,
        )
