"""Knowledge base and sample guidebook data."""

from mwongozo_smart.data.guidebook_data import PROGRAMMES, programme_index, programmes_by_category
from mwongozo_smart.data.institutions import INSTITUTIONS, institution_index
from mwongozo_smart.data.loader import GuidebookTextBlock, load_guidebook_export, split_institution_blocks

__all__ = [
    "GuidebookTextBlock",
    "INSTITUTIONS",
    "PROGRAMMES",
    "institution_index",
    "load_guidebook_export",
    "programme_index",
    "programmes_by_category",
    "split_institution_blocks",
]
