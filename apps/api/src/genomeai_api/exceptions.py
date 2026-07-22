from __future__ import annotations

from genomeai_shared import ApplicationError


class DuplicateGenomeAccessionError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(
            message="Genome accession already exists",
            detail="A genome with this accession already exists in the database",
        )
