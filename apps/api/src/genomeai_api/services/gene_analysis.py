"""Gene analysis engine — AI-powered gene analysis using real data.

Pipeline: fetch gene from NCBI → analyze with Ollama → return structured analysis.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from genomeai_api.ai.base import AIProvider, AIRequest
from genomeai_api.integration.connectors.ncbi.client import NCBIClient
from genomeai_api.integration.connectors.ncbi.models import NCBIGeneRecord

logger = logging.getLogger(__name__)

GENE_ANALYSIS_SYSTEM_PROMPT = """You are a genomics research assistant.
Analyze the provided gene data and return a structured analysis.
Always respond in valid JSON format with the following fields:
{
  "function": "What this gene does",
  "key_variants": ["List of important variants"],
  "associated_diseases": ["Diseases linked to this gene"],
  "drug_targets": ["Drugs targeting this gene or its products"],
  "clinical_significance": "Why this gene matters clinically",
  "summary": "Brief 2-3 sentence summary"
}"""


@dataclass
class GeneAnalysis:
    """Structured gene analysis result."""

    gene_symbol: str
    gene_id: str
    name: str
    organism: str = ""
    chromosome: str = ""
    map_location: str = ""
    description: str = ""
    aliases: list[str] = field(default_factory=list)
    gene_type: str = ""
    function: str = ""
    key_variants: list[str] = field(default_factory=list)
    associated_diseases: list[str] = field(default_factory=list)
    drug_targets: list[str] = field(default_factory=list)
    clinical_significance: str = ""
    summary: str = ""
    ai_raw_response: str = ""
    source: str = "ncbi"


class GeneAnalysisEngine:
    """AI-powered gene analysis using NCBI data + LLM."""

    def __init__(
        self,
        ai_provider: AIProvider,
        ncbi_client: NCBIClient | None = None,
        close_ai_provider: bool = True,
    ) -> None:
        self._ai = ai_provider
        self._ncbi = ncbi_client or NCBIClient()
        self._close_ai_provider = close_ai_provider

    async def analyze_by_symbol(
        self,
        symbol: str,
        organism: str = "Homo sapiens",
    ) -> GeneAnalysis:
        """Analyze a gene by its symbol (e.g., "BRCA1").

        Fetches real data from NCBI, then analyzes with AI.
        """
        records = await self._ncbi.search_genes(
            query=symbol,
            organism=organism,
            max_results=1,
        )
        if not records:
            raise ValueError(f"Gene '{symbol}' not found in NCBI")

        return await self.analyze_from_record(records[0])

    async def analyze_by_id(self, gene_id: str) -> GeneAnalysis:
        """Analyze a gene by NCBI Gene ID (e.g., "672" for BRCA1)."""
        record = await self._ncbi.get_gene(gene_id)
        if not record:
            raise ValueError(f"Gene with ID '{gene_id}' not found in NCBI")
        return await self.analyze_from_record(record)

    async def analyze_from_record(self, record: NCBIGeneRecord) -> GeneAnalysis:
        """Analyze a gene from an existing NCBIGeneRecord."""
        prompt = self._build_prompt(record)
        ai_request = AIRequest(
            prompt=prompt,
            system_prompt=GENE_ANALYSIS_SYSTEM_PROMPT,
            max_tokens=4096,
            temperature=0.3,
        )

        try:
            ai_response = await self._ai.generate(ai_request)
            analysis = self._parse_ai_response(ai_response.text, record)
        except Exception as exc:
            logger.warning("AI analysis failed, using basic analysis: %s", exc)
            analysis = self._basic_analysis(record)

        return analysis

    def _build_prompt(self, record: NCBIGeneRecord) -> str:
        """Build analysis prompt from gene record."""
        parts = [
            "Analyze the following gene based on the provided data:",
            "",
            f"Gene Symbol: {record.symbol}",
            f"Full Name: {record.name}",
            f"Gene ID: {record.gene_id}",
            f"Organism: {record.organism}",
            f"Chromosome: {record.chromosome}",
            f"Map Location: {record.map_location}",
            f"Gene Type: {record.gene_type}",
            f"Description: {record.description}",
        ]
        if record.aliases:
            parts.append(f"Aliases: {', '.join(record.aliases)}")
        parts.append("")
        parts.append(
            "Provide a structured analysis including function, key variants, "
            "associated diseases, drug targets, clinical significance, and summary."
        )
        return "\n".join(parts)

    def _parse_ai_response(
        self,
        response_text: str,
        record: NCBIGeneRecord,
    ) -> GeneAnalysis:
        """Parse AI JSON response into GeneAnalysis.

        Gemini 3.x models may wrap the JSON in markdown code fences and can
        truncate the output at max_tokens, so we strip fences first and then
        salvage the best complete JSON object if strict parsing fails.
        """
        data: dict[str, Any] = {}
        if response_text:
            data = self._extract_json_dict(response_text)

        if not data:
            return self._basic_analysis(record)

        function_val = str(data.get("function", ""))
        key_variants_val: list[str] = []
        if isinstance(data.get("key_variants"), list):
            key_variants_val = [str(v) for v in data["key_variants"]]
        diseases_val: list[str] = []
        if isinstance(data.get("associated_diseases"), list):
            diseases_val = [str(d) for d in data["associated_diseases"]]
        drugs_val: list[str] = []
        if isinstance(data.get("drug_targets"), list):
            drugs_val = [str(d) for d in data["drug_targets"]]
        clinical_val = str(data.get("clinical_significance", ""))
        summary_val = str(data.get("summary", ""))

        return GeneAnalysis(
            gene_symbol=record.symbol,
            gene_id=record.gene_id,
            name=record.name,
            organism=record.organism,
            chromosome=record.chromosome,
            map_location=record.map_location,
            description=record.description,
            aliases=record.aliases,
            gene_type=record.gene_type,
            function=function_val,
            key_variants=key_variants_val,
            associated_diseases=diseases_val,
            drug_targets=drugs_val,
            clinical_significance=clinical_val,
            summary=summary_val,
            ai_raw_response=response_text,
            source="ncbi+ollama",
        )

    @staticmethod
    def _extract_json_dict(response_text: str) -> dict[str, Any]:
        """Extract the best-possible JSON object from an AI response.

        Handles markdown code fences (```json ... ```) and JSON truncated by
        max_tokens. Returns {} if nothing usable is found.
        """
        import json

        text = response_text.strip()

        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(
                ln for ln in lines if not ln.strip().startswith("```")
            )

        start = text.find("{")
        if start == -1:
            return {}
        candidate = text[start:]

        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        # Truncated JSON: try increasingly shorter prefixes, cutting only at
        # positions that could end a complete value ('}' or '"'), bounded scan.
        # A cut may leave the object unclosed, so try appending a closing "}".
        checked = 0
        for i in range(len(candidate) - 1, -1, -1):
            if candidate[i] not in '}"':
                continue
            checked += 1
            if checked > 64:
                break
            for attempt in (candidate[: i + 1], candidate[: i + 1] + "}"):
                if not attempt.endswith("}"):
                    continue
                try:
                    parsed = json.loads(attempt)
                    if isinstance(parsed, dict):
                        return parsed
                except (json.JSONDecodeError, RecursionError):
                    continue

        return {}

    def _basic_analysis(self, record: NCBIGeneRecord) -> GeneAnalysis:
        """Fallback analysis without AI."""
        return GeneAnalysis(
            gene_symbol=record.symbol,
            gene_id=record.gene_id,
            name=record.name,
            organism=record.organism,
            chromosome=record.chromosome,
            map_location=record.map_location,
            description=record.description,
            aliases=record.aliases,
            gene_type=record.gene_type,
            summary=record.description or record.name,
            source="ncbi",
        )

    async def close(self) -> None:
        """Release resources."""
        await self._ncbi.close()
        if self._close_ai_provider:
            await self._ai.close()
