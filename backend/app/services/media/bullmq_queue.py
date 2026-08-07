"""
Professional AI - Media Job Queue (BullMQ-compatible Redis queue)
Replaces asyncio.Queue with a Redis-backed queue so jobs survive restarts
and multiple workers (Python or Node.js BullMQ) can process them.

Architecture:
  Python backend → Redis (BullMQ-format queue) → Workers (Python or Node.js BullMQ)

For production GPU server: run the Node.js media-worker service which uses
BullMQ to consume jobs. For development: Python workers consume directly.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from typing import Dict, Any, Optional
from loguru import logger

import redis.asyncio as aioredis

from app.config import settings
from app.models.media_engine import MediaJob, MediaStatus
from sqlalchemy import select


class BullMQCompatibleQueue:
    """
    Redis-backed job queue compatible with BullMQ format.
    Pushes jobs to Redis in the format BullMQ expects,
    so Node.js media-worker can consume them.
    """

    QUEUE_NAME = "media-vault:jobs"
    PROGRESS_PREFIX = "media-vault:progress"
    BULLMQ_PREFIX = "bq:media-vault"

    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None
        self._python_workers: list = []
        self._running = False
        self._output_dir = os.path.join(settings.MEDIA_OUTPUT_DIR)
        os.makedirs(self._output_dir, exist_ok=True)

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(
                settings.REDIS_URL,
                password=getattr(settings, "REDIS_PASSWORD", None),
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=10,
                retry_on_timeout=True,
                health_check_interval=30,
            )
        return self._redis

    async def start(self, num_workers: int = None):
        """Start Python worker pool (for development / fallback)."""
        if self._running:
            return
        self._running = True
        num_workers = num_workers or settings.MEDIA_QUEUE_MAX_WORKERS
        for i in range(num_workers):
            task = asyncio.create_task(self._python_worker_loop(i))
            self._python_workers.append(task)
        logger.info(f"Media queue started with {num_workers} Python workers + BullMQ compatibility")

    async def shutdown(self):
        self._running = False
        for w in self._python_workers:
            w.cancel()
        for w in self._python_workers:
            try:
                await w
            except asyncio.CancelledError:
                pass
        self._python_workers.clear()
        if self._redis:
            await self._redis.aclose()
            self._redis = None

    async def enqueue(self, job_id: str) -> str:
        """
        Push a job to the Redis queue in BullMQ-compatible format.
        Returns the BullMQ job ID.
        """
        r = await self._get_redis()
        job_uuid = str(uuid.uuid4())
        timestamp = int(time.time() * 1000)

        # Store full job data in BullMQ format
        job_data = {
            "id": job_uuid,
            "name": f"media-{job_id}",
            "data": json.dumps({"job_id": job_id}),
            "opts": json.dumps({}),
            "timestamp": str(timestamp),
            "processedOn": "0",
            "finishedOn": "0",
            "duration": "0",
            "returnvalue": "",
            "failedReason": "",
            "stacktrace": json.dumps([]),
            "progress": json.dumps({}),
        }

        pipe = r.pipeline()
        pipe.hset(f"{self.BULLMQ_PREFIX}:jobs:{job_uuid}", mapping=job_data)
        pipe.zadd(f"{self.BULLMQ_PREFIX}:waiting", {job_uuid: timestamp})
        pipe.lpush(f"{self.QUEUE_NAME}:list", job_uuid)  # for Python workers
        pipe.expire(f"{self.BULLMQ_PREFIX}:jobs:{job_uuid}", 86400)
        await pipe.execute()

        logger.debug(f"Enqueued media job {job_id} as BullMQ job {job_uuid}")
        return job_uuid

    async def _python_worker_loop(self, worker_id: int):
        """Python worker that pulls from Redis list (fallback / dev)."""
        r = await self._get_redis()
        while self._running:
            try:
                # BRPOP blocks until an item is available (timeout 5s for graceful shutdown)
                result = await r.brpop(f"{self.QUEUE_NAME}:list", timeout=5)
                if result is None:
                    continue
                _, job_uuid = result
                await self._process_bullmq_job(job_uuid, worker_id)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Python worker {worker_id} error: {e}")
                await asyncio.sleep(1)

    async def _process_bullmq_job(self, job_uuid: str, worker_id: int):
        """Process a BullMQ-compatible job (Python worker path)."""
        from app.database import _get_session_factory
        from app.services.media.generation import media_generation_service
        from app.services.media.voice_over import voice_over_service
        from app.services.media.storyboard import storyboard_service
        from app.services.media.subtitle_verify import subtitle_verification_service, generate_srt
        from app.services.media.upscaler import upscaler_service

        r = await self._get_redis()
        job_key = f"{self.BULLMQ_PREFIX}:jobs:{job_uuid}"
        raw = await r.hget(job_key, "data")
        if not raw:
            return
        job_data = json.loads(raw)
        job_id = job_data.get("job_id")
        if not job_id:
            return

        factory = _get_session_factory()
        async with factory() as db:
            result = await db.execute(select(MediaJob).where(MediaJob.id == job_id))
            job = result.scalar_one_or_none()
            if not job:
                return

            logger.info(f"Python worker {worker_id} processing job {job_id}")

            # Mark as active in BullMQ format
            now_ms = int(time.time() * 1000)
            await r.hset(job_key, "processedOn", str(now_ms))
            await r.zadd(f"{self.BULLMQ_PREFIX}:active", {job_uuid: now_ms})
            await r.zrem(f"{self.BULLMQ_PREFIX}:waiting", job_uuid)

            try:
                await self._update_job(db, job, MediaStatus.GENERATING, 5, "Starting")
                await self._report_progress(job_id, "starting", 0, "GPU worker processing")

                # Stage 1: Storyboard
                await self._update_job(db, job, MediaStatus.STORYBOARDING, 5, "Building storyboard")
                await self._report_progress(job_id, "storyboarding", 5, "Building storyboard")
                sb = await storyboard_service.build_storyboard(
                    topic=job.topic, script=job.script,
                    scenes_text=job.scenes_text, duration_seconds=job.duration_seconds,
                )
                job.storyboard = sb["scenes"]
                job.scene_count = sb["total_scenes"]
                await db.flush()

                for sd in sb["scenes"]:
                    db.add(MediaScene(
                        job_id=job.id, scene_number=sd["scene_number"],
                        description=sd["description"], prompt=sd["prompt"],
                        duration_seconds=sd.get("duration_seconds", 5.0), status="pending",
                    ))
                await db.flush()

                # Stage 2: Generate scenes
                await self._update_job(db, job, MediaStatus.GENERATING, 20, "Generating scenes")
                await self._report_progress(job_id, "generating_scenes", 20, "Generating scenes")
                scenes_res = await db.execute(
                    select(MediaScene).where(MediaScene.job_id == job.id).order_by(MediaScene.scene_number)
                )
                scenes = scenes_res.scalars().all()
                width, height = self._get_dimensions(
                    job.resolution.value if job.resolution else "8k", job.aspect_ratio
                )

                for i, scene in enumerate(scenes):
                    scene.status = "generating"
                    await db.flush()
                    try:
                        if job.job_type == MediaType.VIDEO:
                            gen = await media_generation_service.generate_video(
                                prompt=scene.prompt, duration_seconds=int(scene.duration_seconds),
                                width=width, height=height, engine=job.model or "kling",
                            )
                        elif job.job_type in (MediaType.PICTURE, MediaType.POSTER):
                            gen = await media_generation_service.generate_image(
                                prompt=scene.prompt, negative_prompt=job.negative_prompt,
                                width=width, height=height, model=job.model or "flux",
                            )
                        else:
                            gen = await media_generation_service.generate_animation(
                                prompt=scene.prompt, duration_seconds=int(scene.duration_seconds),
                                width=width, height=height,
                            )
                        if gen.get("success"):
                            scene.output_path = gen.get("path")
                            scene.status = "generated"
                        else:
                            scene.status = "failed"
                    except Exception as e:
                        scene.status = "failed"
                        logger.error(f"Scene {scene.scene_number} failed: {e}")
                    await db.flush()
                    progress = 20 + int(((i + 1) / max(len(scenes), 1)) * 30)
                    await self._update_job(db, job, MediaStatus.GENERATING, progress, f"Scene {i+1}/{len(scenes)}")
                    await self._report_progress(job_id, "generating_scenes", progress, f"Scene {i+1}/{len(scenes)}")

                # Stage 3: Voice over
                if job.script and job.script.strip():
                    await self._update_job(db, job, MediaStatus.VOICE_OVER, 55, "Voice over")
                    await self._report_progress(job_id, "voice_over", 55, "Generating voice")
                    try:
                        vo = await voice_over_service.generate_voice_over(
                            script=job.script,
                            voice_style=job.voice_style.value if job.voice_style else "adult_female",
                            voice_prompt=job.voice_prompt,
                            language=job.language or "en",
                            voice_clone_id=str(job.voice_clone_id) if job.voice_clone_id else None,
                        )
                        if vo.get("success"):
                            job.voice_over_path = vo.get("path")
                            job.voice_over_status = "completed"
                        else:
                            job.voice_over_status = "failed"
                    except Exception as e:
                        job.voice_over_status = "failed"
                        logger.warning(f"Voice over failed: {e}")
                    await db.flush()

                # Stage 4: Subtitles
                if job.script and job.script.strip():
                    await self._update_job(db, job, MediaStatus.SUBTITLING, 70, "Subtitles")
                    await self._report_progress(job_id, "subtitling", 70, "Generating subtitles")
                    srt_path = os.path.join(self._output_dir, f"subs_{job.id}.srt")
                    srt_content = generate_srt(job.script, job.duration_seconds or 15)
                    with open(srt_path, "w", encoding="utf-8") as f:
                        f.write(srt_content)
                    job.subtitles_path = srt_path
                    job.subtitle_verify_status = "generated"
                    await db.flush()

                    if settings.MEDIA_SUBTITLE_VERIFY_ENABLED:
                        await self._update_job(db, job, MediaStatus.VERIFYING, 80, "Verifying subtitles")
                        await self._report_progress(job_id, "verifying", 80, "Verifying subtitles")
                        verify = await subtitle_verification_service.verify_subtitles(
                            script=job.script, subtitle_path=srt_path, language=job.language or "en",
                        )
                        job.verification_report = verify
                        job.accuracy_verified = verify.get("passed", False)
                        job.subtitle_verify_status = "verified" if verify.get("passed") else "failed"
                        await db.flush()

                # Stage 5: Upscale
                await self._update_job(db, job, MediaStatus.UPSCALING, 90, "Upscaling")
                await self._report_progress(job_id, "upscaling", 90, "Upscaling output")
                scenes_res2 = await db.execute(
                    select(MediaScene).where(MediaScene.job_id == job.id).order_by(MediaScene.scene_number)
                )
                scenes2 = scenes_res2.scalars().all()
                if scenes2 and scenes2[0].output_path:
                    try:
                        up = await upscaler_service.upscale_image(
                            scenes2[0].output_path, job.resolution.value if job.resolution else "8k",
                        )
                        if up.get("success"):
                            job.output_path = up.get("path")
                            job.output_resolution = up.get("resolution", "8k")
                        else:
                            job.output_path = scenes2[0].output_path
                    except Exception:
                        job.output_path = scenes2[0].output_path
                elif scenes2:
                    job.output_path = scenes2[0].output_path

                # Complete
                if job.output_path and os.path.exists(job.output_path):
                    job.output_size_bytes = os.path.getsize(job.output_path)
                job.status = MediaStatus.COMPLETED
                job.progress = 100.0
                job.progress_stage = "Completed"
                job.completed_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
                await db.commit()

                await self._report_progress(job_id, "completed", 100, "Job completed")
                await r.hset(job_key, mapping={
                    "status": "completed",
                    "finishedOn": str(int(time.time() * 1000)),
                    "returnvalue": json.dumps({"success": True, "path": job.output_path}),
                })
                await r.zadd(f"{self.BULLMQ_PREFIX}:completed", {job_uuid: int(time.time() * 1000)})
                await r.zrem(f"{self.BULLMQ_PREFIX}:active", job_uuid)
                logger.info(f"Job {job_id} completed by Python worker {worker_id}")

            except Exception as e:
                logger.error(f"Job {job_id} failed: {e}")
                job.status = MediaStatus.FAILED
                job.error_message = str(e)[:500]
                job.progress_stage = "Failed"
                await db.commit()
                await self._report_progress(job_id, "failed", 0, str(e))
                await r.hset(job_key, mapping={
                    "status": "failed",
                    "finishedOn": str(int(time.time() * 1000)),
                    "failedReason": str(e)[:500],
                    "stacktrace": json.dumps([]),
                })
                await r.zadd(f"{self.BULLMQ_PREFIX}:failed", {job_uuid: int(time.time() * 1000)})
                await r.zrem(f"{self.BULLMQ_PREFIX}:active", job_uuid)

    async def _update_job(self, db, job, status, progress, stage):
        job.status = status
        job.progress = float(progress)
        job.progress_stage = stage
        await db.flush()

    async def _report_progress(self, job_id: str, stage: str, progress: float, message: str):
        r = await self._get_redis()
        key = f"{self.PROGRESS_PREFIX}:{job_id}"
        await r.hset(key, {
            "stage": stage,
            "progress": str(progress),
            "message": message,
            "updated_at": str(int(time.time() * 1000)),
        })
        await r.expire(key, 3600)

    @staticmethod
    def _get_dimensions(resolution: str, aspect_ratio: str = "16:9") -> tuple:
        targets = {"720p": (1280, 720), "1080p": (1920, 1080), "4k": (3840, 2160), "8k": (7680, 4320)}
        base = targets.get(resolution, targets["8k"])
        if aspect_ratio == "9:16":
            return base[1], base[0]
        if aspect_ratio == "1:1":
            s = min(base)
            return s, s
        return base


# Singleton
media_queue_service = BullMQCompatibleQueue()
