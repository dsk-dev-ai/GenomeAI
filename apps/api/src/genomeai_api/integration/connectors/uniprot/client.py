"""UniProt connector — protein sequences, function, annotations."""

from __future__ import annotations

import logging

import httpx

from genomeai_api.integration.connectors.uniprot.models import UniProtProtein

logger = logging.getLogger(__name__)

UNIPROT_API_URL = "https://rest.uniprot.org"


class UniProtClient:
    """Async UniProt REST client."""

    def __init__(self, timeout_seconds: float = 30.0) -> None:
        self._client = httpx.AsyncClient(
            base_url=UNIPROT_API_URL,
            timeout=httpx.Timeout(timeout_seconds),
        )

    async def search(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[UniProtProtein]:
        """Search UniProt by gene name or protein name."""
        params = {
            "query": f"({query}) AND (organism_id:9606)",
            "format": "json",
            "size": max_results,
        }
        try:
            response = await self._client.get("/uniprotkb/search", params=params)
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            return [self._parse_entry(r) for r in results]
        except httpx.HTTPStatusError as exc:
            logger.warning("UniProt search error: %s", exc.response.status_code)
            return []

    async def get_protein(self, accession: str) -> UniProtProtein | None:
        """Fetch a single protein by UniProt accession."""
        try:
            response = await self._client.get(
                f"/uniprotkb/{accession}.json",
            )
            response.raise_for_status()
            data = response.json()
            return self._parse_entry(data)
        except httpx.HTTPStatusError as exc:
            logger.warning("UniProt fetch error: %s", exc.response.status_code)
            return None

    def _parse_entry(self, data: dict[str, object]) -> UniProtProtein:
        parsed_description = data.get("proteinDescription", {})
        prot_desc: dict[str, object] = (
            parsed_description if isinstance(parsed_description, dict) else {}
        )
        rec_name_raw = prot_desc.get("recommendedName", {})
        rec_name_dict: dict[str, object] = (
            rec_name_raw if isinstance(rec_name_raw, dict) else {}
        )
        full_name_obj = rec_name_dict.get("fullName", {})
        full_name_dict: dict[str, object] = (
            full_name_obj if isinstance(full_name_obj, dict) else {}
        )
        raw_fn = full_name_dict.get("value", "")
        full_name: str = str(raw_fn) if isinstance(raw_fn, str) else ""

        raw_genes = data.get("genes", [])
        gene_names: list[str] = []
        if isinstance(raw_genes, list):
            for g in raw_genes:
                if isinstance(g, dict):
                    gn = g.get("geneName", {})
                    if isinstance(gn, dict):
                        val = gn.get("value", "")
                        if isinstance(val, str):
                            gene_names.append(val)

        organism_obj = data.get("organism", {})
        organism_dict: dict[str, object] = (
            organism_obj if isinstance(organism_obj, dict) else {}
        )
        raw_org = organism_dict.get("scientificName", "")
        organism: str = str(raw_org) if isinstance(raw_org, str) else ""

        raw_functions = data.get("comments", [])
        function_text = ""
        if isinstance(raw_functions, list):
            for c in raw_functions:
                if not isinstance(c, dict):
                    continue
                if c.get("commentType") == "FUNCTION":
                    texts = c.get("texts", [])
                    if isinstance(texts, list) and texts:
                        first_item: dict[str, object] = (
                            texts[0] if isinstance(texts[0], dict) else {}
                        )
                        if first_item:
                            raw_val = first_item.get("value", "")
                            function_text = (
                                str(raw_val) if isinstance(raw_val, str) else ""
                            )
                        break

        raw_kw = data.get("keywords", [])
        keywords: list[str] = []
        if isinstance(raw_kw, list):
            for kw in raw_kw:
                if isinstance(kw, dict):
                    name = kw.get("name", "")
                    if isinstance(name, str):
                        keywords.append(name)

        raw_sub = data.get("comments", [])
        sub_loc = ""
        if isinstance(raw_sub, list):
            for c in raw_sub:
                if not isinstance(c, dict):
                    continue
                if c.get("commentType") == "SUBCELLULAR LOCALIZATION":
                    texts = c.get("texts", [])
                    if isinstance(texts, list) and texts:
                        first_item: dict[str, object] = (
                            texts[0] if isinstance(texts[0], dict) else {}
                        )
                        if first_item:
                            raw_val = first_item.get("value", "")
                            sub_loc = (
                                str(raw_val) if isinstance(raw_val, str) else ""
                            )
                        break

        raw_seq_len = data.get("sequence", {})
        seq_obj: dict[str, object] = (
            raw_seq_len if isinstance(raw_seq_len, dict) else {}
        )
        raw_seq_val = seq_obj.get("value", "")
        sequence = str(raw_seq_val) if isinstance(raw_seq_val, str) else ""
        raw_length = seq_obj.get("length", 0)
        length = int(raw_length) if isinstance(raw_length, (int, float)) else 0
        raw_mass = seq_obj.get("molWeight", 0)
        mass = float(raw_mass) if isinstance(raw_mass, (int, float)) else 0.0

        raw_pdb = data.get("uniProtKBCrossReferences", [])
        pdb_ids: list[str] = []
        alphafold_id = ""
        if isinstance(raw_pdb, list):
            for ref in raw_pdb:
                if not isinstance(ref, dict):
                    continue
                db = ref.get("database", "")
                if db == "PDB":
                    pid = ref.get("id", "")
                    if isinstance(pid, str):
                        pdb_ids.append(pid)
                elif db == "AlphaFoldDB":
                    aid = ref.get("id", "")
                    if isinstance(aid, str):
                        alphafold_id = aid

        accession_raw = data.get("primaryAccession", "")
        accession = str(accession_raw) if isinstance(accession_raw, str) else ""
        entry_raw = data.get("uniProtKBId", "")
        entry_name = str(entry_raw) if isinstance(entry_raw, str) else ""

        return UniProtProtein(
            accession=accession,
            entry_name=entry_name,
            protein_name=full_name,
            gene_names=gene_names,
            organism=organism,
            length=length,
            mass=mass,
            function=function_text,
            keywords=keywords,
            subcellular_location=sub_loc,
            sequence=sequence,
            pdb_ids=pdb_ids,
            alphafold_id=alphafold_id,
        )

    async def health_check(self) -> bool:
        try:
            response = await self._client.get(
                "/uniprotkb/search",
                params={"query": "BRCA1", "format": "json", "size": 1},
            )
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        await self._client.aclose()
