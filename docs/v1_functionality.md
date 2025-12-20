# CLIPER v1 - Main Functionality Reference

This document catalogs all main functionality functions in CLIPER to facilitate development of new CLI and GUI interfaces.

## Table of Contents
1. [CLI Workflow](#cli-workflow)
2. [Core Pipeline Functions](#core-pipeline-functions)
3. [Video Download](#video-download)
4. [Transcription](#transcription)
5. [Clip Generation](#clip-generation)
6. [AI Copy Generation](#ai-copy-generation)
7. [Video Export](#video-export)
8. [Face Tracking & Dynamic Reframing](#face-tracking--dynamic-reframing)
9. [Subtitle Generation](#subtitle-generation)
10. [State Management](#state-management)
11. [Cleanup & Utilities](#cleanup--utilities)
12. [Utilities](#utilities)
13. [Configuration](#configuration)
14. [Prompt System Architecture](#prompt-system-architecture)

---

## CLI Workflow

### Main Loop & Menus
- **File:** `cliper.py`
- **Functions:** `main()`, `menu_principal()`, `opcion_procesar_video()`
- **Purpose:** Rich-based interactive CLI that orchestrates the pipeline.
- **Capabilities:** Lists downloaded videos with state, opens per-video actions, entry to add/import videos, cleanup shortcuts, and a “Full Pipeline” menu item (currently shows *coming soon* and is not implemented).

### Add or Import Video
- **Function:** `opcion_descargar_video()`
- **Purpose:** Add a YouTube URL **or** register a local file path.
- **Flow:** Validates input → lets user pick a content preset → downloads if URL or registers existing file → stores `content_type` + `preset` in `StateManager` → optional immediate transcription.

### Per-Video Actions
- **Functions:** `opcion_transcribir_video()`, `opcion_generar_clips()`, `opcion_generar_copies()`, `opcion_exportar_clips()`
- **Purpose:** Guided steps for each pipeline stage using preset-driven defaults.
- **Highlights:** Model selection with shortcuts, language “auto” mapping, clip duration presets (short/medium/long/custom), adjustable max clips, copy generation gating on clips, export options for aspect ratio, subtitles, face tracking (9:16), logo overlay, and organize-by-style folders based on AI classifications.

### Cleanup Shortcuts
- **Functions:** `opcion_cleanup_project()`, `cleanup_downloads()`, `cleanup_transcripts()`, `cleanup_clips_metadata()`, `cleanup_outputs()`, `cleanup_entire_project()`
- **Purpose:** CLI wrappers around `CleanupManager` to delete specific artifact types, outputs only, or perform a guarded full reset.

---

## Core Pipeline Functions

### Main Entry Point
**File:** `cliper.py`

**Function:** `main()`
- **Purpose:** Main CLI loop orchestrating all operations
- **Inputs:** None (reads from CLI)
- **Outputs:** None (interactive menu)
- **Dependencies:** All modules below

**Function:** `escanear_videos() -> List[Dict[str, str]]`
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

---

## Video Download

**Module:** `src/downloader.py` (CLI also accepts direct local file paths, bypassing download)

### Class: `YoutubeDownloader`

**Function:** `__init__(download_dir: str = "downloads")`
- **Purpose:** Initialize downloader
- **Inputs:** `download_dir` (optional, default: "downloads")
- **Outputs:** None (initializes instance)

**Function:** `validate_url(url: str) -> bool`
- **Purpose:** Validates YouTube URL format
- **Inputs:** `url: str` (YouTube URL)
- **Outputs:** `bool` (True if valid)

**Function:** `get_video_info(url: str) -> Optional[Dict[str, Any]]`
- **Purpose:** Gets video metadata without downloading
- **Inputs:** `url: str` (YouTube URL)
- **Outputs:** 
  ```python
  {
    'id': str,
    'title': str,
    'duration': int,  # seconds
    'uploader': str,
    'view_count': int,
    'description': str,
    'thumbnail': str
  }
  ```
- **Returns:** `None` if error

**Function:** `download(url: str, quality: str = "best", output_filename: Optional[str] = None) -> Optional[str]`
- **Purpose:** Downloads video from YouTube
- **Inputs:**
  - `url: str` (YouTube URL)
  - `quality: str` (optional: "best", "1080p", "720p", "480p", "360p")
  - `output_filename: str` (optional custom filename)
- **Outputs:** `str` (path to downloaded file) or `None` if error
- **Side Effects:** Creates file in `downloads/` directory

**Function:** `download_audio_only(url: str) -> Optional[str]`
- **Purpose:** Downloads only audio track as MP3
- **Inputs:** `url: str` (YouTube URL)
- **Outputs:** `str` (path to MP3 file) or `None` if error

**Helper:** `download_video(url: str, quality: str = "best") -> Optional[str>`
- **Purpose:** Convenience wrapper to instantiate `YoutubeDownloader` and call `download()`
- **Outputs:** Same as `download()`

---

## Transcription

**Module:** `src/transcriber.py`

### Class: `Transcriber`

**Function:** `__init__(model_size: str = "base", device: str = "auto", compute_type: str = "int8")`
- **Purpose:** Initialize WhisperX transcriber
- **Inputs:**
  - `model_size: str` ("tiny", "base", "small", "medium", "large-v2")
  - `device: str` ("auto", "cpu", "mps")
  - `compute_type: str` ("int8", "float16")
- **Outputs:** None (loads Whisper model)

**Function:** `transcribe(video_path: str, language: Optional[str] = None, skip_if_exists: bool = True) -> Optional[str]`
- **Purpose:** Transcribes video audio to text with word-level timestamps
- **Inputs:**
  - `video_path: str` (path to video file)
  - `language: Optional[str]` (ISO code: "es", "en", None for auto-detect)
  - `skip_if_exists: bool` (if True, returns existing transcript if found)
- **Outputs:** `str` (path to JSON transcript file) or `None` if error
- **Side Effects:** 
  - Creates `temp/{video_id}_audio.wav` (extracted audio)
  - Creates `temp/{video_id}_transcript.json` (transcription)
- **Output Format:**
  ```json
  {
    "video_id": "video_abc123",
    "video_path": "downloads/video.mp4",
    "audio_path": "temp/video_abc123_audio.wav",
    "language": "es",
    "segments": [
      {
        "start": 0.0,
        "end": 5.2,
        "text": "Hola mundo",
        "words": [
          {"word": "Hola", "start": 0.0, "end": 0.5},
          {"word": "mundo", "start": 0.5, "end": 1.0}
        ]
      }
    ],
    "word_segments": [...]
  }
  ```

**Function:** `load_transcript(transcript_path: str) -> Optional[Dict]`
- **Purpose:** Loads existing transcript JSON
- **Inputs:** `transcript_path: str`
- **Outputs:** `Dict` (transcript data) or `None` if error

**Function:** `get_transcript_summary(transcript_path: str) -> Optional[Dict]`
- **Purpose:** Gets summary statistics without loading full transcript
- **Inputs:** `transcript_path: str`
- **Outputs:**
  ```python
  {
    "language": str,
    "num_segments": int,
    "total_duration": float,  # seconds
    "total_words": int,
    "first_text": str  # first 100 chars
  }
  ```

---

## Clip Generation

**Module:** `src/clips_generator.py`

### Class: `ClipsGenerator`

**Function:** `__init__(min_clip_duration: int = 30, max_clip_duration: int = 90)`
- **Purpose:** Initialize clip generator with ClipsAI
- **Inputs:**
  - `min_clip_duration: int` (minimum seconds per clip)
  - `max_clip_duration: int` (maximum seconds per clip)
- **Outputs:** None (initializes ClipsAI ClipFinder)

**Function:** `generate_clips(transcript_path: str, min_clips: int = 3, max_clips: int = 10) -> Optional[List[Dict]]`
- **Purpose:** Detects clip boundaries using AI topic change detection
- **Inputs:**
  - `transcript_path: str` (path to WhisperX transcript JSON)
  - `min_clips: int` (minimum clips expected)
  - `max_clips: int` (maximum clips to generate)
- **Outputs:**
  ```python
  [
    {
      "clip_id": 1,
      "start_time": 0.0,      # seconds
      "end_time": 45.5,       # seconds
      "duration": 45.5,       # seconds
      "text_preview": "First words...",
      "full_text": "Complete transcript text for this clip",
      "method": "clipsai"  # or "fixed_time" if fallback
    },
    ...
  ]
  ```
- **Returns:** `None` if error
- **Side Effects:** Uses ClipsAI to analyze transcript

**Function:** `save_clips_metadata(clips: List[Dict], video_id: str, output_path: Optional[str] = None) -> Optional[str]`
- **Purpose:** Saves clip metadata to JSON file
- **Inputs:**
  - `clips: List[Dict]` (clips from `generate_clips()`)
  - `video_id: str`
  - `output_path: Optional[str]` (default: `temp/{video_id}_clips.json`)
- **Outputs:** `str` (path to saved JSON) or `None` if error
- **Output Format:**
  ```json
  {
    "video_id": "video_abc123",
    "num_clips": 10,
    "min_clip_duration": 30,
    "max_clip_duration": 90,
    "clips": [...]
  }
  ```

**Function:** `load_clips_metadata(metadata_path: str) -> Optional[Dict]`
- **Purpose:** Loads previously saved clip metadata
- **Inputs:** `metadata_path: str`
- **Outputs:** `Dict` (metadata) or `None` if error

---

## AI Copy Generation

**Module:** `src/copys_generator.py`

### Class: `CopysGenerator`

**Function:** `__init__(video_id: str, model: Literal["gemini-2.0-flash-exp", "gemini-1.5-pro"] = "gemini-2.0-flash-exp", max_attempts: int = 3)`
- **Purpose:** Initialize AI copy generator with LangGraph workflow
- **Inputs:**
  - `video_id: str`
  - `model: str` (Gemini model name)
  - `max_attempts: int` (retry attempts if quality < 7.5)
- **Outputs:** None (initializes LangGraph workflow)

**Function:** `generate() -> Dict`
- **Purpose:** Executes full LangGraph workflow: classify → generate → validate → save
- **Inputs:** None (uses `video_id` from `__init__`)
- **Outputs:**
  ```python
  {
    "success": bool,
    "error": Optional[str],
    "output_file": Optional[str],  # path to clips_copys.json
    "metrics": {
      "total_copies": int,
      "total_classified": int,
      "average_engagement": float,  # 1-10
      "average_viral_potential": float,  # 1-10
      "distribution": {
        "viral": int,
        "educational": int,
        "storytelling": int
      }
    },
    "logs": List[str]  # process logs
  }
  ```
- **Side Effects:**
  - Reads `temp/{video_id}_clips.json`
  - Creates `output/{video_id}/copys/clips_copys.json`
- **Pipeline (LangGraph nodes):**
  - Loads clips metadata → classifies clips into styles → groups clips per style.
  - Generates copies per style (viral/educational/storytelling) using Gemini.
  - Validates structure + analyzes quality; auto-retries up to `max_attempts` if quality < 7.5.
  - Saves results/metrics and returns step-by-step logs for the UI.
- **Output File Format:**
  ```json
  {
    "video_id": "video_abc123",
    "generated_at": "2025-01-15T10:30:00",
    "model": "gemini-2.0-flash-exp",
    "total_clips": 10,
    "style": "auto-classified",
    "average_engagement": 8.5,
    "average_viral_potential": 7.2,
    "clips": [
      {
        "clip_id": 1,
        "copy": "Amazing content 🤯 #AI #Tech #AICDMX",
        "metadata": {
          "sentiment": "educational",
          "sentiment_score": 0.75,
          "engagement_score": 8.5,
          "suggested_thumbnail_timestamp": 12.5,
          "primary_topics": ["AI", "tech", "innovation"],
          "hook_strength": "high",
          "viral_potential": 7.8
        }
      }
    ],
    "classification_metadata": {
      "classifications": [
        {
          "clip_id": 1,
          "style": "viral",
          "confidence": 0.9,
          "reason": "..."
        }
      ],
      "distribution": {...}
    }
  }
  ```

### Helper Function

**Function:** `generate_copys_for_video(video_id: str, model: str = "gemini-2.0-flash-exp") -> Dict`
- **Purpose:** Convenience function for CLI usage
- **Inputs:**
  - `video_id: str`
  - `model: str` (optional)
- **Outputs:** Same as `CopysGenerator.generate()`
- **Side Effects:** Reads clips metadata and writes `output/{video_id}/copys/` artifacts

---

## Video Export

**Module:** `src/video_exporter.py`

### Class: `VideoExporter`

**Function:** `__init__(output_dir: str = "output")`
- **Purpose:** Initialize video exporter
- **Inputs:** `output_dir: str` (optional, default: "output")
- **Outputs:** None (creates output directory)

**Function:** `export_clips(video_path: str, clips: List[Dict], aspect_ratio: Optional[str] = None, video_name: Optional[str] = None, add_subtitles: bool = False, transcript_path: Optional[str] = None, subtitle_style: str = "default", organize_by_style: bool = False, clip_styles: Optional[Dict[int, str]] = None, enable_face_tracking: bool = False, face_tracking_strategy: str = "keep_in_frame", face_tracking_sample_rate: int = 3, add_logo: bool = False, logo_path: Optional[str] = "assets/logo.png", logo_position: str = "top-right", logo_scale: float = 0.1) -> List[str]`
- **Purpose:** Exports clips to video files with optional processing (face tracking, subtitles, logos)
- **Inputs:**
  - `video_path: str` (path to source video)
  - `clips: List[Dict]` (from `ClipsGenerator.generate_clips()`)
  - `aspect_ratio: Optional[str]` ("9:16", "1:1", "16:9", or None for original)
  - `video_name: Optional[str]` (base name for output files)
  - `add_subtitles: bool` (burn subtitles into video)
  - `transcript_path: Optional[str]` (required if `add_subtitles=True`)
  - `subtitle_style: str` ("default", "bold", "yellow", "tiktok", "small", "tiny")
  - `organize_by_style: bool` (create subfolders: viral/educational/storytelling)
  - `clip_styles: Optional[Dict[int, str]]` (mapping clip_id → style)
  - **Face Tracking Parameters:**
    - `enable_face_tracking: bool` (enable dynamic face tracking for aspect ratio conversion)
      - **Only works with `aspect_ratio="9:16"`** (vertical format)
      - Automatically keeps faces in frame when converting 16:9 → 9:16
      - Uses MediaPipe for face detection
    - `face_tracking_strategy: str` 
      - `"keep_in_frame"` (default): Minimal crop movement, professional look
      - `"centered"`: Always centers face, more movement
    - `face_tracking_sample_rate: int` (process every N frames, default: 3 for 3x speedup)
  - **Logo Parameters:**
    - `add_logo: bool` (overlay logo on video)
    - `logo_path: Optional[str]` (path to logo image, default: "assets/logo.png")
    - `logo_position: str` ("top-right", "top-left", "bottom-right", "bottom-left")
    - `logo_scale: float` (0.1 = 10% of video height)
- **Outputs:** `List[str]` (paths to exported clip files)
- **Processing Pipeline:**
  1. If `enable_face_tracking=True` and `aspect_ratio="9:16"`:
     - Calls `FaceReframer.reframe_video()` to create temp reframed video
     - Temp video has face tracking applied (9:16 format)
     - Uses temp video as input for subsequent steps
  2. If `add_subtitles=True`:
     - Generates SRT file for clip using `SubtitleGenerator`
     - Burns subtitles into video with FFmpeg
  3. If `add_logo=True`:
     - Overlays logo using FFmpeg filter_complex
  4. Applies aspect ratio conversion (if not already done by face tracking)
  5. Exports final clip to `output/{video_name}/{clip_id}.mp4`
- **Side Effects:**
  - Creates `output/{video_name}/{clip_id}.mp4` for each clip
  - Creates `output/{video_name}/{clip_id}.srt` if subtitles enabled
  - Creates temporary reframed video if face tracking enabled (auto-deleted)
  - Creates subfolders if `organize_by_style=True`
- **Face Tracking Integration:**
  - Face tracking happens BEFORE subtitles/logo are added
  - Creates `{clip_id}_reframed_temp.mp4` temporarily
  - Falls back to static center crop if face detection fails
- **File Structure:**
  ```
  output/
    {video_name}/
      1.mp4
      1.srt
      2.mp4
      2.srt
      ...
      viral/
        3.mp4
        5.mp4
      educational/
        1.mp4
        2.mp4
  ```

**Function:** `get_video_info(video_path: str) -> Dict`
- **Purpose:** Gets video metadata using ffprobe
- **Inputs:** `video_path: str`
- **Outputs:**
  ```python
  {
    'duration': float,  # seconds
    'width': int,
    'height': int,
    'fps': float,
    'codec': str
  }
  ```

---

## Face Tracking & Dynamic Reframing

**Module:** `src/reframer.py`

### Overview

Face tracking intelligently keeps faces in frame when converting videos from horizontal (16:9) to vertical (9:16) aspect ratios. Instead of static center cropping (which cuts off faces when speakers move), this feature uses MediaPipe face detection to dynamically adjust the crop position frame-by-frame.

**Key Features:**
- **Dynamic Face Tracking**: Detects largest face in each frame and adjusts crop position
- **Aspect Ratio Conversion**: Converts 16:9 → 9:16 while keeping face visible
- **Two Strategies**: "keep_in_frame" (minimal movement) or "centered" (always centered)
- **Performance Optimized**: Frame sampling (process every N frames) for 3x speedup
- **Fallback Support**: Falls back to center crop if no face detected

**Use Case:** Perfect for converting talking-head videos (podcasts, interviews, tutorials) to vertical format for TikTok/Reels/Shorts without losing the speaker's face.

### Class: `FaceReframer`

**Function:** `__init__(frame_sample_rate: int = 3, strategy: str = "keep_in_frame", safe_zone_margin: float = 0.15, min_detection_confidence: float = 0.5)`
- **Purpose:** Initialize face tracking reframer with MediaPipe
- **Inputs:**
  - `frame_sample_rate: int` (process every N frames, default: 3 for 3x speedup)
  - `strategy: str` 
    - `"keep_in_frame"` (default): Only moves crop when face exits safe zone (minimal jitter, professional look)
    - `"centered"`: Always centers face (more movement, can be jittery)
  - `safe_zone_margin: float` (0.15 = 15% margin on each side, total 30% breathing room)
  - `min_detection_confidence: float` (MediaPipe threshold, default: 0.5)
- **Outputs:** None (initializes MediaPipe face detector)
- **Technical Details:**
  - Uses MediaPipe Face Detection (model_selection=1 for full-range detection)
  - Detects largest face in frame (handles multi-person shots)
  - Safe zone prevents unnecessary crop movement

**Function:** `reframe_video(input_path: str, output_path: str, target_resolution: Tuple[int, int], start_time: Optional[float] = None, end_time: Optional[float] = None) -> str`
- **Purpose:** Generates reframed video with dynamic face tracking for aspect ratio conversion
- **Inputs:**
  - `input_path: str` (source video path, typically 16:9)
  - `output_path: str` (output video path, will be 9:16)
  - `target_resolution: Tuple[int, int]` (width, height) e.g., (1080, 1920) for 9:16
  - `start_time: Optional[float]` (start timestamp in seconds, for clip processing)
  - `end_time: Optional[float]` (end timestamp in seconds, for clip processing)
- **Outputs:** `str` (path to reframed video file)
- **Side Effects:** 
  - Creates temporary reframed video file
  - Uses FFmpeg subprocess for encoding (handles macOS M4 compatibility)
- **Process:**
  1. Opens source video with OpenCV
  2. Scales video to ensure sufficient resolution for vertical crop
  3. For each frame (with sampling):
     - Detects largest face using MediaPipe
     - Calculates optimal crop position based on strategy
     - Applies crop (vertical center, horizontal dynamic)
  4. Writes reframed frames to output video
  5. Falls back to center crop if no face detected for 10+ frames
- **Performance:** 
  - ~3.3ms per frame detection (MediaPipe)
  - 3x speedup with frame sampling (process every 3 frames)
  - ~11px average movement between sampled frames (acceptable)

**Internal Methods (used by reframe_video):**

**Function:** `_detect_largest_face(frame) -> Optional[Dict]`
- **Purpose:** Detects largest face in frame using MediaPipe
- **Inputs:** `frame` (OpenCV BGR frame)
- **Outputs:**
  ```python
  {
    'x': int,           # bounding box x
    'y': int,           # bounding box y
    'width': int,       # bounding box width
    'height': int,      # bounding box height
    'center_x': int,    # face center X coordinate
    'center_y': int     # face center Y coordinate
  }
  ```
- **Returns:** `None` if no face detected

**Function:** `_calculate_crop_keep_in_frame(face: Dict, frame_width: int, frame_height: int, target_width: int, target_height: int) -> int`
- **Purpose:** Calculates crop X position using "keep_in_frame" strategy
- **Logic:** Only moves crop when face exits safe zone (15% margins)
- **Inputs:** Face dict, frame dimensions, target dimensions
- **Outputs:** `int` (crop X position in pixels)

**Function:** `_calculate_crop_centered(face: Dict, frame_width: int, target_width: int) -> int`
- **Purpose:** Calculates crop X position using "centered" strategy
- **Logic:** Always centers face horizontally
- **Inputs:** Face dict, frame width, target width
- **Outputs:** `int` (crop X position in pixels)

### Integration with Video Export

Face tracking is automatically used when:
- `enable_face_tracking=True` in `VideoExporter.export_clips()`
- `aspect_ratio="9:16"` (vertical format)
- Creates temporary reframed video before adding subtitles/logo

**Workflow:**
```
Original Video (16:9)
  ↓
FaceReframer.reframe_video() → temp_reframed.mp4 (9:16 with face tracking)
  ↓
FFmpeg adds subtitles/logo → Final output (9:16)
```

### Helper Class: `FFmpegVideoWriter`

**Module:** `src/reframer.py`

**Function:** `__init__(output_path: str, width: int, height: int, fps: float, codec: str = 'libx264', preset: str = 'fast', crf: int = 23)`
- **Purpose:** VideoWriter using FFmpeg subprocess (for macOS M4 compatibility)
- **Inputs:** Video properties and encoding settings
- **Outputs:** None (initializes FFmpeg subprocess)
- **Why:** cv2.VideoWriter fails on macOS M4, FFmpeg subprocess uses native arm64 FFmpeg

**Function:** `write(frame: np.ndarray) -> bool`
- **Purpose:** Writes frame to video via FFmpeg stdin
- **Inputs:** `frame` (NumPy array, BGR format, uint8)
- **Outputs:** `bool` (success)

**Function:** `release()`
- **Purpose:** Closes FFmpeg subprocess and finalizes video
- **Inputs:** None
- **Outputs:** None

---

## Subtitle Generation

**Module:** `src/subtitle_generator.py`

### Class: `SubtitleGenerator`

**Function:** `generate_srt_from_transcript(transcript_path: str, output_path: Optional[str] = None, max_chars_per_line: int = 42, max_duration: float = 5.0) -> Optional[str]`
- **Purpose:** Generates SRT file from full transcript
- **Inputs:**
  - `transcript_path: str` (WhisperX transcript JSON)
  - `output_path: Optional[str]` (default: same as transcript with .srt)
  - `max_chars_per_line: int` (characters per subtitle line)
  - `max_duration: float` (max seconds per subtitle)
- **Outputs:** `str` (path to SRT file) or `None` if error

**Function:** `generate_srt_for_clip(transcript_path: str, clip_start: float, clip_end: float, output_path: str, max_chars_per_line: int = 42, max_duration: float = 5.0) -> Optional[str]`
- **Purpose:** Generates SRT file for a specific clip (timestamps adjusted)
- **Inputs:**
  - `transcript_path: str` (full transcript JSON)
  - `clip_start: float` (clip start time in seconds)
  - `clip_end: float` (clip end time in seconds)
  - `output_path: str` (output SRT path)
  - `max_chars_per_line: int`
  - `max_duration: float`
- **Outputs:** `str` (path to SRT file) or `None` if error

---

## State Management

**Module:** `src/utils/state_manager.py`

### Class: `StateManager`

**Function:** `__init__(state_file: str = "temp/project_state.json")`
- **Purpose:** Initialize state manager
- **Inputs:** `state_file: str` (optional)
- **Outputs:** None (loads existing state or creates new)

**Function:** `register_video(video_id: str, filename: str, content_type: str = "tutorial", preset: Dict = None) -> None`
- **Purpose:** Registers a new video in project state
- **Inputs:**
  - `video_id: str`
  - `filename: str`
  - `content_type: str` (optional: "podcast", "tutorial", "livestream", etc.)
  - `preset: Dict` (optional configuration preset)
- **Outputs:** None (updates state file)

**Function:** `mark_transcribed(video_id: str, transcription_path: str) -> None`
- **Purpose:** Marks video as transcribed
- **Inputs:**
  - `video_id: str`
  - `transcription_path: str`
- **Outputs:** None (updates state)

**Function:** `mark_clips_generated(video_id: str, clips: List[Dict], clips_metadata_path: Optional[str] = None) -> None`
- **Purpose:** Marks clips as generated
- **Inputs:**
  - `video_id: str`
  - `clips: List[Dict]` (clip data)
  - `clips_metadata_path: Optional[str]` (path to metadata JSON)
- **Outputs:** None (updates state)

**Function:** `mark_clips_exported(video_id: str, exported_paths: List[str], aspect_ratio: Optional[str] = None) -> None`
- **Purpose:** Marks clips as exported
- **Inputs:**
  - `video_id: str`
  - `exported_paths: List[str]` (list of exported file paths)
  - `aspect_ratio: Optional[str]` ("9:16", "1:1", etc.)
- **Outputs:** None (updates state)

**Function:** `get_video_state(video_id: str) -> Optional[Dict]`
- **Purpose:** Gets state for a specific video
- **Inputs:** `video_id: str`
- **Outputs:**
  ```python
  {
    "filename": str,
    "downloaded": bool,
    "transcribed": bool,
    "transcript_path": Optional[str],
    "clips_generated": bool,
    "clips": List[Dict],
    "clips_metadata_path": Optional[str],
    "clips_exported": bool,
    "exported_clips": List[str],
    "export_aspect_ratio": Optional[str],
    "content_type": str,
    "preset": Dict,
    "last_updated": str
  }
  ```

**Function:** `get_all_videos() -> Dict`
- **Purpose:** Gets all videos in project state
- **Inputs:** None
- **Outputs:** `Dict` (mapping video_id → video_state)

**Function:** `get_next_step(video_id: str) -> str`
- **Purpose:** Determines next pipeline step for video
- **Inputs:** `video_id: str`
- **Outputs:** `str` ("transcribe", "generate_clips", "export", "done", "unknown")

**Function:** `is_transcribed(video_id: str) -> bool`
- **Purpose:** Checks if a video has been transcribed
- **Inputs:** `video_id: str`
- **Outputs:** `bool` (True if video is transcribed)

**Function:** `clear_video_state(video_id: str) -> None`
- **Purpose:** Removes video state from project state (useful when deleting video)
- **Inputs:** `video_id: str`
- **Outputs:** None (updates state file)

### Helper Function

**Function:** `get_state_manager() -> StateManager`
- **Purpose:** Gets singleton StateManager instance
- **Inputs:** None
- **Outputs:** `StateManager` instance

---

## Cleanup & Utilities

**Module:** `src/cleanup_manager.py`

### Class: `CleanupManager`

**Function:** `__init__(downloads_dir: str = "downloads", temp_dir: str = "temp", output_dir: str = "output")`
- **Purpose:** Initialize cleanup manager
- **Inputs:** Directory paths (optional)
- **Outputs:** None

**Function:** `get_video_artifacts(video_key: str) -> Dict[str, Dict]`
- **Purpose:** Lists all artifacts for a video
- **Inputs:** `video_key: str`
- **Outputs:**
  ```python
  {
    'download': {
      'path': Path,
      'exists': bool,
      'size': int,  # bytes
      'type': str
    },
    'transcript': {...},
    'clips_metadata': {...},
    'output': {
      'path': Path,
      'exists': bool,
      'size': int,
      'type': 'directory',
      'clip_count': int
    },
    'temp_files': {...}
  }
  ```

**Function:** `delete_video_artifacts(video_key: str, artifact_types: Optional[List[str]] = None, dry_run: bool = False) -> Dict[str, bool]`
- **Purpose:** Deletes specific artifacts for a video
- **Inputs:**
  - `video_key: str`
  - `artifact_types: Optional[List[str]]` (["download", "transcript", "clips_metadata", "output", "temp_files"] or None for all)
  - `dry_run: bool` (simulate without deleting)
- **Outputs:** `Dict[str, bool]` (result for each artifact type)

**Function:** `delete_all_project_data(dry_run: bool = False) -> Dict[str, bool]`
- **Purpose:** Deletes all project data (fresh start)
- **Inputs:** `dry_run: bool`
- **Outputs:** `Dict[str, bool]` (result for each directory: downloads, temp, output, cache, state)

**Function:** `display_cleanable_artifacts(video_key: Optional[str] = None)`
- **Purpose:** Displays table of cleanable artifacts
- **Inputs:** `video_key: Optional[str]` (if None, shows all videos)
- **Outputs:** None (prints Rich table)

---

## Utilities

**Module:** `src/utils/logger.py`
- **Functions:** `setup_logger(name: str = "cliper", level=logging.INFO, log_file: Optional[str] = None)`, `get_logger(name: str)`, `default_logger`
- **Purpose:** Centralized logger setup used across modules (console formatter + optional file handler).

**Module:** `src/utils/__init__.py`
- **Exports:** `setup_logger`, `default_logger`, `StateManager`, `get_state_manager`
- **Purpose:** Convenience imports for modules/CLI to share logger and state manager instances.

---

## Configuration

**Module:** `config/content_presets.py`

**Function:** `get_preset(content_type: str) -> Dict[str, Any]`
- **Purpose:** Gets configuration preset for content type
- **Inputs:** `content_type: str` ("podcast", "tutorial", "livestream", "documentary", "short_form")
- **Outputs:**
  ```python
  {
    "name": str,
    "description": str,
    "icon": str,
    "transcription": {
      "model_size": str,
      "enable_diarization": bool,
      "language": Optional[str]
    },
    "clips": {
      "method": str,
      "min_duration": int,
      "max_duration": int,
      "prefer_speaker_changes": bool
    },
    "use_case": str
  }
  ```

**Function:** `list_presets() -> Dict[str, str]`
- **Purpose:** Lists all available presets
- **Inputs:** None
- **Outputs:** `Dict[str, str]` (mapping key → "icon name")

**Function:** `get_preset_description(content_type: str) -> str`
- **Purpose:** Gets description for a preset
- **Inputs:** `content_type: str`
- **Outputs:** `str` (description)
- **Used By:** CLI prompts for adding/processing videos to suggest transcription model sizes, diarization flags, clip durations, and hybrid/fixed-time fallbacks (e.g., livestream preset enables fixed-time fallback).

---

## Prompt System Architecture

**Module:** `src/prompts/`

The prompt system is a sophisticated multi-layered architecture that generates AI copies for clips using Google Gemini. It consists of base prompts, style-specific prompts, and a classifier prompt that work together to create optimized captions for TikTok/Reels/Shorts.

### Architecture Overview

**Prompt Composition:**
```
Final Prompt = BASE_SYSTEM_PROMPT + STYLE_PROMPT + JSON_FORMAT_INSTRUCTIONS
```

The system uses a **two-stage approach**:
1. **Classification Stage:** Classifier analyzes all clips and assigns each one a style (viral/educational/storytelling)
2. **Generation Stage:** Clips are grouped by style and processed with style-specific prompts

### Core Components

#### 1. Base System Prompt (`base_prompts.py`)

**Origin:** Handcrafted prompt engineering based on TikTok/Reels best practices

**Purpose:** Defines the fundamental "contract" for how Gemini should behave across ALL styles

**Key Rules Defined:**
- **Character Limit:** Strict 150-character maximum (TikTok limit)
- **Required Hashtag:** ALL copies MUST include #AICDMX (branding)
- **Code-Switching:** Natural Spanish + English mix for Latino tech audience
  - Structure in Spanish: "¿Sabías que...", "Cuando tu..."
  - Technical terms in English: "React hooks", "API", "debugging"
- **Emoji Usage:** 1-2 relevant emojis maximum
- **Hashtag Integration:** Mix hashtags naturally into copy, NOT at end
- **Metadata Requirements:** 7 required fields (sentiment, engagement_score, viral_potential, etc.)

**Constants:**
- `SYSTEM_PROMPT` - The main system instructions
- `JSON_FORMAT_INSTRUCTIONS` - Required output format specification

**Function:** `build_base_system_prompt(include_format: bool = True) -> str`
- Builds the base prompt with optional JSON format instructions
- Used by style prompts to compose final prompt

**Example Rules from Base Prompt:**
```
✅ CORRECT (148 chars):
"¿Cansado de Q&As dominados? 🎤 Este truco asegura que TODAS las preguntas se respondan #TechEvents #AICDMX"

❌ WRONG (165 chars - TOO LONG):
"¿Estás cansado de que los Q&A sessions sean dominados por una sola persona? Este increíble truco..."

✅ CORRECT (code-switching):
"Cuando tu code funciona en local pero no en prod 💀 #DevLife #AICDMX"

❌ WRONG (all English, no #AICDMX):
"When your code works locally but not in production"
```

#### 2. Classifier Prompt (`classifier_prompt.py`)

**Origin:** Expert-designed classification criteria based on content analysis patterns

**Purpose:** Automatically detects the optimal style for each clip based on transcript content

**Function:** `get_classifier_prompt() -> str`
- Returns the classification prompt
- Used in `CopysGenerator.classify_clips_node()`

**Classification Criteria:**

**Viral Style (🔥)** - Assigned when clip contains:
- Surprising/counterintuitive data
- Provocative or controversial moments
- High-curiosity questions
- Relatable humor/frustration
- "Hot takes" or polarizing opinions
- Keywords: "sorprendente", "nadie habla de", "el 90% de..."

**Educational Style (📚)** - Assigned when clip contains:
- Technical concept explanations
- Tutorials or "how to" content
- Technical comparisons (X vs Y)
- Best practices or design patterns
- Problem-solving demonstrations
- Keywords: "cómo...", "qué es...", "diferencia entre..."

**Storytelling Style (📖)** - Assigned when clip contains:
- Personal experiences from speaker
- Journey or transformation narratives
- Anecdotes with lessons learned
- Emotional/vulnerable moments
- Career decisions or personal stories
- Keywords: "yo...", "mi...", "hace X años...", "el día que..."

**Output Format:**
```json
{
  "classifications": [
    {
      "clip_id": 1,
      "style": "viral",
      "confidence": 0.95,
      "reason": "Contains provocative question about common developer mistakes"
    }
  ]
}
```

**How It's Modified:**
- The classifier prompt is static and defined in `classifier_prompt.py`
- It receives dynamic input: list of clips with their transcripts
- Gemini processes and returns style classifications
- These classifications determine which style prompt to use for generation

#### 3. Style-Specific Prompts

Each style has its own prompt file that extends the base prompt with style-specific instructions.

##### Viral Prompt (`viral_prompt.py`)

**Origin:** Optimized for maximum engagement using viral content formulas

**Constant:** `VIRAL_STYLE_PROMPT`

**Function:** `get_viral_prompt() -> str`
- Returns the viral-specific instructions
- Combined with base prompt by `get_prompt_for_style("viral")`

**Characteristics:**
- **Hook Formulas:**
  - Provocative questions: "¿Sabías que el 90% de devs hacen esto mal? 😱"
  - Contradictions: "Todos usan Docker, pero esto es más rápido 🚀"
  - Surprising data: "Este bug afectó a 3M usuarios y nadie lo notó 🤯"
  - Relatable moments: "POV: Llevas 6h debuggeando y el error era un typo"

- **Emotional Priorities:**
  - Extreme curiosity (sentiment_score > 0.8)
  - Surprise
  - Controlled controversy
  - FOMO (fear of missing out)

- **Expected Metrics:**
  - Hook strength: 80% should be "very_high" or "high"
  - Viral potential: Average 7.5+, identify clips with 9+ potential

- **Hashtag Strategy:** Trending + niche (e.g., #AICDMX #TechTwitter)

##### Educational Prompt (`educational_prompt.py`)

**Origin:** Designed for clear, value-focused educational content

**Constant:** `EDUCATIONAL_STYLE_PROMPT`

**Function:** `get_educational_prompt() -> str`

**Characteristics:**
- **Hook Formulas:**
  - Value promises: "3 React hooks que todo senior debe conocer"
  - Problem-solution: "Cómo debuggear memory leaks en 5 minutos"
  - Comparison: "async/await vs Promises: ¿cuál usar?"

- **Tone:**
  - Clear and direct
  - Less provocative, more informative
  - Focus on actionable learning

- **Expected Metrics:**
  - Engagement score: 7-9 range
  - Sentiment: "educational" or "curious_educational"
  - Hook strength: "high" or "medium" (doesn't need "very_high")

- **Hashtag Strategy:** Niche technical hashtags (e.g., #AICDMX #ReactJS)

##### Storytelling Prompt (`storytelling_prompt.py`)

**Origin:** Crafted for personal narrative and emotional connection

**Constant:** `STORYTELLING_STYLE_PROMPT`

**Function:** `get_storytelling_prompt() -> str`

**Characteristics:**
- **Hook Formulas:**
  - Personal vulnerability: "Mi breakup casi destruye mi project 💔"
  - Journey narrative: "Hace 2 años no sabía programar, hoy trabajo en Google"
  - Lesson learned: "El día que mi CTO me dijo que mi código era un desastre"

- **Tone:**
  - First-person perspective
  - Emotional authenticity
  - Relatable struggles and growth

- **Expected Metrics:**
  - Sentiment: "storytelling", "relatable", or "inspirational"
  - Engagement score: 7-9 range
  - Viral potential: 6-8 (connection over virality)

- **Hashtag Strategy:** Personal/career hashtags (e.g., #AICDMX #DevJourney)

#### 4. Prompt Composition System (`__init__.py`)

**Module:** `src/prompts/__init__.py`

**Function:** `get_prompt_for_style(style: str = "viral") -> str`
- **Purpose:** Composes the complete prompt for a specific style
- **Process:**
  1. Validates style is valid ("viral", "educational", "storytelling")
  2. Builds base prompt using `build_base_system_prompt(include_format=True)`
  3. Gets style-specific prompt using style_prompts map
  4. Combines: `base_prompt + "\n\n" + style_prompt`
- **Returns:** Complete prompt ready to send to Gemini
- **Used By:** `CopysGenerator._generate_copies_for_style()`

**Function:** `get_available_styles() -> list[str]`
- Returns: `["viral", "educational", "storytelling"]`
- Used for validation and CLI display

### How Prompts Are Modified

**1. Static Base (No Runtime Modification):**
- Base prompts (`SYSTEM_PROMPT`, `VIRAL_STYLE_PROMPT`, etc.) are **hardcoded strings**
- These are **NOT modified** at runtime
- Changes require editing the source files

**2. Dynamic Composition:**
Prompts are composed dynamically by combining static pieces:
```python
# In CopysGenerator._generate_copies_for_style()
full_prompt = get_prompt_for_style(style)  # "viral", "educational", or "storytelling"

# This internally does:
# base_prompt = build_base_system_prompt(include_format=True)
# style_prompt = get_viral_prompt()  # or educational/storytelling
# return base_prompt + "\n\n" + style_prompt
```

**3. Dynamic Input Data:**
The composed prompt is sent to Gemini along with **dynamic clip data**:
```python
messages = [
    {"role": "user", "content": full_prompt},  # Static composed prompt
    {"role": "user", "content": json.dumps({    # Dynamic clip data
        "clips": [
            {
                "clip_id": 1,
                "text": "Transcript of clip 1...",
                "duration": 45.2
            },
            # ... more clips
        ]
    })}
]
```

**4. How to Customize Prompts:**

To modify prompt behavior, edit the source files:

- **Change base rules:** Edit `src/prompts/base_prompts.py` → `SYSTEM_PROMPT`
- **Change viral style:** Edit `src/prompts/viral_prompt.py` → `VIRAL_STYLE_PROMPT`
- **Change educational style:** Edit `src/prompts/educational_prompt.py` → `EDUCATIONAL_STYLE_PROMPT`
- **Change storytelling style:** Edit `src/prompts/storytelling_prompt.py` → `STORYTELLING_STYLE_PROMPT`
- **Change classification criteria:** Edit `src/prompts/classifier_prompt.py` → `CLASSIFIER_PROMPT`

**Example: Adding a new rule to base prompt:**
```python
# In base_prompts.py
SYSTEM_PROMPT = """Eres un experto en crear copies virales...

## Reglas CRÍTICAS:

### Formato del Copy:
- **CRÍTICO: MAX 150 CARACTERES**
- **NEW RULE: Always mention the speaker's name if available**  # ← ADD HERE
...
"""
```

### Integration with CopysGenerator

The prompt system integrates into the LangGraph workflow:

**Step 1: Classification** (`classify_clips_node`)
```python
prompt = get_classifier_prompt()  # From classifier_prompt.py
# Send to Gemini with clip transcripts
# Gemini returns: {clip_id: 1, style: "viral", confidence: 0.95, ...}
```

**Step 2: Grouping** (`group_by_style_node`)
```python
# Group clips by classified style
# viral_clips = [clip_1, clip_5, ...]
# educational_clips = [clip_2, clip_3, ...]
# storytelling_clips = [clip_4, ...]
```

**Step 3: Generation** (`generate_viral_node`, `generate_educational_node`, `generate_storytelling_node`)
```python
# In _generate_copies_for_style(clips, style="viral")
full_prompt = get_prompt_for_style("viral")  # Composed base + viral
# Send to Gemini with viral clips
# Returns copies optimized for viral engagement
```

**Step 4: Validation** (`validate_structure_node`)
```python
# Validates all copies meet requirements:
# - Character limit <= 150
# - Contains #AICDMX hashtag
# - All metadata fields present
# - Valid sentiment values
```

### Prompt Source Attribution

**Where Prompts Come From:**

1. **Base Prompt:** Expert-designed based on:
   - TikTok/Reels content creation best practices
   - Character limits and platform constraints
   - Code-switching patterns for Latino tech audience
   - Trial-and-error optimization with real content

2. **Style Prompts:** Derived from:
   - Analysis of successful viral/educational/storytelling content
   - Hook formulas that maximize engagement
   - Platform-specific trending patterns
   - Content creator expertise in each style

3. **Classifier Prompt:** Based on:
   - Content analysis patterns from thousands of tech videos
   - Natural language indicators for each style
   - Machine learning classification principles adapted to LLM prompting

**Prompt Evolution:**
- Prompts are **version controlled** in the codebase
- Changes are made through code edits and testing
- No runtime modification or learning
- Future enhancement: Could add prompt versioning/A-B testing system

---

## Data Flow Summary

### Complete Pipeline Flow

```
1. Download Video
   YoutubeDownloader.download(url) 
   → downloads/{video_name}_{id}.mp4
   → StateManager.register_video()

2. Transcribe Video
   Transcriber.transcribe(video_path)
   → temp/{video_id}_audio.wav
   → temp/{video_id}_transcript.json
   → StateManager.mark_transcribed()

3. Generate Clips
   ClipsGenerator.generate_clips(transcript_path)
   → List[Dict] (clips with timestamps)
   → ClipsGenerator.save_clips_metadata()
   → temp/{video_id}_clips.json
   → StateManager.mark_clips_generated()

4. Generate AI Copies (Optional)
   CopysGenerator.generate()
   → output/{video_id}/copys/clips_copys.json
   → (includes classifications and copies)

5. Export Clips
   VideoExporter.export_clips(video_path, clips, ...)
   
   For each clip:
   
   a. Face Tracking (if enable_face_tracking=True and aspect_ratio="9:16")
      FaceReframer.reframe_video()
      → temp/{clip_id}_reframed_temp.mp4 (9:16 with face tracking)
      → Keeps face in frame during 16:9 → 9:16 conversion
   
   b. Subtitle Generation (if add_subtitles=True)
      SubtitleGenerator.generate_srt_for_clip()
      → output/{video_id}/{clip_id}.srt
   
   c. Video Processing
      FFmpeg processes:
      - Face-tracked video (if step a) OR original video
      - Adds subtitles (if step b)
      - Adds logo overlay (if add_logo=True)
      - Applies aspect ratio (if not done in step a)
      → output/{video_id}/{clip_id}.mp4
   
   → StateManager.mark_clips_exported()
```

**Face Tracking Flow (Detailed):**
```
Original Video (16:9, e.g., 1920x1080)
  ↓
FaceReframer.reframe_video()
  ├─ OpenCV reads frames
  ├─ MediaPipe detects face in each frame (sampled)
  ├─ Calculates crop position (keep_in_frame or centered strategy)
  ├─ Applies dynamic crop (vertical center, horizontal follows face)
  └─ FFmpegVideoWriter encodes → temp_reframed.mp4 (9:16, e.g., 1080x1920)
  ↓
FFmpeg adds subtitles/logo to reframed video
  ↓
Final Output: {clip_id}.mp4 (9:16 with face tracking + subtitles + logo)
```

### File Structure

```
project_root/
├── downloads/          # Source videos
│   └── {video_name}_{id}.mp4
├── temp/              # Intermediate files
│   ├── {video_id}_audio.wav
│   ├── {video_id}_transcript.json
│   ├── {video_id}_clips.json
│   └── project_state.json
└── output/            # Final clips
    └── {video_id}/
        ├── 1.mp4
        ├── 1.srt
        ├── 2.mp4
        ├── copys/
        │   └── clips_copys.json
        └── {style}/   # If organized by style
            └── 3.mp4
```

---

## Dependencies

### External Libraries
- `yt-dlp` - YouTube download
- `whisperx` - Transcription
- `clipsai` - Clip detection
- `langchain_google_genai` - AI copy generation
- `mediapipe` - Face detection
- `opencv-python` - Video processing
- `ffmpeg` - Video encoding (system dependency)
- `pydantic` - Data validation
- `langgraph` - Workflow orchestration
- `python-dotenv` - Environment variable loading
- `rich` - CLI UI components
- `ffmpeg-python`, `tqdm`, `typer`, `loguru`, `faster-whisper` - supporting tooling/utilities

### Internal Dependencies
- `StateManager` - Used by all modules for state tracking
- `SubtitleGenerator` - Used by `VideoExporter`
- `FaceReframer` - Used by `VideoExporter` (optional)
- `content_presets` - Used by CLI for configuration

---

## Error Handling Patterns

All main functions return:
- `Optional[T]` - Returns `None` on error
- `Dict` with `"success": bool` and `"error": Optional[str]` fields
- Exceptions are logged but not always raised (graceful degradation)

### Common Error Scenarios
1. **File not found** → Returns `None` or empty list
2. **API failure** → Logs error, returns `None`
3. **Invalid input** → Validates early, returns `None` with log
4. **Partial success** → Returns partial results with warnings in logs

---

## Notes for GUI/CLI Development

1. **State Management**: Always check `StateManager.get_video_state()` before operations
2. **Progress Tracking**: Use Rich Progress bars (see `VideoExporter.export_clips()`)
3. **Error Display**: Check return values and display errors from logs
4. **Configuration**: Use `content_presets` for default settings
5. **File Paths**: All paths are relative to project root or absolute
6. **Async Operations**: Transcription and export are CPU-intensive (consider async/threading)
7. **Cleanup**: Use `CleanupManager` for disk space management
8. **Face Tracking**: 
   - Only enable when `aspect_ratio="9:16"` (vertical format)
   - Best for talking-head content (podcasts, interviews, tutorials)
   - "keep_in_frame" strategy recommended for professional look (less jittery)
   - Frame sampling (default: 3) provides 3x speedup with minimal quality loss
   - Falls back gracefully to center crop if no face detected
   - Creates temporary files that are auto-deleted after export

---

## Future Enhancements (Not Yet Implemented)

- Batch processing multiple videos
- Custom clip editing (manual trim points)
- Thumbnail generation
- Social media direct upload
- Multi-language subtitle support
- Advanced face tracking smoothing
- Custom branding templates
