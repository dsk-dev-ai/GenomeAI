"""Multi-domain report schemas."""

from __future__ import annotations

from pydantic import BaseModel


class GeneReport(BaseModel):
    """Gene analysis summary."""

    gene: str = ""
    summary: str = ""
    data: dict[str, object] = {}


class VariantReport(BaseModel):
    """Variant analysis summary."""

    variant: str = ""
    summary: str = ""
    data: dict[str, object] = {}


class ProteinReport(BaseModel):
    """Protein analysis summary."""

    protein: str = ""
    summary: str = ""
    data: dict[str, object] = {}


class LiteratureReport(BaseModel):
    """Literature analysis summary."""

    query: str = ""
    summary: str = ""
    paper_count: int = 0
    data: dict[str, object] = {}


class DrugReport(BaseModel):
    """Drug analysis summary."""

    gene: str = ""
    summary: str = ""
    drug_count: int = 0
    data: dict[str, object] = {}


class PathwayReport(BaseModel):
    """Pathway analysis summary."""

    gene: str = ""
    summary: str = ""
    data: dict[str, object] = {}


class DiseaseReport(BaseModel):
    """Disease analysis summary."""

    query: str = ""
    summary: str = ""
    data: dict[str, object] = {}


class MultiDomainReportRequest(BaseModel):
    """Request for multi-domain report."""

    gene: str
    variant: str = ""


class MultiDomainReportResponse(BaseModel):
    """Response from multi-domain report."""

    gene: str
    gene_report: GeneReport = GeneReport()
    variant_report: VariantReport = VariantReport()
    protein_report: ProteinReport = ProteinReport()
    literature_report: LiteratureReport = LiteratureReport()
    drug_report: DrugReport = DrugReport()
    pathway_report: PathwayReport = PathwayReport()
    disease_report: DiseaseReport = DiseaseReport()
    executive_summary: str = ""
    sources: list[str] = []
