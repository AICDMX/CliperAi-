# Getting Started with CLIPER

## Installation in 3 Steps

### 1. Clone and Install Dependencies

```bash
git clone https://github.com/opino-tech/cliper.git
cd cliper
uv sync
```

**Requirements:**
- Python 3.9+
- FFmpeg
- macOS or Linux (Docker available for other platforms)

### 2. Configure Your Environment (Interactive Setup)

We provide an interactive setup script that asks you questions and creates your `.env` file:

```bash
python setup.py
```

This will guide you through:
- **API Key** (required) - Your Google Gemini API key
- **Transcription Settings** - Whisper model size and language
- **Clip Generation** - Min/max clip duration
- **AI Caption Settings** - Model and style preferences
- **Video Export** - Quality and subtitle settings

**Custom output path?** Use the `--output` flag:
```bash
python setup.py --output=.env.demo
python setup.py --output=/etc/cliper/.env
```

**No API key yet?** Get a free one at https://aistudio.google.com/app/apikey

### 3. Run CLIPER

Choose your interface:

**Textual TUI (Recommended):**
```bash
uv run -m src.tui.app
```

**Legacy CLI (prompt-loop):**
```bash
uv run cliper.py
```

---

## What Happens Next?

### CLI Workflow
1. Provide a YouTube URL or local video file
2. CLIPER processes through its pipeline
3. Clips appear in the `output/` directory
4. Publish directly to social platforms

### TUI Workflow
1. Press `a` to add videos (YouTube URL or local paths)
2. Select videos with `space`
3. Queue jobs with `t` (transcribe), `c` (clips), `e` (export)
4. Watch job progress + logs in the right panel

---

## Understanding Output

Your processed clips are organized by style:

```
output/
├── viral/          # High-engagement, hook-driven clips
├── educational/    # Value-focused, educational clips
└── storytelling/   # Narrative-driven, emotional clips
```

Each clip includes:
- Optimized video file
- Synchronized subtitles
- Metadata (captions, timings, styling)

---

## Configuration

### Manual Setup (Without Interactive Script)

If you prefer to set up manually:

1. Copy the template:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your settings (see `.env.example` for all options)

3. Most important: Set your API key
   ```bash
   GOOGLE_API_KEY=your_gemini_api_key_here
   ```

### Environment Variables

**Required:**
- `GOOGLE_API_KEY` - Your Gemini API key

**Optional (sensible defaults provided):**
- `WHISPER_MODEL` - Transcription accuracy (tiny, base, small, medium, large)
- `MIN_CLIP_DURATION` - Minimum clip length in seconds
- `MAX_CLIP_DURATION` - Maximum clip length in seconds
- `GEMINI_MODEL` - Which model to use for captions
- `COPY_STYLE` - Caption generation style (auto, viral, educational, storytelling)
- `VIDEO_CRF` - Video quality (18-28, lower = better)

---

## Troubleshooting

### "API key not found"
- Ensure `.env` file exists in the project root
- Verify `GOOGLE_API_KEY` is set with a valid key
- Run `python setup.py` to reconfigure

### "Transcription failed"
- Check video has clear audio
- Verify FFmpeg is installed: `ffmpeg -version`
- Try a different Whisper model size

### "No clips generated"
- Video may be too short or lack clear topic boundaries
- Try adjusting `MIN_CLIP_DURATION` and `MAX_CLIP_DURATION` in `.env`
- Check logs for detailed error messages

### "GUI won't start"
- Ensure tkinter is installed: `apt install python3-tk` (Linux) or `brew install python-tk` (macOS)
- Check Python version: `python --version` (should be 3.9+)

---

## Docker Setup

For reproducible, containerized deployment:

```bash
docker-compose build
docker-compose run cliper
```

---

## Next Steps

- Read the [full documentation](../README.md)
- Check [Architecture](ARCHITECTURE.md) for technical details
- See [Advanced Features](ADVANCED.md) for production use cases

---

**Ready to transform your videos?** Run `python setup.py` and get started!
