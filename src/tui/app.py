# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, List, Optional

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import DataTable, Footer, Header, Static

from src.utils import get_state_manager


SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".m4v", ".mov", ".mkv", ".webm"}


def _short_hash(text: str, length: int = 8) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:length]


def _compute_unique_video_id(video_path: Path, state_manager) -> str:
    base = video_path.stem
    existing = state_manager.get_video_state(base)
    if not existing:
        return base

    existing_path = (existing.get("video_path") or "").strip()
    if existing_path:
        try:
            if Path(existing_path).resolve() == video_path.resolve():
                return base
        except Exception:
            pass

    return f"{base}_{_short_hash(str(video_path.resolve()))}"


def _load_videos(state_manager) -> List[Dict[str, str]]:
    downloads_dir = Path("downloads")
    downloads_dir.mkdir(parents=True, exist_ok=True)

    video_files: set[Path] = set()
    for ext in SUPPORTED_VIDEO_EXTENSIONS:
        video_files |= set(downloads_dir.glob(f"*{ext}"))
        video_files |= set(downloads_dir.glob(f"*{ext.upper()}"))

    for video_file in video_files:
        video_id = _compute_unique_video_id(video_file, state_manager)
        state_manager.register_video(video_id=video_id, filename=video_file.name, video_path=str(video_file))

    videos: List[Dict[str, str]] = []
    for video_id, state in state_manager.get_all_videos().items():
        filename = state.get("filename") or f"{video_id}.mp4"
        video_path = state.get("video_path")

        if not video_path:
            fallback = Path("downloads") / filename
            if fallback.exists():
                video_path = str(fallback)
                state_manager.register_video(video_id=video_id, filename=filename, video_path=video_path)
            else:
                continue

        vp = Path(video_path)
        if not vp.exists() or not vp.is_file():
            continue

        videos.append({"video_id": video_id, "filename": filename, "path": str(vp)})

    videos.sort(key=lambda v: v["filename"].lower())
    return videos


class CliperTUI(App):
    TITLE = "CLIPER"
    SUB_TITLE = "Video Clipper (Textual)"

    CSS = """
    Screen { layout: vertical; }
    #main { height: 1fr; }
    #library { width: 2fr; }
    #details { width: 1fr; padding: 1 2; }
    """

    def __init__(self):
        super().__init__()
        self.state_manager = get_state_manager()
        self.videos: List[Dict[str, str]] = []
        self.selected_video_id: Optional[str] = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main"):
            yield DataTable(id="library")
            yield Static("Select a video", id="details")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#library", DataTable)
        table.cursor_type = "row"
        table.add_columns("Video", "Status")
        self.refresh_library()

    def refresh_library(self) -> None:
        self.videos = _load_videos(self.state_manager)
        table = self.query_one("#library", DataTable)
        table.clear()

        for video in self.videos:
            state = self.state_manager.get_video_state(video["video_id"]) or {}
            parts = []
            if state.get("transcribed"):
                parts.append("Transcribed")
            if state.get("clips_generated"):
                parts.append(f"Clips: {len(state.get('clips', []) or [])}")
            if state.get("clips_exported"):
                parts.append("Exported")
            status = " | ".join(parts) if parts else "Ready"
            table.add_row(video["filename"], status, key=video["video_id"])

        if self.videos:
            table.focus()

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        self.selected_video_id = str(event.row_key)
        state = self.state_manager.get_video_state(self.selected_video_id) or {}
        details = self.query_one("#details", Static)

        filename = state.get("filename") or self.selected_video_id
        video_path = state.get("video_path") or ""
        content_type = state.get("content_type") or "tutorial"
        lines = [
            f"Video: {filename}",
            f"Type: {content_type}",
            "",
            f"Path: {video_path}",
            "",
            f"Transcribed: {bool(state.get('transcribed'))}",
            f"Clips generated: {bool(state.get('clips_generated'))}",
            f"Clips exported: {bool(state.get('clips_exported'))}",
        ]
        details.update("\n".join(lines))


if __name__ == "__main__":
    CliperTUI().run()

