"""ClinVar client — fetch clinical variant interpretations from NCBI."""

from __future__ import annotations

import asyncio
import json
import logging
import xml.etree.ElementTree as ET

import httpx

from genomeai_api.integration.connectors.clinvar.models import ClinVarRecord

logger = logging.getLogger(__name__)

NCBI_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
NCBI_RATE_LIMIT_DELAY = 0.4
MAX_RETRIES = 3
RETRY_DELAY = 1.0


class ClinVarClient:
    """Async ClinVar client via NCBI E-utilities."""

    def __init__(self, timeout_seconds: float = 30.0) -> None:
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(timeout_seconds))
        self._last_request: float = 0.0

    async def _rate_limit(self) -> None:
        now = asyncio.get_running_loop().time()
        elapsed = now - self._last_request
        if elapsed < NCBI_RATE_LIMIT_DELAY:
            await asyncio.sleep(NCBI_RATE_LIMIT_DELAY - elapsed)
        self._last_request = asyncio.get_running_loop().time()

    async def _get_with_retry(
        self, url: str, params: dict[str, object]
    ) -> httpx.Response:
        for attempt in range(MAX_RETRIES):
            try:
                await self._rate_limit()
                r = await self._client.get(url, params=params)
                r.raise_for_status()
                return r
            except (httpx.RemoteProtocolError, httpx.HTTPStatusError) as exc:
                if attempt == MAX_RETRIES - 1:
                    raise
                delay = RETRY_DELAY * (2 ** attempt)
                logger.warning(
                    "NCBI request failed (attempt %d), retrying in %.1fs: %s",
                    attempt + 1, delay, exc,
                )
                await asyncio.sleep(delay)
        raise RuntimeError("Unreachable")

    async def _esearch(self, term: str, retmax: int = 20) -> list[str]:
        params: dict[str, object] = {
            "db": "clinvar", "term": term,
            "retmode": "json", "retmax": retmax,
        }
        r = await self._get_with_retry(
            f"{NCBI_BASE_URL}/esearch.fcgi", params,
        )
        data = json.loads(r.text, strict=False)
        return data.get("esearchresult", {}).get("idlist", [])

    async def _efetch_docsum(self, ids: list[str]) -> str:
        params: dict[str, object] = {
            "db": "clinvar", "id": ",".join(ids),
            "retmode": "xml", "rettype": "docsum",
        }
        r = await self._get_with_retry(
            f"{NCBI_BASE_URL}/efetch.fcgi", params,
        )
        return r.text

    def _parse_docsum_xml(self, xml_text: str) -> list[ClinVarRecord]:
        records = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            logger.warning("Failed to parse ClinVar XML")
            return records

        for doc in root.findall(".//DocumentSummary"):
            uid = doc.get("uid", "")

            title = ""
            title_elem = doc.find("title")
            if title_elem is not None and title_elem.text:
                title = title_elem.text

            gene_symbol = ""
            if "(" in title:
                in_paren = title.split("(")[1]
                gene_symbol = in_paren.split(")")[0]

            significance = ""
            sig_elem = doc.find(
                ".//germline_classification/description",
            )
            if sig_elem is not None and sig_elem.text:
                significance = sig_elem.text

            review = ""
            review_elem = doc.find(
                ".//germline_classification/review_status",
            )
            if review_elem is not None and review_elem.text:
                review = review_elem.text

            condition = ""
            trait_elem = doc.find(
                ".//germline_classification/"
                "trait_set/trait/trait_name",
            )
            if trait_elem is not None and trait_elem.text:
                condition = trait_elem.text

            chromosome = ""
            start_pos = None
            end_pos = None
            loc_path = (
                ".//variation_set/varying/"
                "variation_loc/assembly_set"
            )
            loc_elem = doc.find(loc_path)
            if loc_elem is not None:
                chr_elem = loc_elem.find("chr")
                start_elem = loc_elem.find("start")
                stop_elem = loc_elem.find("stop")
                if chr_elem is not None and chr_elem.text:
                    chromosome = chr_elem.text
                try:
                    if start_elem is not None and start_elem.text:
                        start_pos = int(start_elem.text)
                    if stop_elem is not None and stop_elem.text:
                        end_pos = int(stop_elem.text)
                except (ValueError, TypeError):
                    pass

            cdna_change = ""
            cdna_path = (
                ".//variation_set/varying/cdna_change"
            )
            cdna_elem = doc.find(cdna_path)
            if cdna_elem is not None and cdna_elem.text:
                cdna_change = cdna_elem.text

            variant_type = ""
            vtype_path = (
                ".//variation_set/varying/variant_type"
            )
            vtype_elem = doc.find(vtype_path)
            if vtype_elem is not None and vtype_elem.text:
                variant_type = vtype_elem.text

            if uid:
                records.append(ClinVarRecord(
                    clinvar_id=uid,
                    gene_symbol=gene_symbol,
                    clinical_significance=significance,
                    review_status=review,
                    condition=condition,
                    variant_type=variant_type,
                    chromosome=chromosome,
                    start=start_pos,
                    end=end_pos,
                    hgvs_c=cdna_change,
                    summary=title,
                ))
        return records

    async def search_variants(
        self,
        gene: str,
        significance: str | None = None,
        max_results: int = 20,
    ) -> list[ClinVarRecord]:
        term = f"{gene}[Gene Name]"
        if significance:
            term += f" AND {significance}[Clinical Significance]"
        ids = await self._esearch(term, retmax=max_results)
        if not ids:
            return []
        xml_text = await self._efetch_docsum(ids)
        return self._parse_docsum_xml(xml_text)

    async def get_variant(
        self, clinvar_id: str,
    ) -> ClinVarRecord | None:
        xml_text = await self._efetch_docsum([clinvar_id])
        records = self._parse_docsum_xml(xml_text)
        return records[0] if records else None

    async def search_by_position(
        self,
        chromosome: str,
        start: int,
        end: int,
    ) -> list[ClinVarRecord]:
        term = f"{chromosome}[chr] AND {start}:{end}[Position]"
        ids = await self._esearch(term, retmax=20)
        if not ids:
            return []
        xml_text = await self._efetch_docsum(ids)
        return self._parse_docsum_xml(xml_text)

    async def health_check(self) -> bool:
        try:
            await self._esearch("BRCA1", retmax=1)
            return True
        except Exception:
            return False

    async def close(self) -> None:
        await self._client.aclose()
