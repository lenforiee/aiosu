"""
This module contains functions to parse beatmap files.
"""
from __future__ import annotations

import hashlib
from typing import Any
from typing import TextIO

from ...models.files.beatmap import BeatmapFile

__all__ = (
    "parse_file",
    "parse_path",
    "write_beatmap",
    "write_path",
)


def _hash_string(s: str) -> str:
    """Hash a string."""
    return hashlib.md5(s.encode()).hexdigest()


def _parse_section_value_from_str(s: str) -> str:
    """Parse section value from a string."""

    return s.split(":", 1)[1].strip()


def _parse_general_section_line(line: str) -> tuple[str, Any]:
    value = _parse_section_value_from_str(line)

    if line.startswith("AudioFilename"):
        return "audio_filename", value

    elif line.startswith("AudioLeadIn"):
        return "audio_lead_in", int(value)

    elif line.startswith("AudioHash"):
        return "audio_hash", value

    elif line.startswith("PreviewTime"):
        return "preview_time", int(value)

    elif line.startswith("Countdown"):
        return "countdown", int(value)

    elif line.startswith("SampleSet"):
        return "sample_set", value

    elif line.startswith("StackLeniency"):
        return "stack_leniency", float(value)

    elif line.startswith("Mode"):
        return "mode", int(value)

    elif line.startswith("LetterboxInBreaks"):
        return "letterbox_in_breaks", bool(int(value))

    elif line.startswith("StoryFireInFront"):
        return "story_fire_in_front", bool(int(value))

    elif line.startswith("UseSkinSprites"):
        return "use_skin_sprites", bool(int(value))

    elif line.startswith("AlwaysShowPlayfield"):
        return "always_show_playfield", bool(int(value))

    elif line.startswith("OverlayPosition"):
        return "overlay_position", value

    elif line.startswith("SkinPreference"):
        return "skin_preference", value

    elif line.startswith("EpilepsyWarning"):
        return "epilepsy_warning", bool(int(value))

    elif line.startswith("CountdownOffset"):
        return "countdown_offset", int(value)

    elif line.startswith("SpecialStyle"):
        return "special_style", bool(int(value))

    elif line.startswith("WidescreenStoryboard"):
        return "widescreen_storyboard", bool(int(value))

    elif line.startswith("SamplesMatchPlaybackRate"):
        return "samples_match_playback_rate", bool(int(value))

    else:
        raise ValueError(f"Unsupported general section line: {line}")


def _parse_editor_section_line(line: str) -> tuple[str, Any]:
    value = _parse_section_value_from_str(line)

    if line.startswith("Bookmarks"):
        return "bookmarks", [int(b) for b in value.split(",")]

    elif line.startswith("DistanceSpacing"):
        return "distance_spacing", float(value)

    elif line.startswith("BeatDivisor"):
        return "beat_divisor", int(value)

    elif line.startswith("GridSize"):
        return "grid_size", int(value)

    elif line.startswith("TimelineZoom"):
        return "timeline_zoom", float(value)

    else:
        raise ValueError(f"Unsupported editor section line: {line}")


def _parse_metadata_section_line(line: str) -> tuple[str, Any]:
    value = _parse_section_value_from_str(line)

    if line.startswith("Title:"):
        return "title", value

    elif line.startswith("TitleUnicode"):
        return "title_unicode", value

    elif line.startswith("Artist:"):
        return "artist", value

    elif line.startswith("ArtistUnicode"):
        return "artist_unicode", value

    elif line.startswith("Creator"):
        return "creator", value

    elif line.startswith("Version"):
        return "version", value

    elif line.startswith("Source"):
        return "source", value

    elif line.startswith("Tags"):
        return "tags", [b for b in value.split(",")]

    elif line.startswith("BeatmapID"):
        return "beatmap_id", int(value)

    elif line.startswith("BeatmapSetID"):
        return "beatmap_set_id", int(value)

    else:
        raise ValueError(f"Unsupported metadata section line: {line}")


def _parse_difficulty_section_line(line: str) -> tuple[str, Any]:
    value = _parse_section_value_from_str(line)

    if line.startswith("HPDrainRate"):
        return "hp_drain_rate", float(value)

    elif line.startswith("CircleSize"):
        return "circle_size", float(value)

    elif line.startswith("OverallDifficulty"):
        return "overall_difficulty", float(value)

    elif line.startswith("ApproachRate"):
        return "approach_rate", float(value)

    elif line.startswith("SliderMultiplier"):
        return "slider_multiplier", float(value)

    elif line.startswith("SliderTickRate"):
        return "slider_tick_rate", float(value)

    else:
        raise ValueError(f"Unsupported difficulty section line: {line}")


STORYBOARD_EVENTS = ["Sprite", "Animation", "Sample"]


def _parse_events_section_line(line: str) -> tuple[str, Any]:
    values = line.split(",")
    event_type = values[0]

    if line[0] == " " or event_type in STORYBOARD_EVENTS:
        return "storyboard_data", line

    elif event_type == "0":
        background: dict[str, Any] = {
            "filename": values[2].strip('"'),
        }

        if len(values) > 3:
            background["x_offset"] = int(values[3])

        if len(values) > 4:
            background["y_offset"] = int(values[4])

        return "background", background

    elif event_type in ["1", "Video"]:
        video: dict[str, Any] = {
            "start_time": int(values[1]),
            "filename": values[2].strip('"'),
        }

        if len(values) > 3:
            video["x_offset"] = int(values[3])

        if len(values) > 4:
            video["y_offset"] = int(values[4])

        return "videos", video

    elif event_type in ["2", "Break"]:
        break_period: dict[str, Any] = {
            "start_time": int(values[1]),
            "end_time": int(values[2]),
        }

        return "break_periods", break_period
    else:
        raise ValueError(f"Unsupported events section line: {line}")


def parse_file(file: TextIO) -> BeatmapFile:
    """Parse a beatmap file and return a dictionary with the beatmap data.

    :param file: The beatmap file.
    :type file: BinaryIO
    :return: The beatmap data.
    :rtype: BeatmapFile
    """
    beatmap: dict[str, Any] = {}
    general: dict[str, Any] = {}
    editor: dict[str, Any] = {}
    metadata: dict[str, Any] = {}
    difficulty: dict[str, Any] = {}
    events: dict[str, Any] = {}

    buffer = file.read()
    lines = buffer.splitlines()
    beatmap["file_md5"] = _hash_string(buffer)

    file_header = lines.pop(0)
    beatmap["file_version"] = int(file_header.split("v")[1])

    section = None
    for line in lines:
        if not line.strip():
            continue

        if line.startswith("[") and line.endswith("]"):
            section = line.strip("[]").lower()
            continue

        if section == "general":
            general_key, general_value = _parse_general_section_line(line)
            general[general_key] = general_value

        elif section == "editor":
            editor_key, editor_value = _parse_editor_section_line(line)
            editor[editor_key] = editor_value

        elif section == "metadata":
            metadata_key, metadata_value = _parse_metadata_section_line(line)
            metadata[metadata_key] = metadata_value

        elif section == "difficulty":
            difficulty_key, difficulty_value = _parse_difficulty_section_line(line)
            difficulty[difficulty_key] = difficulty_value

        elif section == "events":
            if line.startswith("//"):
                continue

            events_key, events_value = _parse_events_section_line(line)

            if events_key == "background":
                events[events_key] = events_value
                continue

            if not events_key in events:
                events[events_key] = []

            events[events_key].append(events_value)

        # else:
        #     raise ValueError(f"Unsupported section: {section}")

    beatmap["general"] = general
    beatmap["editor"] = editor
    beatmap["metadata"] = metadata
    beatmap["difficulty"] = difficulty
    beatmap["events"] = events

    return BeatmapFile(**beatmap)


def parse_path(path: str) -> BeatmapFile:
    """Parse a beatmap file and return a dictionary with the beatmap data.

    :param path: The path to the beatmap file.
    :type path: str
    :return: The beatmap data.
    :rtype: BeatmapFile
    """
    with open(path, encoding="utf-8-sig", errors="ignore") as file:
        return parse_file(file)


def write_beatmap(file: TextIO, beatmap: BeatmapFile) -> None:
    """Write a beatmap to a file.

    :param file: The file to write to.
    :type file: BinaryIO
    :param beatmap: The beatmap to write.
    :type beatmap: BeatmapFile
    """
    ...


def write_path(path: str, beatmap: BeatmapFile) -> None:
    """Write a beatmap to a file.

    :param path: The path to the file to write to.
    :type path: str
    :param beatmap: The beatmap to write.
    :type beatmap: BeatmapFile
    """
    with open(path, "w", encoding="utf-8-sig", errors="ignore") as file:
        write_beatmap(file, beatmap)
