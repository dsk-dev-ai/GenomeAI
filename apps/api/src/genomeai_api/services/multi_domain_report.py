"""Multi-domain report engine — aggregates all 7 slices into one report."""

from __future__ import annotations

import asyncio
import logging

from genomeai_api.ai.base import AIProvider, AIRequest, AIResponse
from genomeai_api.services.disease_analysis import DiseaseAnalysisEngine
from genomeai_api.services.drug_analysis import DrugAnalysisEngine
from genomeai_api.services.gene_analysis import GeneAnalysisEngine
from genomeai_api.services.literature_search import LiteratureSearchEngine
from genomeai_api.services.pathway_analysis import PathwayAnalysisEngine
from genomeai_api.services.protein_analysis import ProteinAnalysisEngine
from genomeai_api.services.variant_interpretation import VariantInterpretationEngine

logger = logging.getLogger(__name__)

EXECUTIVE_SUMMARY_PROMPT = (
    "You are a genomics research expert. Given data from multiple domains "
    "(gene, variant, protein, literature, drug, pathway, disease), produce "
    "a comprehensive executive summary. Include:\n"
    "1. Gene function and clinical relevance\n"
    "2. Key variants and their pathogenicity\n"
    "3. Protein structure and function\n"
    "4. Literature landscape and research trends\n"
    "5. Therapeutic opportunities and drug targets\n"
    "6. Pathway involvement and biological mechanisms\n"
    "7. Disease associations and clinical implications\n"
    "8. Overall research significance and future directions\n\n"
    "Respond with ONLY a JSON object:\n"
    "{\n"
    '  "executive_summary": "...",\n'
    '  "key_findings": ["..."],\n'
    '  "clinical_relevance": "...",\n'
    '  "research_priorities": ["..."]\n'
    "}"
)


class MultiDomainReportEngine:
    """Aggregates all domain analyses into a single report."""

    def __init__(self, ai_provider: AIProvider) -> None:
        self._ai = ai_provider

    async def close(self) -> None:
        """Release the shared AI provider used by sub-analyses."""
        await self._ai.close()

    async def generate_report(
        self,
        gene: str,
        variant: str = "",
    ) -> dict[str, object]:
        """Generate a comprehensive multi-domain report for a gene."""
        sources: list[str] = []

        gene_data: dict[str, object] = {}
        variant_data: dict[str, object] = {}
        protein_data: dict[str, object] = {}
        literature_data: dict[str, object] = {}
        drug_data: dict[str, object] = {}
        pathway_data: dict[str, object] = {}
        disease_data: dict[str, object] = {}

        async def _fetch_gene() -> None:
            try:
                engine = GeneAnalysisEngine(
                    ai_provider=self._ai,
                    close_ai_provider=False,
                )
                result = await engine.analyze_by_symbol(gene)
                gene_data["summary"] = result.summary
                gene_data["data"] = {
                    "gene": result.gene_symbol,
                    "organism": result.organism,
                    "summary": result.summary,
                }
                sources.append("Gene")
                await engine.close()
            except Exception as exc:
                logger.warning("Gene analysis failed: %s", exc)

        async def _fetch_variant() -> None:
            if not variant:
                return
            try:
                engine = VariantInterpretationEngine(
                    ai_provider=self._ai,
                    close_ai_provider=False,
                )
                results = await engine.interpret_by_gene(gene, max_variants=5)
                if results:
                    result = results[0]
                    variant_data["summary"] = result.summary
                    variant_data["data"] = {
                        "variant": result.variant_description,
                        "interpretation": result.summary,
                    }
                sources.append("Variant")
                await engine.close()
            except Exception as exc:
                logger.warning("Variant analysis failed: %s", exc)

        async def _fetch_protein() -> None:
            try:
                engine = ProteinAnalysisEngine(
                    ai_provider=self._ai,
                    close_ai_provider=False,
                )
                result = await engine.analyze_by_gene(gene)
                protein_data["summary"] = result.function_summary
                protein_data["data"] = {
                    "protein": gene,
                    "uniprot_id": result.accession,
                    "structures": len(result.pdb_structures),
                }
                sources.append("Protein")
                await engine.close()
            except Exception as exc:
                logger.warning("Protein analysis failed: %s", exc)

        async def _fetch_literature() -> None:
            try:
                engine = LiteratureSearchEngine(
                    ai_provider=self._ai,
                    close_ai_provider=False,
                )
                result: dict[str, object] = await engine.search(gene, max_results=5)
                lit_summary = result.get("ai_analysis", "")
                epmc_raw: object = result.get("europepmc_articles", [])
                epmc_list: list[object] = epmc_raw if isinstance(epmc_raw, list) else []
                paper_count = len(epmc_list)
                literature_data["summary"] = lit_summary
                literature_data["paper_count"] = paper_count
                literature_data["data"] = {
                    "query": gene,
                    "paper_count": paper_count,
                }
                sources.append("Literature")
                await engine.close()
            except Exception as exc:
                logger.warning("Literature analysis failed: %s", exc)

        async def _fetch_drug() -> None:
            try:
                engine = DrugAnalysisEngine(
                    ai_provider=self._ai,
                    close_ai_provider=False,
                )
                result: dict[str, object] = await engine.analyze(gene)
                drug_summary = result.get("ai_analysis", "")
                chembl_raw: object = result.get("chembl_drugs", [])
                chembl_list: list[object] = chembl_raw if isinstance(chembl_raw, list) else []
                drug_count = len(chembl_list)
                drug_data["summary"] = drug_summary
                drug_data["drug_count"] = drug_count
                drug_data["data"] = {
                    "gene": gene,
                    "drug_count": drug_count,
                }
                sources.append("Drug")
                await engine.close()
            except Exception as exc:
                logger.warning("Drug analysis failed: %s", exc)

        async def _fetch_pathway() -> None:
            try:
                engine = PathwayAnalysisEngine(
                    ai_provider=self._ai,
                    close_ai_provider=False,
                )
                result = await engine.analyze_by_gene(gene)
                pathway_data["summary"] = result.ai_raw_response
                pathway_data["data"] = {
                    "gene": gene,
                    "reactome": len(result.reactome_pathways),
                    "kegg": len(result.kegg_pathways),
                    "string_interactions": len(result.string_interactions),
                }
                sources.append("Pathway")
                await engine.close()
            except Exception as exc:
                logger.warning("Pathway analysis failed: %s", exc)

        async def _fetch_disease() -> None:
            try:
                engine = DiseaseAnalysisEngine(
                    ai_provider=self._ai,
                    close_ai_provider=False,
                )
                result = await engine.analyze_gene_diseases(gene)
                disease_data["summary"] = result.ai_raw_response
                disease_data["data"] = {
                    "gene": gene,
                    "diseases": len(result.diseases),
                    "associations": len(result.gene_disease_associations),
                }
                sources.append("Disease")
                await engine.close()
            except Exception as exc:
                logger.warning("Disease analysis failed: %s", exc)

        await asyncio.gather(
            _fetch_gene(),
            _fetch_variant(),
            _fetch_protein(),
            _fetch_literature(),
            _fetch_drug(),
            _fetch_pathway(),
            _fetch_disease(),
        )

        executive_summary = await self._get_executive_summary(
            gene, gene_data, variant_data, protein_data,
            literature_data, drug_data, pathway_data, disease_data,
        )

        return {
            "gene": gene,
            "gene_report": gene_data,
            "variant_report": variant_data,
            "protein_report": protein_data,
            "literature_report": literature_data,
            "drug_report": drug_data,
            "pathway_report": pathway_data,
            "disease_report": disease_data,
            "executive_summary": executive_summary,
            "sources": sources,
        }

    async def _get_executive_summary(
        self,
        gene: str,
        gene_data: dict[str, object],
        variant_data: dict[str, object],
        protein_data: dict[str, object],
        literature_data: dict[str, object],
        drug_data: dict[str, object],
        pathway_data: dict[str, object],
        disease_data: dict[str, object],
    ) -> str:
        parts: list[str] = [f"Gene: {gene}"]

        summary_fields: list[tuple[dict[str, object], str]] = [
            (gene_data, "Gene analysis"),
            (variant_data, "Variant analysis"),
            (protein_data, "Protein analysis"),
            (literature_data, "Literature"),
            (drug_data, "Drug analysis"),
            (pathway_data, "Pathway analysis"),
            (disease_data, "Disease analysis"),
        ]
        for data_dict, label in summary_fields:
            summary_val = data_dict.get("summary", "")
            if summary_val and isinstance(summary_val, str):
                parts.append(f"\n{label}: {summary_val[:500]}")

        if len(parts) == 1:
            return ""

        request = AIRequest(
            system_prompt=EXECUTIVE_SUMMARY_PROMPT,
            prompt="\n".join(parts),
            max_tokens=4096,
            temperature=0.3,
        )
        try:
            response: AIResponse = await self._ai.generate(request)
            return response.text
        except Exception as exc:
            logger.warning("Executive summary AI analysis failed: %s", exc)
            return "\n".join(parts[1:])
