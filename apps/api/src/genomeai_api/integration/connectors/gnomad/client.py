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
        variant = data.get("data", {}).get("variant")
        if not variant:
            return None

        exome = variant.get("exome") or {}
        genome = variant.get("genome") or {}

        return GnomADVariant(
            variant_id=variant.get("variant_id", variant_id),
            chromosome=str(variant.get("chrom", "")),
            start=variant.get("pos"),
            ref=variant.get("ref", ""),
            alt=variant.get("alt", ""),
            exome_ac=exome.get("ac", 0),
            exome_an=exome.get("an", 0),
            exome_af=exome.get("af", 0.0),
            genome_ac=genome.get("ac", 0),
            genome_an=genome.get("an", 0),
            genome_af=genome.get("af", 0.0),
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
