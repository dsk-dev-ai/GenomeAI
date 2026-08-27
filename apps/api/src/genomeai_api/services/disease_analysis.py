"""Disease analysis engine — orchestrates OpenTargets, Disease Ontology, Monarch + AI."""

from __future__ import annotations

import logging

from genomeai_api.ai.base import AIProvider, AIRequest, AIResponse
from genomeai_api.integration.connectors.disease_ontology import DiseaseOntologyClient
from genomeai_api.integration.connectors.monarch import MonarchClient
from genomeai_api.integration.connectors.opentargets import OpenTargetsClient
from genomeai_api.schemas.disease_analysis import (
    DiseaseAnalysis,
    DiseaseInfo,
    GeneDiseaseAssociation,
    MonarchDiseaseResult,
)

logger = logging.getLogger(__name__)

DISEASE_SYSTEM_PROMPT = (
    "You are a bioinformatics expert specializing in disease genetics.\n"
    "Analyze the disease data provided and give a structured JSON response:\n"
    "1. Disease summary and clinical significance\n"
    "2. Key gene-disease associations and their strength\n"
    "3. Phenotypic features and clinical presentation\n"
    "4. Therapeutic implications and drug targets\n"
    "5. Research significance and future directions\n\n"
    "Respond with ONLY a JSON object:\n"
    "{\n"
    '  "disease_summary": "...",\n'
    '  "key_associations": [\n'
    '    {"gene": "...", "score": 0.0, "significance": "..."}\n'
    "  ],\n"
    '  "phenotypic_features": "...",\n'
    '  "therapeutic_implications": "...",\n'
    '  "research_significance": "..."\n'
    "}"
)


class DiseaseAnalysisEngine:
    """Orchestrates disease analysis from OpenTargets, DO, Monarch + AI."""

    def __init__(self, ai_provider: AIProvider) -> None:
        self._ai = ai_provider
        self._opentargets = OpenTargetsClient()
        self._do = DiseaseOntologyClient()
        self._monarch = MonarchClient()

    async def close(self) -> None:
        await self._opentargets.close()
        await self._do.close()
        await self._monarch.close()

    async def search_disease(self, query: str) -> DiseaseAnalysis:
        """Search for a disease by name/query."""
        diseases: list[DiseaseInfo] = []
        associations: list[GeneDiseaseAssociation] = []
        monarch_results: list[MonarchDiseaseResult] = []
        sources: list[str] = []

        # OpenTargets search
        try:
            ot_results = await self._opentargets.search_disease(query, size=5)
            for hit in ot_results:
                name_val = hit.get("name", "")
                diseases.append(DiseaseInfo(
                    disease_id=str(hit.get("id", "")),
                    name=str(name_val),
                    description=str(hit.get("description", "")),
                ))
            if ot_results:
                sources.append("OpenTargets")
        except Exception as exc:
            logger.warning("OpenTargets search failed for %s: %s", query, exc)

        # Disease Ontology search
        try:
            do_results = await self._do.search_terms(query)
            for term in do_results[:5]:
                term_id = str(term.get("id", term.get("term_id", "")))
                label = str(term.get("label", term.get("name", "")))
                definition = str(term.get("definition", ""))
                diseases.append(DiseaseInfo(
                    disease_id=term_id,
                    name=label,
                    description=definition,
                ))
            if do_results:
                sources.append("DiseaseOntology")
        except Exception as exc:
            logger.warning("Disease Ontology search failed for %s: %s", query, exc)

        # Monarch search
        try:
            monarch_hits = await self._monarch.search(query, limit=5)
            for hit in monarch_hits:
                cat = str(hit.get("category", ""))
                if "disease" in cat.lower() or "phenotype" in cat.lower():
                    monarch_results.append(MonarchDiseaseResult(
                        disease_id=str(hit.get("id", "")),
                        disease_name=str(hit.get("name", hit.get("label", ""))),
                        category=cat,
                    ))
            if monarch_hits:
                sources.append("Monarch")
        except Exception as exc:
            logger.warning("Monarch search failed for %s: %s", query, exc)

        # AI analysis
        ai_response = ""
        if sources:
            ai_response = await self._get_ai_analysis(
                query, diseases, associations, monarch_results,
            )

        return DiseaseAnalysis(
            query=query,
            diseases=diseases,
            gene_disease_associations=associations,
            monarch_results=monarch_results,
            ai_raw_response=ai_response,
            sources=sources,
        )

    async def analyze_gene_diseases(self, gene_symbol: str) -> DiseaseAnalysis:
        """Find diseases associated with a gene."""
        diseases: list[DiseaseInfo] = []
        associations: list[GeneDiseaseAssociation] = []
        monarch_results: list[MonarchDiseaseResult] = []
        sources: list[str] = []

        # OpenTargets: gene -> diseases
        try:
            ensembl_id = await self._opentargets.resolve_gene_to_ensembl(gene_symbol)
            if ensembl_id:
                target_data: dict[str, object] = (
                    await self._opentargets.get_target_diseases(ensembl_id, size=10)
                )
                disease_rows: object = target_data.get("associatedDiseases", {})
                if isinstance(disease_rows, dict):
                    rows: object = disease_rows.get("rows", [])
                    if isinstance(rows, list):
                        for row in rows:
                            if isinstance(row, dict):
                                disease_obj: object = row.get("disease", {})
                                score_val: object = row.get("score", 0)
                                if isinstance(disease_obj, dict):
                                    score = (
                                        float(score_val)
                                        if isinstance(score_val, (int, float))
                                        else 0.0
                                    )
                                    associations.append(GeneDiseaseAssociation(
                                        gene_symbol=gene_symbol,
                                        gene_id=str(target_data.get("id", "")),  # pyright: ignore[reportUnknownArgumentType]
                                        disease_name=str(disease_obj.get("name", "")),  # pyright: ignore[reportUnknownArgumentType]
                                        disease_id=str(disease_obj.get("id", "")),  # pyright: ignore[reportUnknownArgumentType]
                                        score=score,
                                    ))
            if associations:
                sources.append("OpenTargets")
        except Exception as exc:
            logger.warning("OpenTargets gene-disease failed for %s: %s", gene_symbol, exc)

        # Monarch: gene -> diseases
        try:
            monarch_assocs = await self._monarch.get_disease_associations(
                f"HGNC:{gene_symbol}",
                limit=10,
            )
            for assoc in monarch_assocs:
                disease_obj: object = assoc.get("disease", assoc.get("object", {}))
                if isinstance(disease_obj, dict):
                    monarch_results.append(MonarchDiseaseResult(
                        disease_id=str(disease_obj.get("id", "")),  # pyright: ignore[reportUnknownArgumentType]
                        disease_name=str(disease_obj.get("label", "")),  # pyright: ignore[reportUnknownArgumentType]
                        category=str(assoc.get("category", "")),
                    ))
            if monarch_assocs:
                sources.append("Monarch")
        except Exception as exc:
            logger.warning("Monarch gene-disease failed for %s: %s", gene_symbol, exc)

        ai_response = ""
        if sources:
            ai_response = await self._get_ai_analysis(
                gene_symbol, diseases, associations, monarch_results,
            )

        return DiseaseAnalysis(
            query=gene_symbol,
            diseases=diseases,
            gene_disease_associations=associations,
            monarch_results=monarch_results,
            ai_raw_response=ai_response,
            sources=sources,
        )

    async def _get_ai_analysis(
        self,
        query: str,
        diseases: list[DiseaseInfo],
        associations: list[GeneDiseaseAssociation],
        monarch_results: list[MonarchDiseaseResult],
    ) -> str:
        parts: list[str] = []
        if diseases:
            parts.append("Diseases found:")
            for d in diseases[:5]:
                parts.append(f"- {d.name} ({d.disease_id}): {d.description[:200]}")
        if associations:
            parts.append("\nGene-disease associations:")
            for a in associations[:5]:
                parts.append(f"- {a.gene_symbol} -> {a.disease_name} (score={a.score})")
        if monarch_results:
            parts.append("\nMonarch phenotype-disease associations:")
            for m in monarch_results[:5]:
                parts.append(f"- {m.disease_name} ({m.disease_id})")

        if not parts:
            return ""

        user_prompt = f"Query: {query}\n\n" + "\n".join(parts)
        request = AIRequest(
            system_prompt=DISEASE_SYSTEM_PROMPT,
            prompt=user_prompt,
            max_tokens=4096,
            temperature=0.3,
        )
        response: AIResponse = await self._ai.generate(request)
        return response.text

    async def _get_ai_analysis_gene(
        self,
        gene_symbol: str,
        associations: list[GeneDiseaseAssociation],
        monarch_results: list[MonarchDiseaseResult],
    ) -> str:
        parts: list[str] = [f"Gene: {gene_symbol}"]
        if associations:
            parts.append("\nGene-disease associations:")
            for a in associations[:10]:
                parts.append(f"- {a.disease_name} ({a.disease_id}) score={a.score:.3f}")
        if monarch_results:
            parts.append("\nMonarch associations:")
            for m in monarch_results[:10]:
                parts.append(f"- {m.disease_name} ({m.disease_id}) [{m.category}]")

        if len(parts) == 1:
            return ""

        user_prompt = "\n".join(parts)
        request = AIRequest(
            system_prompt=DISEASE_SYSTEM_PROMPT,
            prompt=user_prompt,
            max_tokens=4096,
            temperature=0.3,
        )
        response: AIResponse = await self._ai.generate(request)
        return response.text
