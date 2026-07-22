from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self


@dataclass
class BaseModel:
    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
