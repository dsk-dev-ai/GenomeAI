from __future__ import annotations

import logging
from dataclasses import dataclass, field

from genomeai_config import Settings


@dataclass
class AppState:
    settings: Settings
    logger: logging.Logger = field(compare=False)
