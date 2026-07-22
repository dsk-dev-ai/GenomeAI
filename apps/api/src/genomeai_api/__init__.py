from __future__ import annotations

import importlib

app = importlib.import_module("genomeai_api.main").app

__all__ = ["app"]
