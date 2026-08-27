"""Pathway analysis engine — combines Reactome + STRING + KEGG with Gemini AI."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from genomeai_api.ai.base import AIProvider, AIRequest
from genomeai_api.integration.connectors.kegg.client import KEGGClient
from genomeai_api.integration.connectors.reactome.client import ReactomeClient
from genomeai_api.integration.connectors.string_db.client import StringDBClient

logger = logging.getLogger(__name__)

PATHWAY_SYSTEM_PROMPT = (
    "You are a bioinformatics expert specializing in biological pathway analysis.\n"
    "Analyze the pathway data provided and give a structured JSON response about:\n"
    "1. Key biological pathways the gene/proteins are involved in\n"
    "2. Functional enrichment results and their significance\n"
    "3. Protein-protein interaction network insights\n"
    "4. Cross-database pathway concordance (Reactome vs KEGG vs STRING)\n"
    "5. Clinical and research significance of the pathways\n\n"
    "Respond with ONLY a JSON object (no markdown, no explanation before/after):\n"
    "{\n"
    '  "pathway_summary": "...",\n'
    '  "key_pathways": [\n'
    '    {"name": "...", "source": "Reactome/KEGG/STRING", '
    '"significance": "...", "description": "..."}\n'
    "  ],\n"
    '  "interaction_network": "...",\n'
    '  "functional_enrichment": "...",\n'
    '  "cross_database_analysis": "...",\n'
    '  "clinical_significance": "..."\n'
    "}"
)


@dataclass
class PathwayAnalysis:
    """Complete pathway analysis result."""

    query: str
    reactome_pathways: list[dict[str, object]] = field(default_factory=list)
    kegg_pathways: list[dict[str, object]] = field(default_factory=list)
    string_interactions: list[dict[str, object]] = field(default_factory=list)
    string_enrichment: list[dict[str, object]] = field(default_factory=list)
    ai_raw_response: str = ""
    sources: list[str] = field(default_factory=list)


class PathwayAnalysisEngine:
    """Engine for pathway analysis using Reactome, STRING, KEGG, and AI."""

    def __init__(
        self,
        ai_provider: AIProvider,
        reactome_client: ReactomeClient | None = None,
        string_client: StringDBClient | None = None,
        kegg_client: KEGGClient | None = None,
    ) -> None:
        self._ai = ai_provider
        self._reactome = reactome_client or ReactomeClient()
        self._string = string_client or StringDBClient()
        self._kegg = kegg_client or KEGGClient()

    async def analyze_by_gene(self, gene: str) -> PathwayAnalysis:
        """Full pathway analysis for a single gene."""
        sources: list[str] = []
        reactome_pathways: list[dict[str, object]] = []
        kegg_pathways: list[dict[str, object]] = []
        string_interactions: list[dict[str, object]] = []
        string_enrichment: list[dict[str, object]] = []

        # Reactome: search pathways for gene
        try:
            result = await self._reactome.search_pathways(gene, max_results=5)
            for pw in result.pathways:
                reactome_pathways.append({
                    "name": pw.name,
                    "st_id": pw.st_id,
                    "species": pw.species,
                })
            if reactome_pathways:
                sources.append("Reactome")
        except Exception as exc:
            logger.warning("Reactome search failed for %s: %s", gene, exc)

        # KEGG: find pathways for gene
        try:
            # Build a name lookup from full pathway list (KEGG /link/ returns IDs only)
            all_kegg = await self._kegg.list_pathways()
            kegg_name_map = {p.pathway_id: p.name for p in all_kegg}

            gene_ids = await self._kegg.find_genes("hsa", gene)
            if gene_ids:
                kegg_entry = gene_ids[0]
                kegg_pathways_raw = await self._kegg.get_pathways_for_gene(kegg_entry)
                for pw in kegg_pathways_raw[:5]:
                    name = kegg_name_map.get(pw.pathway_id, pw.name)
                    kegg_pathways.append({
                        "pathway_id": pw.pathway_id,
                        "name": name,
                    })
                if kegg_pathways:
                    sources.append("KEGG")
        except Exception as exc:
            logger.warning("KEGG search failed for %s: %s", gene, exc)

        # STRING: interaction partners + enrichment
        try:
            partners = await self._string.get_interaction_partners([gene], limit=5)
            for p in partners:
                string_interactions.append({
                    "partner": p.preferred_name_b,
                    "score": p.score,
                    "experimental": p.experimental_score,
                    "database": p.database_score,
                })
            if string_interactions:
                sources.append("STRING")

            enrichment = await self._string.get_enrichment([gene])
            for e in enrichment[:5]:
                string_enrichment.append({
                    "category": e.category,
                    "term": e.term,
                    "description": e.description,
                    "p_value": e.p_value,
                    "fdr": e.fdr,
                })
        except Exception as exc:
            logger.warning("STRING search failed for %s: %s", gene, exc)

        # AI analysis
        ai_response = ""
        if sources:
            ai_response = await self._get_ai_analysis(
                gene, reactome_pathways, kegg_pathways,
                string_interactions, string_enrichment,
            )

        return PathwayAnalysis(
            query=gene,
            reactome_pathways=reactome_pathways,
            kegg_pathways=kegg_pathways,
            string_interactions=string_interactions,
            string_enrichment=string_enrichment,
            ai_raw_response=ai_response,
            sources=sources,
        )

    async def analyze_by_gene_list(self, genes: list[str]) -> PathwayAnalysis:
        """Pathway analysis for multiple genes (network + enrichment focus)."""
        sources: list[str] = []
        string_interactions: list[dict[str, object]] = []
        string_enrichment: list[dict[str, object]] = []
        kegg_pathways: list[dict[str, object]] = []

        # STRING: network between all genes
        try:
            network = await self._string.get_network(genes, required_score=400)
            for edge in network:
                string_interactions.append({
                    "from": edge.preferred_name_a,
                    "to": edge.preferred_name_b,
                    "score": edge.score,
                })
            if string_interactions:
                sources.append("STRING")
        except Exception as exc:
            logger.warning("STRING network failed: %s", exc)

        # STRING: enrichment
        try:
            enrichment = await self._string.get_enrichment(genes)
            for e in enrichment[:10]:
                string_enrichment.append({
                    "category": e.category,
                    "term": e.term,
                    "description": e.description,
                    "p_value": e.p_value,
                    "fdr": e.fdr,
                })
        except Exception as exc:
            logger.warning("STRING enrichment failed: %s", exc)

        # KEGG: find shared pathways
        all_kegg = await self._kegg.list_pathways()
        kegg_name_map = {p.pathway_id: p.name for p in all_kegg}
        for gene in genes[:3]:
            try:
                gene_ids = await self._kegg.find_genes("hsa", gene)
                if gene_ids:
                    pws = await self._kegg.get_pathways_for_gene(gene_ids[0])
                    for pw in pws[:3]:
                        name = kegg_name_map.get(pw.pathway_id, pw.name)
                        entry: dict[str, object] = {
                            "pathway_id": pw.pathway_id,
                            "name": name,
                            "gene": gene,
                        }
                        if entry not in kegg_pathways:
                            kegg_pathways.append(entry)
            except Exception as exc:
                logger.warning("KEGG failed for %s: %s", gene, exc)
        if kegg_pathways:
            sources.append("KEGG")

        query_label = ", ".join(genes[:5])
        ai_response = ""
        if sources:
            ai_response = await self._get_ai_analysis(
                query_label, [], kegg_pathways,
                string_interactions, string_enrichment,
            )

        return PathwayAnalysis(
            query=query_label,
            kegg_pathways=kegg_pathways,
            string_interactions=string_interactions,
            string_enrichment=string_enrichment,
            ai_raw_response=ai_response,
            sources=sources,
        )

    async def _get_ai_analysis(
        self,
        query: str,
        reactome_pathways: list[dict[str, object]],
        kegg_pathways: list[dict[str, object]],
        string_interactions: list[dict[str, object]],
        string_enrichment: list[dict[str, object]],
    ) -> str:
        """Get AI analysis of pathway data."""
        prompt = (
            f"Analyze pathway data for: {query}\n\n"
            f"Reactome Pathways ({len(reactome_pathways)}):\n"
            f"{json.dumps(reactome_pathways, indent=2)}\n\n"
            f"KEGG Pathways ({len(kegg_pathways)}):\n"
            f"{json.dumps(kegg_pathways, indent=2)}\n\n"
            f"STRING Interactions ({len(string_interactions)}):\n"
            f"{json.dumps(string_interactions, indent=2)}\n\n"
            f"STRING Functional Enrichment ({len(string_enrichment)}):\n"
            f"{json.dumps(string_enrichment, indent=2)}\n\n"
            "Provide a comprehensive pathway analysis."
        )
        ai_request = AIRequest(
            prompt=prompt,
            system_prompt=PATHWAY_SYSTEM_PROMPT,
            max_tokens=4096,
            temperature=0.3,
        )
        try:
            response = await self._ai.generate(ai_request)
            return response.text
        except Exception as exc:
            logger.warning("AI analysis failed: %s", exc)
            return ""

    async def close(self) -> None:
        await self._reactome.close()
        await self._string.close()
        await self._kegg.close()
