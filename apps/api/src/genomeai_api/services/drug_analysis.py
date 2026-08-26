"""Drug analysis engine — ChEMBL + PubChem + Gemini AI."""

from __future__ import annotations

import logging

from genomeai_api.ai.base import AIProvider, AIRequest
from genomeai_api.integration.connectors.chembl.client import ChEMBLClient
from genomeai_api.integration.connectors.chembl.models import ChEMBLDrug
from genomeai_api.integration.connectors.pubchem.client import PubChemClient
from genomeai_api.integration.connectors.pubchem.models import PubChemCompound

logger = logging.getLogger(__name__)

DRUG_ANALYSIS_PROMPT = """\
You are a pharmacogenomics analyst. Analyze the following drug information and \
provide a structured report.

Drug data:
{drug_data}

Provide:
1. Drug classification and mechanism of action
2. Key pharmacological properties
3. Clinical applications and indications
4. Known drug-gene interactions relevant to genomics
5. Safety considerations based on pharmacogenomics

Respond in JSON format:
{{
  "drug_name": "...",
  "classification": "...",
  "mechanism": "...",
  "pharmacogenomic_relevance": "...",
  "clinical_applications": ["..."],
  "drug_gene_interactions": ["..."],
  "safety_notes": "..."
}}
"""


class DrugAnalysisEngine:
    """Drug analysis engine combining ChEMBL + PubChem + AI."""

    def __init__(self, ai_provider: AIProvider) -> None:
        self._chembl = ChEMBLClient()
        self._pubchem = PubChemClient()
        self._ai = ai_provider

    async def search(self, query: str) -> dict[str, object]:
        """Search ChEMBL + PubChem for drug information."""
        chembl_drugs = await self._chembl.search_drugs(query, max_results=3)
        pubchem_compound = await self._pubchem.search_by_name(query)

        results: dict[str, object] = {
            "query": query,
            "chembl_drugs": [self._chembl_to_dict(d) for d in chembl_drugs],
            "pubchem_compound": (
                self._pubchem_to_dict(pubchem_compound)
                if pubchem_compound
                else None
            ),
        }
        return results

    async def analyze(self, query: str) -> dict[str, object]:
        """Search and analyze drug with AI."""
        search_results = await self.search(query)
        drug_data_parts: list[str] = []

        raw_chembl = search_results.get("chembl_drugs", [])
        if isinstance(raw_chembl, list):
            for d in raw_chembl:
                d_dict: dict[str, object] = d if isinstance(d, dict) else {}
                if d_dict:
                    drug_data_parts.append(self._chembl_to_str(d_dict))

        raw_pubchem = search_results.get("pubchem_compound")
        pc_dict: dict[str, object] = (
            raw_pubchem if isinstance(raw_pubchem, dict) else {}
        )
        if pc_dict:
            drug_data_parts.append(self._pubchem_to_str(pc_dict))

        if not drug_data_parts:
            return {"error": "No drug data found", "analysis": None}

        drug_data = "\n\n".join(drug_data_parts)
        prompt = DRUG_ANALYSIS_PROMPT.format(drug_data=drug_data)
        ai_request = AIRequest(prompt=prompt)

        try:
            ai_response = await self._ai.generate(ai_request)
        except Exception as exc:
            logger.warning("AI analysis failed: %s", exc)
            return {
                "query": query,
                "ai_analysis": None,
                "error": str(exc),
            }

        return {
            "query": query,
            "ai_analysis": ai_response.text,
        }

    def _chembl_to_dict(self, drug: ChEMBLDrug) -> dict[str, object]:
        return {
            "molecule_chembl_id": drug.molecule_chembl_id,
            "name": drug.name,
            "molecule_type": drug.molecule_type,
            "max_phase": drug.max_phase,
            "smiles": drug.smiles,
            "source": "chembl",
        }

    def _pubchem_to_dict(self, compound: PubChemCompound) -> dict[str, object]:
        return {
            "cid": compound.cid,
            "name": compound.name,
            "molecular_formula": compound.molecular_formula,
            "molecular_weight": compound.molecular_weight,
            "iupac_name": compound.iupac_name,
            "canonical_smiles": compound.canonical_smiles,
            "description": compound.description[:500] if compound.description else "",
            "source": "pubchem",
        }

    def _chembl_to_str(self, drug: dict[str, object]) -> str:
        name = str(drug.get("name", ""))
        mol_id = str(drug.get("molecule_chembl_id", ""))
        smiles = str(drug.get("smiles", ""))
        return f"ChEMBL Drug: {name} ({mol_id})\nSMILES: {smiles}"

    def _pubchem_to_str(self, compound: dict[str, object]) -> str:
        name = str(compound.get("name", ""))
        formula = str(compound.get("molecular_formula", ""))
        mw = str(compound.get("molecular_weight", ""))
        desc = str(compound.get("description", ""))
        return f"PubChem Compound: {name}\nFormula: {formula}\nMW: {mw}\nDescription: {desc}"

    async def close(self) -> None:
        await self._chembl.close()
        await self._pubchem.close()
