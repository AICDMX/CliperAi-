# CLIPER v2 - Planned Functionality

This document outlines planned enhancements for CLIPER v2. All v1 functionality remains, with these additions and improvements.

## Table of Contents
1. [Installation & Deployment](#installation--deployment)
2. [Input Handling](#input-handling)
3. [Automation & Batch Processing](#automation--batch-processing)
4. [Human-in-the-Loop Workflow](#human-in-the-loop-workflow)
5. [Subtitle Customization](#subtitle-customization)
6. [Clipping Control](#clipping-control)
7. [Prompt Management](#prompt-management)
8. [Output Management](#output-management)
9. [User Experience](#user-experience)

---

## Installation & Deployment

### Full Installation Build
**Status:** Planned

**Description:** Create a complete installation target that downloads all dependencies upfront, avoiding on-demand downloads during runtime.

**Use Case:** Docker builds and offline environments where re-downloading dependencies on each run is inefficient.

**Implementation Approach:**
- Add `make install-full` target
- Pre-download all models (Whisper, MediaPipe, etc.)
- Cache all dependencies
- Verify installation completeness

---

## Input Handling

### Flexible Video Input Paths
**Status:** Planned

**Current Limitation:** Videos must be placed in `downloads/` folder.

**Planned Features:**

1. **Process Videos from Anywhere**
   - Accept absolute/relative paths as input
   - No requirement to copy videos to specific folder
   - Support drag-and-drop or file picker

2. **Auto-Copy Local Files**
   - Option to copy local videos to `downloads/` for organization
   - Preserve original file location
   - Symlink support for large files

**Implementation Approach:**
- Modify `escanear_videos()` to accept path parameter
- Add video path validation
- Update StateManager to track original locations

---

## Automation & Batch Processing

### Fully Automated CLI Mode
**Status:** Planned

**Description:** Run complete pipeline from start to finish with pre-configured settings via command-line arguments.

**Example Usage:**
```bash
uv run python src/tui/app.py \
  --input video.mp4 \
  --content-type podcast \
  --aspect-ratio 9:16 \
  --add-subtitles \
  --enable-face-tracking \
  --output-dir output/batch1 \
  --auto-run
```

**Features:**
- Accept all configuration as CLI flags
- Skip interactive prompts
- Run entire pipeline automatically
- Error handling with logs

### Bulk Video Processing
**Status:** Planned

**Description:** Apply same configuration to multiple videos in one operation.

**Features:**
- Select multiple videos for processing
- Apply consistent settings across batch
- Parallel processing where possible
- Batch progress tracking
- Group outputs in batch-specific subfolder

**Example Workflow:**
```bash
uv run python src/tui/app.py --batch \
  --input-dir path/to/videos \
  --content-type tutorial \
  --aspect-ratio 9:16 \
  --output-dir output/batch_2025_01
```

---

## Human-in-the-Loop Workflow

### Caption Review & Editing
**Status:** Planned

**Description:** Interactive interface to review and edit AI-generated copies before finalizing.

**Features:**
- Display generated copies with metadata
- Edit copy text while maintaining character limit
- Preview engagement/viral scores
- Approve/reject individual copies
- Batch approve with filters

**UI Concept:**
```
Clip 1 (Viral - Score: 8.5/10)
Copy: "¿Sabías que el 90% de devs hacen esto mal? 😱 #AICDMX"
Chars: 62/150 | Engagement: 8.5 | Viral Potential: 7.8

[Edit] [Approve] [Reject] [Regenerate]
```

### Multiple Human-in-the-Loop Points
**Status:** Planned

**Description:** Identify and implement review/approval steps throughout pipeline.

**Planned Review Points:**

1. **After Clip Detection**
   - Review detected clips boundaries
   - Manually adjust start/end times
   - Merge or split clips
   - Remove unwanted clips

2. **After Classification**
   - Review viral/educational/storytelling assignments
   - Override AI classifications
   - Bulk reassign styles

3. **After Copy Generation**
   - Review and edit copies (see above)
   - Regenerate specific copies
   - Apply custom templates

4. **Before Export**
   - Preview clips with subtitles
   - Final quality check
   - Adjust export settings per clip

---

## Subtitle Customization

### Advanced Subtitle Styling
**Status:** Planned

**Current State:** Predefined styles (default, bold, yellow, tiktok, small, tiny)

**Planned Features:**

1. **Custom Font Settings**
   - Font family selection
   - Font size (absolute or relative)
   - Font weight (normal, bold, etc.)
   - Font color (hex/RGB)

2. **Subtitle Segmentation Control**
   - Max/min characters per subtitle
   - Max/min words per subtitle
   - Line break rules
   - Duration constraints

3. **Subtitle Display Types**

   **Type 1: Word-by-Word**
   - Display one word at a time
   - Karaoke-style progression
   - Adjustable word duration

   **Type 2: Key Words Only**
   - AI-extracted important words
   - Filter out filler words
   - Emphasize main concepts

   **Type 3: Multi-Word with Highlight**
   - Display multiple words
   - Highlight current word dynamically
   - Customizable highlight color
   - Smooth transitions

**Configuration Example:**
```python
subtitle_config = {
    "font": {
        "family": "Arial",
        "size": 48,
        "weight": "bold",
        "color": "#FFFFFF"
    },
    "segmentation": {
        "max_chars": 42,
        "min_chars": 10,
        "max_words": 8,
        "min_words": 2,
        "max_duration": 5.0
    },
    "display_type": "multi_word_highlight",
    "highlight_color": "#FFD700"
}
```

---

## Clipping Control

### Trim Mode (Preamble/Postamble Removal)
**Status:** Planned

**Description:** Mode to trim video start/end without AI clip detection.

**Use Cases:**
- Remove intro music or countdown
- Cut dead air at beginning/end
- Remove post-event chat
- Simple trim operations

**Features:**
- Manual trim point selection
- Preview trim result
- Preserve full transcript
- Skip clip detection pipeline

**Implementation Approach:**
- Add `--trim-mode` flag
- Interactive trim point selection
- Direct video export without clipping

---

## Prompt Management

### Markdown-Based Prompt System
**Status:** Planned

**Current State:** Prompts are Python strings in `.py` files

**Planned Structure:**
```
prompts/
  base/
    system_prompt.md
    json_format.md
  styles/
    viral.md
    educational.md
    storytelling.md
  classifier/
    classifier_prompt.md
  templates/
    custom_style_template.md
```

**Features:**
- Human-readable Markdown format
- Easier editing without Python knowledge
- Version control friendly
- Support for prompt templates
- Dynamic variable substitution

**Example Markdown Prompt:**
```markdown
# Viral Copy Generation

## Objective
Create copies that CAPTURE attention in 0.5 seconds.

## Hook Formulas
- Provocative questions: {{example_1}}
- Contradictions: {{example_2}}

## Rules
- Max {{max_chars}} characters
- ALWAYS include {{required_hashtag}}
```

---

## Output Management

### Custom Output Directory
**Status:** Planned

**Current State:** Outputs to `output/{video_id}/`

**Planned Features:**

1. **Custom Base Output Path**
   - CLI flag: `--output-dir path/to/output`
   - Environment variable: `CLIPER_OUTPUT_DIR`
   - Config file setting

2. **Batch Organization**
   - Group batch outputs in subfolder
   - Example: `output/batch_20250119/{video1, video2, ...}/`
   - Maintain individual video structure within batch

3. **Output Templates**
   - Customizable folder structure
   - Template variables: `{date}`, `{video_id}`, `{batch_name}`, `{content_type}`
   - Example: `output/{date}/{content_type}/{video_id}/`

---

## User Experience

### Clickable Video Links
**Status:** Planned

**Description:** Display clickable file:// URLs for exported videos in terminal output.

**Current State:** Shows file paths as text

**Planned Output:**
```
✓ Exported 10 clips

Clips exported to: file:///path/to/output/video_abc123/

  1.mp4 → file:///path/to/output/video_abc123/1.mp4
  2.mp4 → file:///path/to/output/video_abc123/2.mp4
  ...

Click links to open in default video player
```

**Implementation:**
- Rich library clickable links
- Platform detection (macOS/Linux/Windows)
- Option to open folder automatically

### Demo Logo Replacement
**Status:** Planned

**Current State:** Ships with AICDMX logo in `assets/logo.png`

**Planned:**
- Ship with generic demo logo
- Clear documentation on logo replacement
- Logo placement guide
- Optional: Logo generation wizard

---

## Implementation Priority

### Phase 1 (High Priority)
1. Flexible video input paths
2. Automated CLI mode
3. Custom output directory
4. Clickable video links

### Phase 2 (Medium Priority)
5. Caption review & editing
6. Bulk processing
7. Subtitle customization (font, color, size)
8. Trim mode

### Phase 3 (Future Enhancements)
9. Markdown-based prompts
10. Advanced subtitle types
11. Multiple human-in-the-loop points
12. Demo logo system

---

## Notes

- All v1 functionality remains unchanged and available
- v2 features are additive, not breaking changes
- Backward compatibility maintained for existing workflows
- Configuration files may be introduced for complex settings
