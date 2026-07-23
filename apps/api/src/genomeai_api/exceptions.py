from __future__ import annotations

from genomeai_shared import ApplicationError


class DuplicateGenomeAccessionError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(
            message="Genome accession already exists",
            detail="A genome with this accession already exists in the database",
        )


class DuplicateSampleError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(
            message="Sample already exists",
            detail="A sample with this sample_id already exists in the database",
        )


class DuplicateGeneError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(
            message="Gene already exists",
            detail="A gene with this gene_id already exists in the database",
        )


class DuplicateVariantError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(
            message="Variant already exists",
            detail="A variant with this variant_id already exists in the database",
        )


class DuplicateTranscriptError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(
            message="Transcript already exists",
            detail="A transcript with this transcript_id already exists in the database",
        )


class DuplicateProteinError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(
            message="Protein already exists",
            detail="A protein with this protein_id already exists in the database",
        )


class DuplicateExperimentError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(
            message="Experiment already exists",
            detail="An experiment with this experiment_id already exists in the database",
        )


class InvalidForeignKeyError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(
            message="Invalid reference",
            detail="A referenced entity does not exist in the database",
        )
