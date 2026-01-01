# -*- coding: utf-8 -*-
from __future__ import annotations

import re
import json
import shutil
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from .events import JobStatusEvent, LogEvent, LogLevel, ProgressEvent, StateEvent
from .models import JobSpec, JobState, JobStatus, JobStep


EmitFn = Callable[[object], None]


class JobRunner:
    """
    Orquesta el pipeline usando las clases existentes pero emitiendo eventos
    UI-agnósticos para que Textual/CLI/GUI puedan observar el progreso.
    """

    def __init__(self, state_manager, emit: EmitFn):
        self.state_manager = state_manager
        self.emit = emit

    def run_job(self, job: JobSpec) -> JobStatus:
        status = JobStatus(progress_current=0, progress_total=len(job.video_ids) * max(1, len(job.steps)))
        status.mark_started()
        self.emit(JobStatusEvent(job_id=job.job_id, state=status.state))

        run_output_dir = self._ensure_run_output_dir(job_id=job.job_id, video_ids=job.video_ids)

        try:
            for video_id in job.video_ids:
                self._ensure_video_run_dir(run_output_dir=run_output_dir, video_id=video_id)
                for step in job.steps:
                    status.label = f"{step.value} ({video_id})"
                    self.emit(ProgressEvent(job_id=job.job_id, video_id=video_id, current=status.progress_current, total=status.progress_total, label=status.label))
                    self._run_step(job_id=job.job_id, video_id=video_id, step=step, settings=job.settings, run_output_dir=run_output_dir)
                    status.progress_current += 1
                    self.emit(ProgressEvent(job_id=job.job_id, video_id=video_id, current=status.progress_current, total=status.progress_total, label=status.label))

            status.mark_finished_ok()
            self.emit(JobStatusEvent(job_id=job.job_id, state=status.state))
            return status

        except Exception as e:
            status.mark_failed(str(e))
            self.emit(LogEvent(job_id=job.job_id, level=LogLevel.ERROR, message=f"Job failed: {e}"))
            self.emit(JobStatusEvent(job_id=job.job_id, state=status.state, error=str(e)))
            return status

    def _run_step(self, *, job_id: str, video_id: str, step: JobStep, settings: Dict[str, Any], run_output_dir: Path) -> None:
        if step == JobStep.TRANSCRIBE:
            self._step_transcribe(job_id=job_id, video_id=video_id, settings=settings.get("transcribe") or {}, run_output_dir=run_output_dir)
        elif step == JobStep.GENERATE_CLIPS:
            self._step_generate_clips(job_id=job_id, video_id=video_id, settings=settings.get("clips") or {}, run_output_dir=run_output_dir)
        elif step == JobStep.EXPORT_CLIPS:
            self._step_export_clips(job_id=job_id, video_id=video_id, settings=settings.get("export") or {}, run_output_dir=run_output_dir)
        elif step == JobStep.DOWNLOAD:
            raise ValueError("DOWNLOAD is not supported as a job step; use Add Videos to download and register.")
        else:
            raise ValueError(f"Unknown job step: {step}")

    def _slugify(self, value: str, *, max_len: int = 48) -> str:
        cleaned = (value or "").strip().lower()
        cleaned = cleaned.replace(" ", "_")
        cleaned = re.sub(r"[^a-z0-9._-]+", "_", cleaned)
        cleaned = re.sub(r"_+", "_", cleaned).strip("._-")
        return (cleaned or "run")[:max_len]

    def _ensure_run_output_dir(self, *, job_id: str, video_ids: list[str]) -> Path:
        input_stem = None
        if video_ids:
            first_video_path = self.state_manager.get_video_path(video_ids[0])
            if first_video_path:
                input_stem = Path(first_video_path).stem

        run_name = f"{self._slugify(input_stem or 'job')}_{job_id}"
        run_output_dir = Path("output") / "runs" / run_name
        run_output_dir.mkdir(parents=True, exist_ok=True)

        # Persist for UI / debugging.
        self.state_manager.update_job_status(job_id, {"run_output_dir": str(run_output_dir)})
        return run_output_dir

    def _ensure_video_run_dir(self, *, run_output_dir: Path, video_id: str) -> Path:
        video_dir = run_output_dir / video_id
        video_dir.mkdir(parents=True, exist_ok=True)
        return video_dir

    def _copy_if_exists(self, src: Path, dst: Path) -> Optional[Path]:
        if not src.exists():
            return None
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return dst

    def _rewrite_transcript_json_paths(self, transcript_path: Path, *, audio_path: Optional[Path] = None) -> None:
        if not transcript_path.exists() or transcript_path.suffix.lower() != ".json":
            return
        try:
            data = json.loads(transcript_path.read_text(encoding="utf-8"))
        except Exception:
            return
        if not isinstance(data, dict):
            return
        updated = False
        if audio_path and audio_path.exists():
            data["audio_path"] = str(audio_path)
            updated = True
        if updated:
            transcript_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _copy_exported_clip(self, src: Path, *, video_run_dir: Path) -> Optional[Path]:
        if not src.exists():
            return None
        try:
            export_idx = src.parts.index("export")
        except ValueError:
            export_idx = -1
        rel = Path(*src.parts[export_idx + 1 :]) if export_idx >= 0 else Path(src.name)
        dst = video_run_dir / "export" / rel
        return self._copy_if_exists(src, dst)

    def _get_video_path(self, video_id: str) -> str:
        path = self.state_manager.get_video_path(video_id)
        if not path:
            raise FileNotFoundError(f"Video path not registered for: {video_id}")
        return path

    def _step_transcribe(self, *, job_id: str, video_id: str, settings: Dict[str, Any], run_output_dir: Path) -> None:
        self.emit(LogEvent(job_id=job_id, video_id=video_id, level=LogLevel.INFO, message="Starting transcription"))

        video_path = self._get_video_path(video_id)
        if self.state_manager.is_transcribed(video_id) and settings.get("skip_done", True):
            state = self.state_manager.get_video_state(video_id) or {}
            transcript_existing = state.get("transcript_path") or state.get("transcription_path")
            copied_transcript: Optional[Path] = None
            copied_audio: Optional[Path] = None
            if transcript_existing:
                video_run_dir = self._ensure_video_run_dir(run_output_dir=run_output_dir, video_id=video_id)
                transcript_src = Path(transcript_existing)
                transcript_dst = video_run_dir / "transcribe" / transcript_src.name
                copied_transcript = self._copy_if_exists(transcript_src, transcript_dst)
                if copied_transcript:
                    self.state_manager.update_job_status(job_id, {"transcript_path": str(copied_transcript)})

            audio_src = Path("temp") / f"{Path(video_path).stem}_audio.wav"
            if audio_src.exists():
                video_run_dir = self._ensure_video_run_dir(run_output_dir=run_output_dir, video_id=video_id)
                audio_dst = video_run_dir / "transcribe" / audio_src.name
                copied_audio = self._copy_if_exists(audio_src, audio_dst)
                if copied_audio:
                    self.state_manager.update_job_status(job_id, {"transcript_audio_path": str(copied_audio)})
            if copied_transcript and copied_audio:
                self._rewrite_transcript_json_paths(copied_transcript, audio_path=copied_audio)
            self.emit(LogEvent(job_id=job_id, video_id=video_id, level=LogLevel.INFO, message="Already transcribed; skipping"))
            return

        from src.transcriber import Transcriber

        transcriber = Transcriber(
            model_size=settings.get("model", "base"),
            device=settings.get("device", "auto"),
            compute_type=settings.get("compute_type", "int8"),
        )
        transcript_path_raw = transcriber.transcribe(
            video_path=video_path,
            language=settings.get("language"),
            skip_if_exists=settings.get("skip_if_exists", True),
        )
        if not transcript_path_raw:
            raise RuntimeError("Transcription failed (no transcript returned)")

        transcript_src = Path(transcript_path_raw)
        video_run_dir = self._ensure_video_run_dir(run_output_dir=run_output_dir, video_id=video_id)
        transcript_dst = video_run_dir / "transcribe" / transcript_src.name
        copied_transcript = self._copy_if_exists(transcript_src, transcript_dst)
        transcript_path = str(copied_transcript or transcript_src)

        audio_src = Path("temp") / f"{Path(video_path).stem}_audio.wav"
        audio_dst = video_run_dir / "transcribe" / audio_src.name
        copied_audio = self._copy_if_exists(audio_src, audio_dst)
        if copied_transcript and copied_audio:
            self._rewrite_transcript_json_paths(copied_transcript, audio_path=copied_audio)

        self.state_manager.mark_transcribed(video_id, transcript_path)
        job_updates: Dict[str, object] = {"transcribed": True, "transcript_path": transcript_path}
        if copied_audio:
            job_updates["transcript_audio_path"] = str(copied_audio)
        self.state_manager.update_job_status(job_id, job_updates)
        self.emit(StateEvent(job_id=job_id, video_id=video_id, updates=job_updates))
        self.emit(LogEvent(job_id=job_id, video_id=video_id, level=LogLevel.INFO, message="Transcription complete"))

    def _step_generate_clips(self, *, job_id: str, video_id: str, settings: Dict[str, Any], run_output_dir: Path) -> None:
        self.emit(LogEvent(job_id=job_id, video_id=video_id, level=LogLevel.INFO, message="Generating clips"))

        state = self.state_manager.get_video_state(video_id) or {}
        transcript_path = state.get("transcript_path") or state.get("transcription_path")
        if not transcript_path:
            raise RuntimeError("No transcript_path found; run Transcribe first")

        if (state.get("clips_generated") or state.get("clips_metadata_path")) and settings.get("skip_done", True):
            clips_metadata_existing = state.get("clips_metadata_path")
            if clips_metadata_existing:
                video_run_dir = self._ensure_video_run_dir(run_output_dir=run_output_dir, video_id=video_id)
                metadata_src = Path(clips_metadata_existing)
                metadata_dst = video_run_dir / "clips" / metadata_src.name
                copied_metadata = self._copy_if_exists(metadata_src, metadata_dst)
                if copied_metadata:
                    self.state_manager.update_job_status(job_id, {"clips_metadata_path": str(copied_metadata)})
            self.emit(LogEvent(job_id=job_id, video_id=video_id, level=LogLevel.INFO, message="Clips already generated; skipping"))
            return

        from src.clips_generator import ClipsGenerator

        generator = ClipsGenerator(
            min_clip_duration=int(settings.get("min_seconds", 30)),
            max_clip_duration=int(settings.get("max_seconds", 90)),
        )
        clips = generator.generate_clips(
            transcript_path=transcript_path,
            min_clips=int(settings.get("min_clips", 3)),
            max_clips=int(settings.get("max_clips", 10)),
        )

        if not clips:
            raise RuntimeError("Clips generation failed (no clips returned)")

        video_run_dir = self._ensure_video_run_dir(run_output_dir=run_output_dir, video_id=video_id)
        clips_metadata_path = generator.save_clips_metadata(
            clips=clips,
            video_id=video_id,
            output_path=str(video_run_dir / "clips" / f"{video_id}_clips.json"),
        )

        self.state_manager.mark_clips_generated(video_id, clips or [], clips_metadata_path=clips_metadata_path)
        self.state_manager.update_job_status(job_id, {"clips_metadata_path": clips_metadata_path})
        self.emit(
            StateEvent(
                job_id=job_id,
                video_id=video_id,
                updates={
                    "clips_generated": True,
                    "clips_count": len(clips or []),
                    "clips_metadata_path": clips_metadata_path,
                },
            )
        )
        self.emit(LogEvent(job_id=job_id, video_id=video_id, level=LogLevel.INFO, message="Clips generation complete"))

    def _step_export_clips(self, *, job_id: str, video_id: str, settings: Dict[str, Any], run_output_dir: Path) -> None:
        self.emit(LogEvent(job_id=job_id, video_id=video_id, level=LogLevel.INFO, message="Exporting clips"))

        state = self.state_manager.get_video_state(video_id) or {}
        clips = state.get("clips") or []
        if not clips:
            raise RuntimeError("No clips in state; run Generate Clips first")

        if state.get("clips_exported") and settings.get("skip_done", True):
            existing_paths = [Path(p) for p in (state.get("exported_clips") or []) if p]
            video_run_dir = self._ensure_video_run_dir(run_output_dir=run_output_dir, video_id=video_id)
            copied: list[Path] = []
            for src in existing_paths:
                copied_path = self._copy_exported_clip(src, video_run_dir=video_run_dir)
                if copied_path:
                    copied.append(copied_path)

            mp4s = [p for p in copied if p.suffix.lower() == ".mp4" and p.exists()]
            final_mp4s = mp4s
            if not final_mp4s:
                final_mp4s = [p for p in existing_paths if p.suffix.lower() == ".mp4" and p.exists()]
            if final_mp4s:
                final = max(final_mp4s, key=lambda p: p.stat().st_mtime)
                self.state_manager.update_job_status(
                    job_id,
                    {"final_video_path": str(final), "final_video_paths": [str(p) for p in final_mp4s]},
                )

            self.emit(StateEvent(job_id=job_id, video_id=video_id, updates={"clips_exported": True, "exported_count": len(mp4s)}))
            self.emit(LogEvent(job_id=job_id, video_id=video_id, level=LogLevel.INFO, message="Clips already exported; skipping"))
            return

        from src.video_exporter import VideoExporter

        video_run_dir = self._ensure_video_run_dir(run_output_dir=run_output_dir, video_id=video_id)
        exporter = VideoExporter(output_dir=str(video_run_dir))
        exported_paths = exporter.export_clips(
            video_path=self._get_video_path(video_id),
            clips=clips,
            aspect_ratio=settings.get("aspect_ratio"),
            video_name="export",
            add_subtitles=bool(settings.get("add_subtitles", False)),
            transcript_path=state.get("transcript_path") or state.get("transcription_path"),
            subtitle_style=str(settings.get("subtitle_style", "default")),
            organize_by_style=bool(settings.get("organize_by_style", False)),
            clip_styles=state.get("clip_styles"),
            enable_face_tracking=bool(settings.get("enable_face_tracking", False)),
            face_tracking_strategy=str(settings.get("face_tracking_strategy", "keep_in_frame")),
            face_tracking_sample_rate=int(settings.get("face_tracking_sample_rate", 3)),
            add_logo=bool(settings.get("add_logo", False)),
            logo_path=settings.get("logo_path", "assets/logo.png"),
            logo_position=str(settings.get("logo_position", "top-right")),
            logo_scale=float(settings.get("logo_scale", 0.1)),
        )

        self.state_manager.mark_clips_exported(video_id, exported_paths, aspect_ratio=settings.get("aspect_ratio"))
        if exported_paths:
            self.state_manager.update_job_status(
                job_id,
                {
                    "final_video_path": str(Path(exported_paths[-1])),
                    "final_video_paths": [str(Path(p)) for p in exported_paths],
                },
            )
        self.emit(StateEvent(job_id=job_id, video_id=video_id, updates={"clips_exported": True, "exported_count": len(exported_paths)}))
        self.emit(LogEvent(job_id=job_id, video_id=video_id, level=LogLevel.INFO, message="Export complete"))
