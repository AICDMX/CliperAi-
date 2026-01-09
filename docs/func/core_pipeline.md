# Core Pipeline Functions

### Main Entry Point
**File:** `src/tui/app.py`

The Textual TUI provides an interactive interface for orchestrating all pipeline operations.

### Video Registry
**File:** `src/utils/video_registry.py`

**Function:** `scan_videos() -> List[Dict[str, str]]`
- **Purpose:** Scans `downloads/` folder for MP4 videos
- **Inputs:** None
- **Outputs:**
  ```python
  [
    {
      "filename": "video.mp4",
      "path": "downloads/video.mp4",
      "video_id": "video_abc123"
    }
  ]
  ```
