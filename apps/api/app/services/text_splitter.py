"""Text splitter — volume detection, chapter detection, content extraction."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class SplitChapter:
    title: str
    content: str
    index: int
    volume_name: str = ""


# Volume patterns (卷, 篇, Book, Part, Volume)
_VOLUME_PATTERNS = [
    re.compile(r"^\s*(第[零一二三四五六七八九十百千万\d]+[卷篇][\s：:]*.*?)$", re.MULTILINE),
    re.compile(r"^\s*((?:Book|Part|Volume)\s+\d+.*?)$", re.MULTILINE | re.IGNORECASE),
]

# Chapter patterns — ordered by specificity
_CHAPTER_PATTERNS = [
    # 第X章/节/回 with optional title: 第一章 标题
    re.compile(
        r"^\s*(第[零一二三四五六七八九十百千万\d]+[章节回][\s：:]*.*?)$",
        re.MULTILINE,
    ),
    # 序章/序言/楔子/番外/尾声/后记/前言 (keyword must be followed by space/punct/EOL, not regular text)
    re.compile(
        r"^\s*((?:序章|序言|楔子|引子|番外|尾声|后记|前言|终章|终卷|番外篇)(?:[\s：:,.，。].*|$))",
        re.MULTILINE,
    ),
    # Chapter N / CHAPTER N
    re.compile(r"^\s*(Chapter\s+\d+.*?)$", re.MULTILINE | re.IGNORECASE),
    # Numeric: "001 标题" or "1. 标题" or "1、标题"
    re.compile(r"^\s*(\d{1,4}[\.\s、]+[^\d].+?)$", re.MULTILINE),
]

# Combined: matches both volume and chapter lines for overall splitting
_ANY_HEADING = re.compile(
    r"^\s*(?:(?:第[零一二三四五六七八九十百千万\d]+[章节回卷篇][\s：:]*.*?)"
    r"|(?:序章|序言|楔子|引子|番外|尾声|后记|前言|终章|终卷|番外篇).*?"
    r"|(?:Chapter\s+\d+.*?)"
    r"|(?:\d{1,4}[\.\s、]+[^\d].+?))$",
    re.MULTILINE | re.IGNORECASE,
)


def _detect_best_chapter_pattern(text: str) -> re.Pattern | None:
    """Find the pattern that matches the most chapter headings."""
    best = None
    best_count = 0
    for pattern in _CHAPTER_PATTERNS:
        count = len(pattern.findall(text))
        if count > best_count:
            best_count = count
            best = pattern
    return best if best_count >= 2 else None


def _extract_volumes(text: str) -> list[tuple[str, int, int]]:
    """Extract volume boundaries. Returns list of (volume_name, start, end)."""
    matches = []
    for pattern in _VOLUME_PATTERNS:
        for m in pattern.finditer(text):
            matches.append((m.group(1).strip(), m.start(), m.end()))

    if not matches:
        return []

    # Sort by position and deduplicate overlapping
    matches.sort(key=lambda x: x[1])
    volumes = []
    for name, start, end in matches:
        if not volumes or start >= volumes[-1][2]:
            volumes.append((name, start, end))
    return volumes


def _find_all_chapter_matches(text: str) -> list[re.Match]:
    """Find all chapter heading matches using all patterns, deduplicated by position."""
    seen_positions: set[int] = set()
    all_matches: list[re.Match] = []

    for pattern in _CHAPTER_PATTERNS:
        for m in pattern.finditer(text):
            if m.start() not in seen_positions:
                seen_positions.add(m.start())
                all_matches.append(m)

    all_matches.sort(key=lambda m: m.start())
    return all_matches


def split_text(text: str) -> list[SplitChapter]:
    """Split text into chapters with volume detection.

    Uses all chapter patterns combined to find headings.
    Returns a list of SplitChapter with title, content, index, and volume_name.
    If no chapter titles are found, returns the entire text as one chapter.
    """
    matches = _find_all_chapter_matches(text)

    if not matches:
        return [SplitChapter(title="全文", content=text.strip(), index=0)]

    # Extract volume boundaries
    volumes = _extract_volumes(text)

    chapters: list[SplitChapter] = []

    for i, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()

        if not content:
            continue

        # Determine which volume this chapter belongs to
        volume = ""
        for vol_name, vol_start, vol_end in volumes:
            if match.start() >= vol_start:
                volume = vol_name

        chapters.append(
            SplitChapter(
                title=title,
                content=content,
                index=len(chapters),
                volume_name=volume,
            )
        )

    # Content before first chapter heading → prologue
    if matches and matches[0].start() > 0:
        preamble = text[: matches[0].start()].strip()
        if len(preamble) > 100:
            volume = ""
            for vol_name, vol_start, vol_end in volumes:
                if 0 >= vol_start:
                    volume = vol_name
            chapters.insert(
                0,
                SplitChapter(
                    title="序章",
                    content=preamble,
                    index=0,
                    volume_name=volume,
                ),
            )
            for i, ch in enumerate(chapters):
                ch.index = i

    return chapters if chapters else [SplitChapter(title="全文", content=text.strip(), index=0)]


def preview_split(text: str, max_chapters: int = 20) -> list[dict]:
    """Preview split results without full content. Returns list of dicts for API response."""
    chapters = split_text(text)
    return [
        {
            "index": ch.index,
            "title": ch.title,
            "volume_name": ch.volume_name,
            "word_count": len(ch.content),
            "preview": ch.content[:200] + ("..." if len(ch.content) > 200 else ""),
        }
        for ch in chapters[:max_chapters]
    ]
