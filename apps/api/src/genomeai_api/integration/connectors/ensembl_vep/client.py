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
        consequences = []
        for tc in data.get("transcript_consequences", []):
            if not isinstance(tc, dict):
                continue
            terms = [
                str(c) for c in tc.get("consequence_terms", [])
                if isinstance(c, str)
            ]
            sift = (
                float(tc["sift_score"])
                if tc.get("sift_score") is not None
                else None
            )
            polyphen = (
                float(tc["polyphen_score"])
                if tc.get("polyphen_score") is not None
                else None
            )

            def _int(key: str) -> int | None:
                v = tc.get(key)
                return int(v) if v is not None else None

            consequences.append(VEPConsequence(
                transcript_id=str(tc.get("transcript_id", "")),
                gene_symbol=str(tc.get("gene_symbol", "")),
                gene_id=str(tc.get("gene_id", "")),
                biotype=str(tc.get("biotype", "")),
                consequence_terms=terms,
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

        colocated = data.get("colocated_variants", [])
        rs_id = ""
        if (
            colocated
            and isinstance(colocated, list)
            and isinstance(colocated[0], dict)
        ):
            rs_id = str(colocated[0].get("id", ""))

        allele_string = str(data.get("allele_string", ""))
        allele = (
            allele_string.split("/")[1]
            if "/" in allele_string else ""
        )

        return VEPResult(
            input=str(data.get("id", "")),
            start=(
                int(data["start"])
                if data.get("start") is not None
                else None
            ),
            end=(
                int(data["end"])
                if data.get("end") is not None
                else None
            ),
            allele=allele,
            strand=int(data.get("strand", 0)),
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
