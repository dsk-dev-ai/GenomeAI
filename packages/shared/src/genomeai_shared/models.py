from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class BaseModel:
    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BaseModel:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
