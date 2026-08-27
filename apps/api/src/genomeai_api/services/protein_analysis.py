"""Protein analysis engine — AI-powered protein analysis.

Pipeline: UniProt (sequence/function) + PDB (3D structure) +
AlphaFold (predicted structure) + Gemini (AI analysis).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from genomeai_api.ai.base import AIProvider, AIRequest
from genomeai_api.integration.connectors.alphafold.client import AlphaFoldClient
from genomeai_api.integration.connectors.alphafold.models import AlphaFoldStructure
from genomeai_api.integration.connectors.pdb.client import PDBClient
from genomeai_api.integration.connectors.pdb.models import PDBStructure
from genomeai_api.integration.connectors.uniprot.client import UniProtClient
from genomeai_api.integration.connectors.uniprot.models import UniProtProtein

logger = logging.getLogger(__name__)

PROTEIN_SYSTEM_PROMPT = """You are a protein bioinformatics expert.
Analyze the provided protein data and return a structured analysis.
Always respond in valid JSON format:
{
  "function_summary": "Brief description of protein function",
  "domains": ["List of key protein domains"],
  "clinical_significance": "Clinical relevance if any",
  "drug_targets": ["Known drug targets or interactions"],
  "disease_associations": ["Associated diseases"],
  "structural_notes": "Notes on protein structure",
  "summary": "Brief overall summary"
}"""


@dataclass
class ProteinAnalysis:
    """Structured protein analysis result."""

    protein_name: str = ""
    accession: str = ""
    gene_names: list[str] = field(default_factory=list)
    organism: str = ""
    length: int = 0
    function: str = ""
    subcellular_location: str = ""
    pdb_structures: list[PDBStructure] = field(default_factory=list)
    alphafold: AlphaFoldStructure | None = None
    function_summary: str = ""
    domains: list[str] = field(default_factory=list)
    clinical_significance: str = ""
    drug_targets: list[str] = field(default_factory=list)
    disease_associations: list[str] = field(default_factory=list)
    structural_notes: str = ""
    summary: str = ""
    ai_raw_response: str = ""
    data_sources: list[str] = field(default_factory=list)


class ProteinAnalysisEngine:
    """AI-powered protein analysis using UniProt + PDB + AlphaFold + Gemini."""

    def __init__(
        self,
        ai_provider: AIProvider,
        uniprot_client: UniProtClient | None = None,
        pdb_client: PDBClient | None = None,
        alphafold_client: AlphaFoldClient | None = None,
    ) -> None:
        self._ai = ai_provider
        self._uniprot = uniprot_client or UniProtClient()
        self._pdb = pdb_client or PDBClient()
        self._alphafold = alphafold_client or AlphaFoldClient()

    async def analyze_by_gene(
        self, gene: str,
    ) -> ProteinAnalysis:
        """Analyze a protein by gene name."""
        proteins = await self._uniprot.search(gene, max_results=5)
        if not proteins:
            raise ValueError(f"Protein for gene '{gene}' not found in UniProt")
        best = proteins[0]
        gene_upper = gene.upper()
        for p in proteins:
            if any(g.upper() == gene_upper for g in p.gene_names):
                best = p
                break
            if gene_upper in p.protein_name.upper():
                best = p
                break
        return await self._analyze_protein(best)

    async def analyze_by_accession(
        self, accession: str,
    ) -> ProteinAnalysis:
        """Analyze a protein by UniProt accession."""
        protein = await self._uniprot.get_protein(accession)
        if not protein:
            raise ValueError(f"Protein '{accession}' not found in UniProt")
        return await self._analyze_protein(protein)

    async def _analyze_protein(
        self, protein: UniProtProtein,
    ) -> ProteinAnalysis:
        sources = ["UniProt"]

        pdb_structures: list[PDBStructure] = []
        if protein.pdb_ids:
            for pid in protein.pdb_ids[:3]:
                try:
                    struct = await self._pdb.get_structure(pid)
                    if struct:
                        pdb_structures.append(struct)
                except Exception as exc:
                    logger.warning("PDB lookup failed for %s: %s", pid, exc)
            if pdb_structures:
                sources.append("PDB")

        alphafold_struct = None
        if protein.accession:
            try:
                alphafold_struct = await self._alphafold.get_prediction(
                    protein.accession,
                )
                if alphafold_struct:
                    sources.append("AlphaFold")
            except Exception as exc:
                logger.warning("AlphaFold lookup failed: %s", exc)

        prompt = self._build_prompt(protein, pdb_structures, alphafold_struct)
        ai_request = AIRequest(
            prompt=prompt,
            system_prompt=PROTEIN_SYSTEM_PROMPT,
            max_tokens=1024,
            temperature=0.3,
        )

        try:
            ai_response = await self._ai.generate(ai_request)
            parsed = self._parse_ai_response(ai_response.text)
        except Exception as exc:
            logger.warning("AI analysis failed: %s", exc)
            parsed = self._basic_analysis(protein)

        raw_domains = parsed.get("domains", [])
        domains: list[str] = (
            [str(d) for d in raw_domains if isinstance(d, str)]
            if isinstance(raw_domains, list)
            else []
        )
        raw_drugs = parsed.get("drug_targets", [])
        drug_targets: list[str] = (
            [str(d) for d in raw_drugs if isinstance(d, str)]
            if isinstance(raw_drugs, list)
            else []
        )
        raw_diseases = parsed.get("disease_associations", [])
        disease_assoc: list[str] = (
            [str(d) for d in raw_diseases if isinstance(d, str)]
            if isinstance(raw_diseases, list)
            else []
        )

        return ProteinAnalysis(
            protein_name=protein.protein_name,
            accession=protein.accession,
            gene_names=protein.gene_names,
            organism=protein.organism,
            length=protein.length,
            function=protein.function,
            subcellular_location=protein.subcellular_location,
            pdb_structures=pdb_structures,
            alphafold=alphafold_struct,
            function_summary=str(parsed.get("function_summary", "")),
            domains=domains,
            clinical_significance=str(parsed.get("clinical_significance", "")),
            drug_targets=drug_targets,
            disease_associations=disease_assoc,
            structural_notes=str(parsed.get("structural_notes", "")),
            summary=str(parsed.get("summary", "")),
            ai_raw_response=json.dumps(parsed),
            data_sources=sources,
        )

    def _build_prompt(
        self,
        protein: UniProtProtein,
        pdb: list[PDBStructure],
        alphafold: AlphaFoldStructure | None,
    ) -> str:
        parts = [
            "Analyze the following protein:",
            "",
            f"Gene: {', '.join(protein.gene_names)}",
            f"Protein: {protein.protein_name}",
            f"Accession: {protein.accession}",
            f"Organism: {protein.organism}",
            f"Length: {protein.length} aa",
            f"Function: {protein.function}",
            f"Subcellular location: {protein.subcellular_location}",
            f"Keywords: {', '.join(protein.keywords[:10])}",
        ]
        if pdb:
            parts.append("")
            parts.append("Known 3D Structures (PDB):")
            for s in pdb[:3]:
                parts.append(
                    f"  {s.pdb_id}: {s.title[:80]} ({s.method}, {s.resolution}A)"
                )
        if alphafold:
            parts.extend([
                "",
                "AlphaFold Prediction:",
                f"  ID: {alphafold.alphafold_id}",
                f"  Length: {alphafold.sequence_length} aa",
            ])
        parts.extend([
            "",
            "Provide functional analysis, domain information, clinical "
            "significance, drug targets, and disease associations.",
        ])
        return "\n".join(parts)

    def _parse_ai_response(self, response_text: str) -> dict[str, object]:
        try:
            cleaned = response_text.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                lines = [ln for ln in lines if not ln.startswith("```")]
                cleaned = "\n".join(lines)
            data = json.loads(cleaned)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
        return {"summary": response_text}

    def _basic_analysis(
        self, protein: UniProtProtein,
    ) -> dict[str, object]:
        return {
            "function_summary": protein.function[:200] if protein.function else "",
            "summary": f"{protein.protein_name} ({protein.accession}) - {protein.organism}",
        }

    async def close(self) -> None:
        await self._uniprot.close()
        await self._pdb.close()
        await self._alphafold.close()
