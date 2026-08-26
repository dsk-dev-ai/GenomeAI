"""Variant interpretation API endpoints — search and interpret variants."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from genomeai_api.ai.ollama import OllamaProvider
from genomeai_api.integration.connectors.clinvar.client import ClinVarClient
from genomeai_api.integration.connectors.ensembl_vep.client import EnsemblVEPClient
from genomeai_api.integration.connectors.gnomad.client import GnomADClient
from genomeai_api.schemas.variant_interpretation import (
    ClinVarInfo,
    GnomADInfo,
    VariantInterpretRequest,
    VariantInterpretResponse,
    VariantSearchRequest,
    VariantSearchResponse,
    VariantSearchResult,
    VEPInfo,
)
from genomeai_api.services.variant_interpretation import VariantInterpretationEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/variants", tags=["variant-interpretation"])


def _get_engine() -> VariantInterpretationEngine:
    return VariantInterpretationEngine(
        ai_provider=OllamaProvider(),
        clinvar_client=ClinVarClient(),
        gnomad_client=GnomADClient(),
        vep_client=EnsemblVEPClient(),
    )


@router.post("/interpret", response_model=VariantInterpretResponse)
async def interpret_variant(request: VariantInterpretRequest) -> VariantInterpretResponse:
    """Interpret variants for a gene using real ClinVar + gnomAD + VEP + AI."""
    engine = _get_engine()
    try:
        if request.clinvar_id:
            interp = await engine.interpret_by_clinvar_id(request.clinvar_id)
            return _format_response(interp)
        if request.hgvs_c:
            interp = await engine.interpret_by_variant(request.gene, request.hgvs_c)
            return _format_response(interp)
        interps = await engine.interpret_by_gene(
            request.gene, request.max_variants,
        )
        if not interps:
            msg = f"No pathogenic variants found for {request.gene}"
            raise HTTPException(status_code=404, detail=msg)
        return _format_response(interps[0])
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("Variant interpretation failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Interpretation failed: {exc}")
    finally:
        await engine.close()


@router.post("/search", response_model=VariantSearchResponse)
async def search_variants(request: VariantSearchRequest) -> VariantSearchResponse:
    """Search ClinVar for variants by gene."""
    client = ClinVarClient()
    try:
        records = await client.search_variants(
            gene=request.gene,
            significance=request.significance or None,
            max_results=request.max_results,
        )
        return VariantSearchResponse(
            gene=request.gene,
            count=len(records),
            results=[
                VariantSearchResult(
                    clinvar_id=r.clinvar_id,
                    gene_symbol=r.gene_symbol,
                    clinical_significance=r.clinical_significance,
                    condition=r.condition,
                    hgvs_c=r.hgvs_c,
                    hgvs_p=r.hgvs_p,
                )
                for r in records
            ],
        )
    except Exception as exc:
        logger.error("Variant search failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Search failed: {exc}")
    finally:
        await client.close()


def _format_response(interp: object) -> VariantInterpretResponse:
    from genomeai_api.services.variant_interpretation import VariantInterpretation
    i = interp
    if not isinstance(i, VariantInterpretation):
        raise ValueError("Invalid interpretation type")
    clinvar_info = None
    if i.clinvar:
        clinvar_info = ClinVarInfo(
            clinvar_id=i.clinvar.clinvar_id,
            clinical_significance=i.clinvar.clinical_significance,
            review_status=i.clinvar.review_status,
            condition=i.clinvar.condition,
            hgvs_c=i.clinvar.hgvs_c,
            hgvs_p=i.clinvar.hgvs_p,
        )
    gnomad_info = None
    if i.gnomad:
        gnomad_info = GnomADInfo(
            variant_id=i.gnomad.variant_id,
            allele_frequency=i.gnomad.genome_af or i.gnomad.exome_af,
            allele_count=i.gnomad.genome_ac or i.gnomad.exome_ac,
            allele_number=i.gnomad.genome_an or i.gnomad.exome_an,
        )
    vep_info = None
    if i.vep and i.vep.consequences:
        c = i.vep.consequences[0]
        vep_info = VEPInfo(
            consequence=", ".join(c.consequence_terms),
            impact=c.impact,
            sift_prediction=c.sift_prediction,
            sift_score=c.sift_score,
            polyphen_prediction=c.polyphen_prediction,
            polyphen_score=c.polyphen_score,
        )
    return VariantInterpretResponse(
        variant_description=i.variant_description,
        gene_symbol=i.gene_symbol,
        clinvar=clinvar_info,
        gnomad=gnomad_info,
        vep=vep_info,
        pathogenicity=i.pathogenicity,
        acmg_criteria=i.acmg_criteria,
        reasoning=i.reasoning,
        clinical_actionability=i.clinical_actionability,
        summary=i.summary,
        data_sources=i.data_sources,
    )
