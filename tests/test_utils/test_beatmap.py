from __future__ import annotations

from io import StringIO

import pytest

import aiosu

modes = ["legacy", "lazer"]


@pytest.fixture
def beatmap_file():
    def _beatmap_file():
        with open(f"tests/data/beatmap.osu") as f:
            data = f.read()
        return data

    return _beatmap_file


def test_parse_beatmap(beatmap_file):
    with StringIO(beatmap_file()) as data:
        beatmap = aiosu.utils.parsers.beatmap.parse_file(data)
        print(beatmap.__dict__)
        assert isinstance(beatmap, aiosu.models.BeatmapFile)
