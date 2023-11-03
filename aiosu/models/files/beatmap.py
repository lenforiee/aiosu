"""
This module contains models for beatmaps.
"""
from __future__ import annotations

from enum import IntEnum
from enum import Enum
from typing import Optional

from pydantic import model_validator

from ..base import BaseModel
from ..gamemode import Gamemode

__all__ = (
    "BeatmapFile",
    "Countdown",
    "SampleSet",
    "OverlayPosition",
)

EARLY_VERSION_TIMING_OFFSET = 24


def _add_offsets(time: int, version: int) -> int:
    """Add offsets to the time."""
    if version < 5:
        return time + EARLY_VERSION_TIMING_OFFSET

    return time


class Countdown(IntEnum):
    NONE = 0
    NORMAL = 1
    HALF = 2
    DOUBLE = 3

    @classmethod
    def from_type(cls, __o: object) -> Countdown:
        """Gets a sample set type.

        :param __o: Object to search for
        :type __o: object
        :raises ValueError: If object cannot be converted to Countdown
        :return: A Countdown object.
        :rtype: aiosu.models.files.beatmap.Countdown
        """
        if isinstance(__o, cls):
            return __o

        if isinstance(__o, int):
            return cls(__o)

        if isinstance(__o, str) and __o.isdigit():
            return cls(int(__o))

        if isinstance(__o, str) and __o.upper() in cls.__members__:
            return cls[__o.upper()]

        raise ValueError(f"Countdown {__o} does not exist.")

    @classmethod
    def _missing_(cls, query: object) -> Countdown:
        return cls.from_type(query)


class SampleSet(Enum):
    NONE = 0
    NORMAL = 1
    SOFT = 2
    DRUM = 3

    @classmethod
    def from_type(cls, __o: object) -> SampleSet:
        """Gets a sample set type.

        :param __o: Object to search for
        :type __o: object
        :raises ValueError: If object cannot be converted to SampleSet
        :return: A SampleSet object.
        :rtype: aiosu.models.files.beatmap.SampleSet
        """
        if isinstance(__o, cls):
            return __o

        if isinstance(__o, int):
            return cls(__o)

        if isinstance(__o, str) and __o.isdigit():
            return cls(int(__o))

        if isinstance(__o, str) and __o.upper() in cls.__members__:
            return cls[__o.upper()]

        raise ValueError(f"SampleSet {__o} does not exist.")

    @classmethod
    def _missing_(cls, query: object) -> SampleSet:
        return cls.from_type(query)


class OverlayPosition(Enum):
    NOCHANGE = "NoChange"
    BELOW = "Below"
    ABOVE = "Above"

    @classmethod
    def from_type(cls, __o: object) -> OverlayPosition:
        """Gets a sample set type.

        :param __o: Object to search for
        :type __o: object
        :raises ValueError: If object cannot be converted to OverlayPosition
        :return: A OverlayPosition object.
        :rtype: aiosu.models.files.beatmap.OverlayPosition
        """
        if isinstance(__o, cls):
            return __o

        if isinstance(__o, str) and __o.upper() in cls.__members__:
            return cls[__o.upper()]

        raise ValueError(f"OverlayPosition {__o} does not exist.")

    @classmethod
    def _missing_(cls, query: object) -> OverlayPosition:
        return cls.from_type(query)


class GeneralSection(BaseModel):
    audio_filename: str
    audio_lead_in: int
    audio_hash: Optional[str] = None
    preview_time: int
    countdown: Countdown
    sample_set: SampleSet
    stack_leniency: float
    mode: Gamemode
    letterbox_in_breaks: bool
    story_fire_in_front: Optional[bool] = None
    use_skin_sprites: Optional[bool] = None
    always_show_playfield: Optional[bool] = None
    overlay_position: Optional[OverlayPosition] = None
    skin_preference: Optional[str] = None
    epilepsy_warning: Optional[bool] = None
    countdown_offset: Optional[int] = None
    special_style: Optional[bool] = None
    widescreen_storyboard: Optional[bool] = None
    samples_match_playback_rate: Optional[bool] = None


class EditorSection(BaseModel):
    bookmarks: Optional[list[int]] = None
    distance_spacing: float
    beat_divisor: int
    grid_size: int
    timeline_zoom: float


class MetadataSection(BaseModel):
    title: str
    title_unicode: Optional[str] = None
    artist: str
    artist_unicode: Optional[str] = None
    creator: str
    version: str
    source: Optional[str] = None
    tags: Optional[list[str]] = None
    beatmap_id: Optional[int] = None  # TLDR: osu before relied on beatmap hash.
    beatmap_set_id: Optional[int] = None


class DifficultySection(BaseModel):
    hp_drain_rate: float
    circle_size: float
    overall_difficulty: float
    approach_rate: float
    slider_multiplier: float
    slider_tick_rate: float


class BeatmapFile(BaseModel):
    file_version: int
    file_md5: str

    general: GeneralSection
    editor: EditorSection
    metadata: MetadataSection
    difficulty: DifficultySection

    @property
    def full_title(self) -> str:
        return (
            f"{self.metadata.artist} - {self.metadata.title} [{self.metadata.version}]"
        )

    def __repr__(self) -> str:
        return f"<Beatmap {self.full_title} ({self.file_md5})>"

    def __str__(self) -> str:
        return self.full_title

    @model_validator(mode="after")
    def _apply_offsets(self) -> BeatmapFile:
        if self.general.preview_time and self.general.preview_time != -1:
            self.general.preview_time = _add_offsets(
                self.general.preview_time,
                self.file_version,
            )

        return self
