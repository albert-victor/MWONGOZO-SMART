"""Pluggable exam result HTML sources (NECTA online, TETEA archive, etc.)."""

from mwongozo_smart.exam_lookup.sources.source_router import (
    TETEA_CSEE_BASE,
    CSEE_NECTA_ONLINE_MIN_YEAR,
    csee_centre_page_url,
    csee_year_index_probe_url,
    resolve_csee_data_source,
)

__all__ = [
    "TETEA_CSEE_BASE",
    "CSEE_NECTA_ONLINE_MIN_YEAR",
    "csee_centre_page_url",
    "csee_year_index_probe_url",
    "resolve_csee_data_source",
]
