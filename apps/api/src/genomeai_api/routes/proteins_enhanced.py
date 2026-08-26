"""Protein analysis API endpoints — search and analyze proteins."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from genomeai_api.ai.gemini import GeminiProvider
from genomeai_api.integration.connectors.alphafold.client import AlphaFoldClient
from genomeai_api.integration.connectors.pdb.client import PDBClient
from genomeai_api.integration.connectors.uniprot.client import UniProtClient
from genomeai_api.schemas.protein_analysis import (
    AlphaFoldInfo,
    PDBInfo,
    ProteinAnalyzeRequest,
    ProteinAnalyzeResponse,
    ProteinSearchRequest,
    ProteinSearchResponse,
    ProteinSearchResult,
)
from genomeai_api.services.protein_analysis import ProteinAnalysisEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/proteins", tags=["protein-analysis"])


def _get_engine() -> ProteinAnalysisEngine:
    return ProteinAnalysisEngine(
        ai_provider=GeminiProvider(),
        uniprot_client=UniProtClient(),
        pdb_client=PDBClient(),
        alphafold_client=AlphaFoldClient(),
    )


@router.post("/analyze", response_model=ProteinAnalyzeResponse)
async def analyze_protein(
    request: ProteinAnalyzeRequest,
) -> ProteinAnalyzeResponse:
    """Analyze a protein using real UniProt + PDB + AlphaFold + AI."""
    if not request.gene and not request.accession:
        raise HTTPException(
            status_code=422,
            detail="Either 'gene' or 'accession' must be provided",
        )
    engine = _get_engine()
    try:
        if request.accession:
            analysis = await engine.analyze_by_accession(request.accession)
        else:
            analysis = await engine.analyze_by_gene(request.gene)
        pdb_infos = [
            PDBInfo(
                pdb_id=s.pdb_id,
                title=s.title,
                method=s.method,
                resolution=s.resolution,
            )
            for s in analysis.pdb_structures
        ]
        af_info = None
        if analysis.alphafold:
            af_info = AlphaFoldInfo(
                alphafold_id=analysis.alphafold.alphafold_id,
                sequence_length=analysis.alphafold.sequence_length,
                confidence_version=analysis.alphafold.confidence_version,
            )
        return ProteinAnalyzeResponse(
            protein_name=analysis.protein_name,
            accession=analysis.accession,
            gene_names=analysis.gene_names,
            organism=analysis.organism,
            length=analysis.length,
            function=analysis.function,
            subcellular_location=analysis.subcellular_location,
            pdb_structures=pdb_infos,
            alphafold=af_info,
            function_summary=analysis.function_summary,
            domains=analysis.domains,
            clinical_significance=analysis.clinical_significance,
            drug_targets=analysis.drug_targets,
            disease_associations=analysis.disease_associations,
            structural_notes=analysis.structural_notes,
            summary=analysis.summary,
            data_sources=analysis.data_sources,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("Protein analysis failed: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {exc}",
        )
    finally:
        await engine.close()


@router.post("/search", response_model=ProteinSearchResponse)
async def search_proteins(
    request: ProteinSearchRequest,
) -> ProteinSearchResponse:
    """Search UniProt for proteins by gene name."""
    client = UniProtClient()
    try:
        proteins = await client.search(
            request.query, max_results=request.max_results,
        )
        return ProteinSearchResponse(
            query=request.query,
            count=len(proteins),
            results=[
                ProteinSearchResult(
                    accession=p.accession,
                    entry_name=p.entry_name,
                    protein_name=p.protein_name,
                    gene_names=p.gene_names,
                    organism=p.organism,
                    length=p.length,
                )
                for p in proteins
            ],
        )
    except Exception as exc:
        logger.error("Protein search failed: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {exc}",
        )
    finally:
        await client.close()
