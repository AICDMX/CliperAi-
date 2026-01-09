# TUI Workflow

### Main Interface
- **File:** `src/tui/app.py`
- **Purpose:** Textual-based TUI that orchestrates the pipeline.
- **Capabilities:** Lists videos with state, multi-select for batch operations, job queue management, real-time progress and log display.

### Add or Import Video
- **Keyboard:** Press `a` to add videos
- **Purpose:** Add a YouTube URL **or** register local file paths.
- **Flow:** Validates input → downloads if URL or registers existing file → stores in `StateManager`.

### Per-Video Actions
- **Keyboard shortcuts:** `t` (transcribe), `c` (clips), `e` (export)
- **Purpose:** Queue pipeline stages for selected videos.
- **Highlights:** Settings panels for model selection, clip duration, export options (aspect ratio, subtitles, face tracking, logo overlay).

### Job Queue
- **File:** `src/core/job_runner.py`
- **Purpose:** Event-driven job orchestration with progress events.
- **Features:** Background processing, real-time progress updates, log streaming.
