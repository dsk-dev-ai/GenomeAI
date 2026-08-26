"""Variant interpretation engine — AI-powered variant analysis.

Pipeline: ClinVar (clinical significance) + gnomAD (population frequency) +
Ensembl VEP (computational predictions) + Ollama (AI interpretation).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from genomeai_api.ai.base import AIProvider, AIRequest
from genomeai_api.integration.connectors.clinvar.client import ClinVarClient
from genomeai_api.integration.connectors.clinvar.models import ClinVarRecord
from genomeai_api.integration.connectors.ensembl_vep.client import EnsemblVEPClient
from genomeai_api.integration.connectors.ensembl_vep.models import VEPResult
from genomeai_api.integration.connectors.gnomad.client import GnomADClient
from genomeai_api.integration.connectors.gnomad.models import GnomADVariant

logger = logging.getLogger(__name__)

VARIANT_SYSTEM_PROMPT = """You are a clinical genomics variant interpreter.
Analyze the provided variant data and return a structured interpretation.
Always respond in valid JSON format:
{
  "pathogenicity": "Pathogenic|Likely pathogenic|Uncertain significance|Likely benign|Benign",
  "acmg_criteria": ["List of ACMG criteria applied"],
  "reasoning": "Detailed reasoning for the classification",
  "clinical_actionability": "What clinical actions are recommended",
  "summary": "Brief summary of the variant interpretation"
}"""


@dataclass
class VariantInterpretation:
    """Structured variant interpretation result."""

    variant_description: str = ""
    gene_symbol: str = ""
    clinvar: ClinVarRecord | None = None
    gnomad: GnomADVariant | None = None
    vep: VEPResult | None = None
    pathogenicity: str = ""
    acmg_criteria: list[str] = field(default_factory=list)
    reasoning: str = ""
    clinical_actionability: str = ""
    summary: str = ""
    ai_raw_response: str = ""
    data_sources: list[str] = field(default_factory=list)


class VariantInterpretationEngine:
    """AI-powered variant interpretation using ClinVar + gnomAD + VEP + Ollama."""

    def __init__(
        self,
        ai_provider: AIProvider,
        clinvar_client: ClinVarClient | None = None,
        gnomad_client: GnomADClient | None = None,
        vep_client: EnsemblVEPClient | None = None,
    ) -> None:
        self._ai = ai_provider
        self._clinvar = clinvar_client or ClinVarClient()
        self._gnomad = gnomad_client or GnomADClient()
        self._vep = vep_client or EnsemblVEPClient()

    async def interpret_by_gene(
        self,
        gene: str,
        max_variants: int = 5,
    ) -> list[VariantInterpretation]:
        """Find and interpret pathogenic variants for a gene."""
        clinvar_records = await self._clinvar.search_variants(
            gene=gene,
            significance="pathogenic",
            max_results=max_variants,
        )
        results = []
        for record in clinvar_records:
            interpretation = await self._interpret_clinvar_record(record)
            results.append(interpretation)
        return results

    async def interpret_by_clinvar_id(
        self,
        clinvar_id: str,
    ) -> VariantInterpretation:
        """Interpret a specific ClinVar record."""
        record = await self._clinvar.get_variant(clinvar_id)
        if not record:
            raise ValueError(f"ClinVar record '{clinvar_id}' not found")
        return await self._interpret_clinvar_record(record)

    async def interpret_by_variant(
        self,
        gene: str,
        hgvs_c: str,
    ) -> VariantInterpretation:
        """Interpret a variant by gene + HGVS notation."""
        clinvar_records = await self._clinvar.search_variants(
            gene=gene,
            max_results=50,
        )
        matching = None
        for record in clinvar_records:
            if hgvs_c and hgvs_c in (record.hgvs_c or ""):
                matching = record
                break
        if matching:
            return await self._interpret_clinvar_record(matching)

        fake_record = ClinVarRecord(
            clinvar_id="",
            gene_symbol=gene,
            clinical_significance="Unknown",
            hgvs_c=hgvs_c,
        )
        return await self._interpret_clinvar_record(fake_record)

    async def _interpret_clinvar_record(
        self,
        record: ClinVarRecord,
    ) -> VariantInterpretation:
        """Interpret a ClinVar record with gnomAD + VEP + AI."""
        sources = ["ClinVar"]

        gnomad_variant = None
        if record.chromosome and record.start and record.ref_allele and record.alt_allele:
            vid = f"{record.chromosome}-{record.start}-{record.ref_allele}-{record.alt_allele}"
            try:
                gnomad_variant = await self._gnomad.get_variant(vid)
                if gnomad_variant:
                    sources.append("gnomAD")
            except Exception as exc:
                logger.warning("gnomAD lookup failed: %s", exc)

        vep_result = None
        if record.hgvs_c:
            try:
                vep_result = await self._vep.predict_hgvs(record.hgvs_c)
                if vep_result:
                    sources.append("Ensembl VEP")
            except Exception as exc:
                logger.warning("VEP lookup failed: %s", exc)

        prompt = self._build_prompt(record, gnomad_variant, vep_result)
        ai_request = AIRequest(
            prompt=prompt,
            system_prompt=VARIANT_SYSTEM_PROMPT,
            max_tokens=1024,
            temperature=0.3,
        )

        try:
            ai_response = await self._ai.generate(ai_request)
            parsed = self._parse_ai_response(ai_response.text)
        except Exception as exc:
            logger.warning("AI interpretation failed: %s", exc)
            parsed = self._basic_interpretation(record)

        variant_desc = f"{record.gene_symbol} {record.hgvs_c or ''}"
        return VariantInterpretation(
            variant_description=variant_desc.strip(),
            gene_symbol=record.gene_symbol,
            clinvar=record,
            gnomad=gnomad_variant,
            vep=vep_result,
            pathogenicity=parsed.get("pathogenicity", record.clinical_significance),
            acmg_criteria=parsed.get("acmg_criteria", []),
            reasoning=parsed.get("reasoning", ""),
            clinical_actionability=parsed.get("clinical_actionability", ""),
            summary=parsed.get("summary", ""),
            ai_raw_response=json.dumps(parsed),
            data_sources=sources,
        )

    def _build_prompt(
        self,
        record: ClinVarRecord,
        gnomad: GnomADVariant | None,
        vep: VEPResult | None,
    ) -> str:
        parts = [
            "Interpret the following variant based on the provided data:",
            "",
            f"Gene: {record.gene_symbol}",
            f"ClinVar ID: {record.clinvar_id}",
            f"Clinical Significance: {record.clinical_significance}",
            f"Review Status: {record.review_status}",
            f"Condition: {record.condition}",
            f"HGVS cDNA: {record.hgvs_c}",
            f"HGVS Protein: {record.hgvs_p}",
        ]
        if gnomad:
            af = gnomad.genome_af or gnomad.exome_af
            parts.extend([
                "",
                "Population Frequency (gnomAD):",
                f"  Allele Frequency: {af:.6f}",
                f"  Allele Count: {gnomad.genome_ac or gnomad.exome_ac}",
                f"  Allele Number: {gnomad.genome_an or gnomad.exome_an}",
            ])
        if vep and vep.consequences:
            c = vep.consequences[0]
            parts.extend([
                "",
                "Computational Predictions (VEP):",
                f"  Consequence: {', '.join(c.consequence_terms)}",
                f"  Impact: {c.impact}",
                f"  SIFT: {c.sift_prediction} ({c.sift_score})"
                if c.sift_score is not None else "",
                f"  PolyPhen: {c.polyphen_prediction}"
                f" ({c.polyphen_score})"
                if c.polyphen_score is not None else "",
            ])
        parts.extend([
            "",
            "Apply ACMG criteria and provide pathogenicity classification.",
        ])
        return "\n".join(parts)

    def _parse_ai_response(self, response_text: str) -> dict[str, object]:
        try:
            data = json.loads(response_text)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
        return {"summary": response_text}

    def _basic_interpretation(
        self, record: ClinVarRecord,
    ) -> dict[str, object]:
        sig = record.clinical_significance
        summary = record.summary or (
            f"{record.gene_symbol} variant classified as {sig}"
        )
        return {
            "pathogenicity": sig,
            "reasoning": f"ClinVar classified as {sig}",
            "summary": summary,
        }

    async def close(self) -> None:
        await self._clinvar.close()
        await self._gnomad.close()
        await self._vep.close()
