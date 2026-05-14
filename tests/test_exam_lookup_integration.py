from __future__ import annotations

import asyncio
import os

import pytest

from mwongozo_smart.exam_lookup.acsee_service import AcseeResultService
from mwongozo_smart.exam_lookup.result_service import CseeResultService


@pytest.mark.integration
def test_live_lookup_s1027_0034_2022() -> None:
    if os.environ.get("RUN_NECTA_INTEGRATION") != "1":
        pytest.skip("Set environment variable RUN_NECTA_INTEGRATION=1 to run live NECTA HTTP tests.")

    async def run() -> None:
        service = CseeResultService()
        # Year >= 2023 uses NECTA onlinesys; older years use TETEA archive.
        result = await service.lookup(2024, "S1027-0034", skip_cache=True)
        assert result.candidate_number == "S1027/0034"
        assert result.center_number == "S1027"
        assert result.data_source == "necta_onlinesys"

    asyncio.run(run())


@pytest.mark.integration
def test_live_tetea_csee_lookup_2008_s1027() -> None:
    if os.environ.get("RUN_NECTA_INTEGRATION") != "1":
        pytest.skip("Set environment variable RUN_NECTA_INTEGRATION=1 to run live HTTP tests.")

    async def run() -> None:
        service = CseeResultService()
        result = await service.lookup(2008, "S1027-0034", skip_cache=True)
        assert result.candidate_number == "S1027/0034"
        assert result.data_source == "tetea_maktaba"
        assert "maktaba.tetea.org" in result.source_url

    asyncio.run(run())


@pytest.mark.integration
def test_live_acsee_lookup_s0140_0538_2024() -> None:
    if os.environ.get("RUN_NECTA_INTEGRATION") != "1":
        pytest.skip("Set environment variable RUN_NECTA_INTEGRATION=1 to run live NECTA HTTP tests.")

    async def run() -> None:
        service = AcseeResultService()
        result = await service.lookup(2024, "S0140-0538", refresh_centre_index=False)
        assert result.candidate_number == "S0140/0538"
        assert result.center_number == "S0140"

    asyncio.run(run())
