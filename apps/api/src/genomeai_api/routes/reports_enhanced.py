"""Multi-domain report API router."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException

from genomeai_api.ai.gemini import GeminiProvider
from genomeai_api.schemas.multi_domain_report import (
    DiseaseReport,
    DrugReport,
    GeneReport,
    LiteratureReport,
    MultiDomainReportRequest,
    MultiDomainReportResponse,
    PathwayReport,
    ProteinReport,
    VariantReport,
)
from genomeai_api.services.multi_domain_report import MultiDomainReportEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


def _get_engine() -> MultiDomainReportEngine:
    return MultiDomainReportEngine(ai_provider=GeminiProvider())


def _parse_ai_json(raw: str) -> str:
    if not raw:
        return ""
    try:
        parsed = json.loads(raw)
        return json.dumps(parsed, indent=2)
    except (json.JSONDecodeError, TypeError):
        return raw


def _safe_str(val: object) -> str:
    if isinstance(val, str):
        return val
    return ""


def _safe_dict(val: object) -> dict[str, object]:
    if isinstance(val, dict):
        return val
    return {}


def _safe_int(val: object) -> int:
    if isinstance(val, (int, float)):
        return int(val)
    return 0


def _safe_str_list(val: object) -> list[str]:
    if isinstance(val, list):
        return [str(s) for s in val if isinstance(s, str)]
    return []


@router.post("/multi-domain", response_model=MultiDomainReportResponse)
async def generate_report(
    request: MultiDomainReportRequest,
) -> MultiDomainReportResponse:
    """Generate a comprehensive multi-domain report for a gene."""
    engine = _get_engine()
    try:
        result = await engine.generate_report(
            gene=request.gene,
            variant=request.variant,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        await engine.close()

    gene_report_data = _safe_dict(result.get("gene_report"))
    variant_report_data = _safe_dict(result.get("variant_report"))
    protein_report_data = _safe_dict(result.get("protein_report"))
    literature_report_data = _safe_dict(result.get("literature_report"))
    drug_report_data = _safe_dict(result.get("drug_report"))
    pathway_report_data = _safe_dict(result.get("pathway_report"))
    disease_report_data = _safe_dict(result.get("disease_report"))

    return MultiDomainReportResponse(
        gene=_safe_str(result.get("gene")),
        gene_report=GeneReport(
            gene=request.gene,
            summary=_safe_str(gene_report_data.get("summary")),
            data=_safe_dict(gene_report_data.get("data")),
        ),
        variant_report=VariantReport(
            variant=request.variant,
            summary=_safe_str(variant_report_data.get("summary")),
            data=_safe_dict(variant_report_data.get("data")),
        ),
        protein_report=ProteinReport(
            protein=request.gene,
            summary=_safe_str(protein_report_data.get("summary")),
            data=_safe_dict(protein_report_data.get("data")),
        ),
        literature_report=LiteratureReport(
            query=request.gene,
            summary=_safe_str(literature_report_data.get("summary")),
            paper_count=_safe_int(literature_report_data.get("paper_count")),
            data=_safe_dict(literature_report_data.get("data")),
        ),
        drug_report=DrugReport(
            gene=request.gene,
            summary=_safe_str(drug_report_data.get("summary")),
            drug_count=_safe_int(drug_report_data.get("drug_count")),
            data=_safe_dict(drug_report_data.get("data")),
        ),
        pathway_report=PathwayReport(
            gene=request.gene,
            summary=_safe_str(pathway_report_data.get("summary")),
            data=_safe_dict(pathway_report_data.get("data")),
        ),
        disease_report=DiseaseReport(
            query=request.gene,
            summary=_safe_str(disease_report_data.get("summary")),
            data=_safe_dict(disease_report_data.get("data")),
        ),
        executive_summary=_parse_ai_json(
            _safe_str(result.get("executive_summary")),
        ),
        sources=_safe_str_list(result.get("sources")),
    )
