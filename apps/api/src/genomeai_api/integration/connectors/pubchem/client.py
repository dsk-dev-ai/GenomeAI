"""PubChem connector — compound data and drug information."""

from __future__ import annotations

import logging

import httpx

from genomeai_api.integration.connectors.pubchem.models import PubChemCompound

logger = logging.getLogger(__name__)

PUBCHEM_API_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"


class PubChemClient:
    """Async PubChem REST client."""

    def __init__(self, timeout_seconds: float = 30.0) -> None:
        self._client = httpx.AsyncClient(
            base_url=PUBCHEM_API_URL,
            timeout=httpx.Timeout(timeout_seconds),
        )

    async def search_by_name(self, name: str) -> PubChemCompound | None:
        """Search PubChem compound by name."""
        try:
            response = await self._client.get(
                f"/compound/name/{name}/property/"
                "MolecularFormula,MolecularWeight,IUPACName,"
                "CanonicalSMILES,InChI,XLogP,"
                "HBondDonorCount,HBondAcceptorCount/JSON",
            )
            response.raise_for_status()
            data: dict[str, object] = response.json()
            props = data.get("PropertyTable", {})
            props_dict: dict[str, object] = (
                props if isinstance(props, dict) else {}
            )
            compounds_raw = props_dict.get("Properties", [])
            compounds_list: list[object] = (
                compounds_raw if isinstance(compounds_raw, list) else []
            )
            if compounds_list:
                first: dict[str, object] = (
                    compounds_list[0] if isinstance(compounds_list[0], dict) else {}
                )
                if first:
                    compound = self._parse_compound(first)
                    desc = await self._get_description(str(first.get("CID", "")))
                    return PubChemCompound(
                        cid=compound.cid,
                        name=name,
                        molecular_formula=compound.molecular_formula,
                        molecular_weight=compound.molecular_weight,
                        iupac_name=compound.iupac_name,
                        canonical_smiles=compound.canonical_smiles,
                        inchi=compound.inchi,
                        xlogp=compound.xlogp,
                        hydrogen_bond_donor_count=compound.hydrogen_bond_donor_count,
                        hydrogen_bond_acceptor_count=compound.hydrogen_bond_acceptor_count,
                        description=desc,
                    )
            return None
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return None
            logger.warning("PubChem search error: %s", exc.response.status_code)
            return None

    async def get_compound(self, cid: int) -> PubChemCompound | None:
        """Fetch a compound by PubChem CID."""
        try:
            response = await self._client.get(
                f"/compound/cid/{cid}/property/"
                "MolecularFormula,MolecularWeight,IUPACName,"
                "CanonicalSMILES,InChI,XLogP,"
                "HBondDonorCount,HBondAcceptorCount/JSON",
            )
            response.raise_for_status()
            data: dict[str, object] = response.json()
            props = data.get("PropertyTable", {})
            props_dict: dict[str, object] = (
                props if isinstance(props, dict) else {}
            )
            compounds_raw = props_dict.get("Properties", [])
            compounds_list: list[object] = (
                compounds_raw if isinstance(compounds_raw, list) else []
            )
            if compounds_list:
                first: dict[str, object] = (
                    compounds_list[0] if isinstance(compounds_list[0], dict) else {}
                )
                if first:
                    compound = self._parse_compound(first)
                    desc = await self._get_description(str(cid))
                    return PubChemCompound(
                        cid=compound.cid,
                        name=compound.iupac_name,
                        molecular_formula=compound.molecular_formula,
                        molecular_weight=compound.molecular_weight,
                        iupac_name=compound.iupac_name,
                        canonical_smiles=compound.canonical_smiles,
                        inchi=compound.inchi,
                        xlogp=compound.xlogp,
                        hydrogen_bond_donor_count=compound.hydrogen_bond_donor_count,
                        hydrogen_bond_acceptor_count=compound.hydrogen_bond_acceptor_count,
                        description=desc,
                    )
            return None
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return None
            logger.warning("PubChem fetch error: %s", exc.response.status_code)
            return None

    async def _get_description(self, cid: str) -> str:
        """Get compound description from PubChem."""
        if not cid:
            return ""
        try:
            response = await self._client.get(
                f"/compound/cid/{cid}/description/JSON",
            )
            response.raise_for_status()
            data: dict[str, object] = response.json()
            info_list_raw = data.get("InformationList", {})
            info_list_dict: dict[str, object] = (
                info_list_raw if isinstance(info_list_raw, dict) else {}
            )
            info_raw = info_list_dict.get("Information", [])
            info_list: list[object] = (
                info_raw if isinstance(info_raw, list) else []
            )
            for info in info_list:
                info_dict: dict[str, object] = (
                    info if isinstance(info, dict) else {}
                )
                desc_raw = info_dict.get("Description", "")
                desc = str(desc_raw) if isinstance(desc_raw, str) else ""
                if desc and len(desc) > 50:
                    return desc[:500]
            return ""
        except Exception:
            return ""

    async def health_check(self) -> bool:
        try:
            response = await self._client.get(
                "/compound/cid/2244/property/MolecularFormula/JSON",
            )
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        await self._client.aclose()

    def _parse_compound(self, data: dict[str, object]) -> PubChemCompound:
        cid_raw = data.get("CID", 0)
        cid = int(cid_raw) if isinstance(cid_raw, (int, float)) else 0
        formula_raw = data.get("MolecularFormula", "")
        formula = str(formula_raw) if isinstance(formula_raw, str) else ""
        mw_raw = data.get("MolecularWeight", 0)
        if isinstance(mw_raw, str):
            mw = float(mw_raw) if mw_raw else 0.0
        else:
            mw = float(mw_raw) if isinstance(mw_raw, (int, float)) else 0.0
        iupac_raw = data.get("IUPACName", "")
        iupac = str(iupac_raw) if isinstance(iupac_raw, str) else ""
        smiles_raw = data.get("CanonicalSMILES", "")
        smiles = str(smiles_raw) if isinstance(smiles_raw, str) else ""
        inchi_raw = data.get("InChI", "")
        inchi = str(inchi_raw) if isinstance(inchi_raw, str) else ""
        xlogp_raw = data.get("XLogP", 0)
        if isinstance(xlogp_raw, str):
            xlogp = float(xlogp_raw) if xlogp_raw else 0.0
        else:
            xlogp = float(xlogp_raw) if isinstance(xlogp_raw, (int, float)) else 0.0
        hbd_raw = data.get("HBondDonorCount", 0)
        hbd = int(hbd_raw) if isinstance(hbd_raw, (int, float)) else 0
        hba_raw = data.get("HBondAcceptorCount", 0)
        hba = int(hba_raw) if isinstance(hba_raw, (int, float)) else 0

        return PubChemCompound(
            cid=cid,
            molecular_formula=formula,
            molecular_weight=mw,
            iupac_name=iupac,
            canonical_smiles=smiles,
            inchi=inchi,
            xlogp=xlogp,
            hydrogen_bond_donor_count=hbd,
            hydrogen_bond_acceptor_count=hba,
        )
