"""ChEMBL connector — drug targets and bioactivity data."""

from __future__ import annotations

import logging

import httpx

from genomeai_api.integration.connectors.chembl.models import (
    ChEMBLBioactivity,
    ChEMBLDrug,
)

logger = logging.getLogger(__name__)

CHEMBL_API_URL = "https://www.ebi.ac.uk/chembl/api/data"


class ChEMBLClient:
    """Async ChEMBL REST client."""

    def __init__(self, timeout_seconds: float = 30.0) -> None:
        self._client = httpx.AsyncClient(
            base_url=CHEMBL_API_URL,
            timeout=httpx.Timeout(timeout_seconds),
        )

    async def search_drugs(self, query: str, max_results: int = 5) -> list[ChEMBLDrug]:
        """Search ChEMBL for drugs by name."""
        params: dict[str, str | int] = {
            "q": query,
            "limit": max_results,
            "format": "json",
        }
        try:
            response = await self._client.get("/molecule/search.json", params=params)
            response.raise_for_status()
            data: dict[str, object] = response.json()
            molecules_raw = data.get("molecules", [])
            molecules_list: list[object] = (
                molecules_raw if isinstance(molecules_raw, list) else []
            )
            drugs: list[ChEMBLDrug] = []
            for m in molecules_list:
                m_dict: dict[str, object] = m if isinstance(m, dict) else {}
                if m_dict:
                    drugs.append(self._parse_molecule(m_dict))
            return drugs
        except httpx.HTTPStatusError as exc:
            logger.warning("ChEMBL search error: %s", exc.response.status_code)
            return []

    async def get_drug(self, chembl_id: str) -> ChEMBLDrug | None:
        """Fetch a single drug by ChEMBL molecule ID."""
        try:
            response = await self._client.get(
                f"/molecule/{chembl_id}.json",
            )
            response.raise_for_status()
            data: dict[str, object] = response.json()
            molecule_raw = data.get("molecule", data)
            molecule: dict[str, object] = (
                molecule_raw if isinstance(molecule_raw, dict) else data
            )
            return self._parse_molecule(molecule)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return None
            logger.warning("ChEMBL fetch error: %s", exc.response.status_code)
            return None

    async def get_drug_activities(
        self, chembl_id: str, max_results: int = 10,
    ) -> list[ChEMBLBioactivity]:
        """Fetch bioactivity records for a drug."""
        params: dict[str, str | int] = {
            "molecule_chembl_id": chembl_id,
            "limit": max_results,
            "format": "json",
        }
        try:
            response = await self._client.get("/activity.json", params=params)
            response.raise_for_status()
            data: dict[str, object] = response.json()
            activities_raw = data.get("activities", [])
            activities_list: list[object] = (
                activities_raw if isinstance(activities_raw, list) else []
            )
            results: list[ChEMBLBioactivity] = []
            for a in activities_list:
                a_dict: dict[str, object] = a if isinstance(a, dict) else {}
                if a_dict:
                    results.append(self._parse_activity(a_dict))
            return results
        except httpx.HTTPStatusError as exc:
            logger.warning("ChEMBL activities error: %s", exc.response.status_code)
            return []

    def _parse_molecule(self, data: dict[str, object]) -> ChEMBLDrug:
        mol_id_raw = data.get("molecule_chembl_id", "")
        mol_id = str(mol_id_raw) if isinstance(mol_id_raw, str) else ""
        name_raw = data.get("pref_name", "")
        name = str(name_raw) if isinstance(name_raw, str) else ""
        mol_type_raw = data.get("molecule_type", "")
        mol_type = str(mol_type_raw) if isinstance(mol_type_raw, str) else ""
        max_phase_raw = data.get("max_phase", 0)
        max_phase = int(max_phase_raw) if isinstance(max_phase_raw, (int, float)) else 0
        smiles_raw = data.get("molecule_structures", {})
        smiles_dict: dict[str, object] = (
            smiles_raw if isinstance(smiles_raw, dict) else {}
        )
        smiles_raw_val = smiles_dict.get("canonical_smiles", "")
        smiles = str(smiles_raw_val) if isinstance(smiles_raw_val, str) else ""

        return ChEMBLDrug(
            molecule_chembl_id=mol_id,
            name=name,
            molecule_type=mol_type,
            max_phase=max_phase,
            smiles=smiles,
            pref_name=name,
        )

    def _parse_activity(self, data: dict[str, object]) -> ChEMBLBioactivity:
        act_id_raw = data.get("activity_id", "")
        act_id = str(act_id_raw) if isinstance(act_id_raw, str) else ""
        target_raw = data.get("target_pref_name", "")
        target_name = str(target_raw) if isinstance(target_raw, str) else ""
        assay_raw = data.get("assay_type", "")
        assay_type = str(assay_raw) if isinstance(assay_raw, str) else ""
        std_type_raw = data.get("standard_type", "")
        std_type = str(std_type_raw) if isinstance(std_type_raw, str) else ""
        std_val_raw = data.get("standard_value", 0)
        std_val = float(std_val_raw) if isinstance(std_val_raw, (int, float)) else 0.0
        std_units_raw = data.get("standard_units", "")
        std_units = str(std_units_raw) if isinstance(std_units_raw, str) else ""
        std_rel_raw = data.get("standard_relation", "")
        std_rel = str(std_rel_raw) if isinstance(std_rel_raw, str) else ""
        pchembl_raw = data.get("pchembl_value", 0)
        pchembl = float(pchembl_raw) if isinstance(pchembl_raw, (int, float)) else 0.0

        return ChEMBLBioactivity(
            activity_id=act_id,
            target_name=target_name,
            assay_type=assay_type,
            standard_type=std_type,
            standard_value=std_val,
            standard_units=std_units,
            standard_relation=std_rel,
            pchembl_value=pchembl,
        )

    async def health_check(self) -> bool:
        try:
            response = await self._client.get(
                "/molecule/CHEMBL25.json",
            )
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        await self._client.aclose()
