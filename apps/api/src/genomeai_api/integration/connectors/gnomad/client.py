"""gnomAD client — fetch population variant frequencies via GraphQL."""

from __future__ import annotations

import logging

import httpx

from genomeai_api.integration.connectors.gnomad.models import GnomADVariant

logger = logging.getLogger(__name__)

GNOMAD_API_URL = "https://gnomad.broadinstitute.org/api"

VARIANT_QUERY = """
query VariantQuery($variantId: String!, $dataset: DatasetId!) {
  variant(variantId: $variantId, dataset: $dataset) {
    variant_id
    chrom
    pos
    ref
    alt
    exome {
      ac
      an
      af
    }
    genome {
      ac
      an
      af
    }
  }
}
"""


class GnomADClient:
    """Async gnomAD GraphQL client."""

    def __init__(self, timeout_seconds: float = 30.0) -> None:
        self._client = httpx.AsyncClient(
            base_url=GNOMAD_API_URL,
            timeout=httpx.Timeout(timeout_seconds),
        )

    async def _query(
        self,
        query: str,
        variables: dict[str, object],
    ) -> dict[str, object]:
        response = await self._client.post(
            "",
            json={"query": query, "variables": variables},
        )
        response.raise_for_status()
        data = response.json()
        if "errors" in data:
            logger.warning("gnomAD errors: %s", data["errors"])
        return data

    async def get_variant(
        self,
        variant_id: str,
        dataset: str = "gnomad_r3",
    ) -> GnomADVariant | None:
        """Fetch variant frequency from gnomAD.

        Args:
            variant_id: Variant in format "chr-pos-ref-alt" (e.g., "19-44908822-C-T")
            dataset: gnomad_r3 or gnomad_r2_1
        """
        data = await self._query(
            VARIANT_QUERY,
            {"variantId": variant_id, "dataset": dataset},
        )

        data_obj = data.get("data")
        if not isinstance(data_obj, dict):
            return None

        variant = data_obj.get("variant")
        if not isinstance(variant, dict):
            return None

        exome = variant.get("exome")
        exome_dict: dict[str, object] = (
            exome if isinstance(exome, dict) else {}
        )
        genome = variant.get("genome")
        genome_dict: dict[str, object] = (
            genome if isinstance(genome, dict) else {}
        )

        def _int(d: dict[str, object], k: str) -> int:
            v = d.get(k, 0)
            return int(v) if isinstance(v, (int, float)) else 0

        def _float(d: dict[str, object], k: str) -> float:
            v = d.get(k, 0.0)
            return float(v) if isinstance(v, (int, float)) else 0.0

        raw_vid = variant.get("variant_id", "")
        vid = str(raw_vid) if isinstance(raw_vid, str) else variant_id
        raw_chrom = variant.get("chrom", "")
        chrom = str(raw_chrom) if isinstance(raw_chrom, str) else ""
        raw_pos = variant.get("pos", 0)
        pos = int(raw_pos) if isinstance(raw_pos, (int, float)) else 0
        raw_ref = variant.get("ref", "")
        ref = str(raw_ref) if isinstance(raw_ref, str) else ""
        raw_alt = variant.get("alt", "")
        alt = str(raw_alt) if isinstance(raw_alt, str) else ""

        return GnomADVariant(
            variant_id=vid or variant_id,
            chromosome=chrom,
            start=pos,
            ref=ref,
            alt=alt,
            exome_ac=_int(exome_dict, "ac"),
            exome_an=_int(exome_dict, "an"),
            exome_af=_float(exome_dict, "af"),
            genome_ac=_int(genome_dict, "ac"),
            genome_an=_int(genome_dict, "an"),
            genome_af=_float(genome_dict, "af"),
        )

    async def health_check(self) -> bool:
        try:
            await self._query(
                VARIANT_QUERY,
                {"variantId": "19-44908822-C-T", "dataset": "gnomad_r3"},
            )
            return True
        except Exception:
            return False

    async def close(self) -> None:
        await self._client.aclose()
