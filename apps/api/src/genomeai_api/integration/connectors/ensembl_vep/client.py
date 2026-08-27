"""Ensembl VEP client — fetch variant effect predictions."""

from __future__ import annotations

import logging

import httpx

from genomeai_api.integration.connectors.ensembl_vep.models import (
    VEPConsequence,
    VEPResult,
)

logger = logging.getLogger(__name__)

ENSEMBL_REST_URL = "https://rest.ensembl.org"


class EnsemblVEPClient:
    """Async Ensembl VEP REST client."""

    def __init__(self, timeout_seconds: float = 30.0) -> None:
        self._client = httpx.AsyncClient(
            base_url=ENSEMBL_REST_URL,
            timeout=httpx.Timeout(timeout_seconds),
        )

    async def predict_hgvs(
        self, hgvs_notation: str,
    ) -> VEPResult | None:
        """Predict variant consequences using HGVS notation."""
        try:
            response = await self._client.get(
                f"/vep/human/hgvs/{hgvs_notation}",
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()
            if not data:
                return None
            return self._parse_result(data[0])
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "Ensembl VEP error: %s", exc.response.status_code,
            )
            return None

    async def predict_id(
        self, rs_id: str,
    ) -> VEPResult | None:
        """Predict variant consequences using rsID (e.g. rs7412)."""
        try:
            response = await self._client.get(
                f"/vep/human/id/{rs_id}",
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()
            if not data:
                return None
            return self._parse_result(data[0])
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "Ensembl VEP id error: %s", exc.response.status_code,
            )
            return None

    async def predict_region(
        self,
        chromosome: str,
        start: int,
        end: int,
        allele: str,
    ) -> VEPResult | None:
        """Predict variant consequences using region notation."""
        region = f"{chromosome}:{start}-{end}:{allele}"
        try:
            response = await self._client.get(
                f"/vep/human/region/{region}",
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()
            if not data:
                return None
            return self._parse_result(data[0])
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "Ensembl VEP error: %s", exc.response.status_code,
            )
            return None

    def _parse_result(self, data: dict[str, object]) -> VEPResult:
        consequences: list[VEPConsequence] = []
        raw_tc = data.get("transcript_consequences", [])
        tc_list: list[dict[str, object]] = (
            raw_tc if isinstance(raw_tc, list) else []
        )

        for tc in tc_list:
            raw_terms = tc.get("consequence_terms", [])
            raw_terms_list: list[str] = (
                [str(c) for c in raw_terms if isinstance(c, str)]
                if isinstance(raw_terms, list)
                else []
            )

            raw_sift = tc.get("sift_score")
            sift = (
                float(raw_sift)
                if isinstance(raw_sift, (int, float))
                else None
            )

            raw_poly = tc.get("polyphen_score")
            polyphen = (
                float(raw_poly)
                if isinstance(raw_poly, (int, float))
                else None
            )

            def _int(key: str) -> int | None:
                v = tc.get(key)
                if isinstance(v, (int, float)):
                    return int(v)
                return None

            consequences.append(VEPConsequence(
                transcript_id=str(tc.get("transcript_id", "")),
                gene_symbol=str(tc.get("gene_symbol", "")),
                gene_id=str(tc.get("gene_id", "")),
                biotype=str(tc.get("biotype", "")),
                consequence_terms=raw_terms_list,
                impact=str(tc.get("impact", "")),
                sift_score=sift,
                sift_prediction=str(
                    tc.get("sift_prediction", ""),
                ),
                polyphen_score=polyphen,
                polyphen_prediction=str(
                    tc.get("polyphen_prediction", ""),
                ),
                codons=str(tc.get("codons", "")),
                amino_acids=str(tc.get("amino_acids", "")),
                cdna_start=_int("cdna_start"),
                cdna_end=_int("cdna_end"),
                cds_start=_int("cds_start"),
                cds_end=_int("cds_end"),
                protein_start=_int("protein_start"),
                protein_end=_int("protein_end"),
                exon=str(tc.get("exon", "")),
                intron=str(tc.get("intron", "")),
            ))

        raw_colocated = data.get("colocated_variants", [])
        colocated: list[object] = (
            raw_colocated
            if isinstance(raw_colocated, list)
            else []
        )
        rs_id = ""
        if (
            colocated
            and isinstance(colocated[0], dict)
        ):
            first: dict[str, object] = colocated[0]
            rs_id = str(first.get("id", ""))

        allele_string = str(data.get("allele_string", ""))
        allele = (
            allele_string.split("/")[1]
            if "/" in allele_string else ""
        )

        raw_start = data.get("start")
        raw_end = data.get("end")
        raw_strand = data.get("strand", 0)
        strand_val = int(raw_strand) if isinstance(raw_strand, (int, float)) else 0

        return VEPResult(
            input=str(data.get("id", "")),
            start=(
                int(raw_start)
                if isinstance(raw_start, (int, float))
                else None
            ),
            end=(
                int(raw_end)
                if isinstance(raw_end, (int, float))
                else None
            ),
            allele=allele,
            strand=strand_val,
            rs_id=rs_id,
            consequences=consequences,
        )

    async def health_check(self) -> bool:
        try:
            response = await self._client.get("/info/ping")
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        await self._client.aclose()
