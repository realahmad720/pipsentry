"""YouTube ingestion per spec Section 6: youtube-transcript-api first, falling
back to yt-dlp's own caption tracks (auto-generated or manual) when the primary
API has no transcript for the video. Whisper-based audio transcription (the
spec's final fallback for videos with no captions at all) is intentionally not
wired in here — it pulls in torch/ffmpeg, a heavy dependency for an MVP scaffold
to carry. `YouTubeExtractionError` is the single failure mode callers need to
handle either way, so swapping in a Whisper step later doesn't change callers.
"""

import re
from dataclasses import dataclass

import httpx
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import CouldNotRetrieveTranscript


class YouTubeExtractionError(Exception):
    pass


@dataclass
class YouTubeSource:
    title: str | None
    transcript: str


_VIDEO_ID_PATTERNS = [
    r"(?:v=|\/videos\/|embed\/|youtu\.be\/|\/shorts\/)([A-Za-z0-9_-]{11})",
]


def _extract_video_id(url: str) -> str:
    for pattern in _VIDEO_ID_PATTERNS:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise YouTubeExtractionError(f"Could not parse a video id out of {url!r}")


def _fetch_via_transcript_api(video_id: str) -> str:
    transcript = YouTubeTranscriptApi().fetch(video_id)
    text = " ".join(snippet.text for snippet in transcript)
    if not text.strip():
        raise YouTubeExtractionError("Transcript API returned an empty transcript")
    return text


def _strip_vtt(vtt_text: str) -> str:
    lines = []
    for line in vtt_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped == "WEBVTT":
            continue
        if "-->" in stripped or stripped.isdigit():
            continue
        lines.append(re.sub(r"<[^>]+>", "", stripped))
    # Caption files repeat the same line across consecutive cues; collapse runs.
    deduped: list[str] = []
    for line in lines:
        if not deduped or deduped[-1] != line:
            deduped.append(line)
    return " ".join(deduped)


def _fetch_via_yt_dlp_captions(info: dict) -> str:
    tracks = info.get("subtitles") or {}
    auto_tracks = info.get("automatic_captions") or {}
    candidates = tracks.get("en") or auto_tracks.get("en") or []
    vtt_entry = next((c for c in candidates if c.get("ext") == "vtt"), None)
    if vtt_entry is None:
        raise YouTubeExtractionError("No English captions (manual or automatic) available")

    response = httpx.get(vtt_entry["url"], timeout=15.0)
    response.raise_for_status()
    text = _strip_vtt(response.text)
    if not text.strip():
        raise YouTubeExtractionError("Caption track downloaded but contained no text")
    return text


def fetch_youtube_source(url: str) -> YouTubeSource:
    video_id = _extract_video_id(url)

    ydl_opts = {"skip_download": True, "quiet": True, "no_warnings": True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as exc:
        raise YouTubeExtractionError(f"Could not load video metadata: {exc}") from exc

    title = info.get("title")

    try:
        transcript = _fetch_via_transcript_api(video_id)
    except CouldNotRetrieveTranscript:
        transcript = _fetch_via_yt_dlp_captions(info)

    return YouTubeSource(title=title, transcript=transcript)
