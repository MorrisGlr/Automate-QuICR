import asyncio
import json
import os
from dataclasses import asdict
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from sse_starlette.sse import EventSourceResponse

from server.config import settings
from server.services.pipeline_service import (
    PipelineEvent,
    create_job,
    get_job_queue,
    remove_job,
    run_pipeline_for_files,
)

router = APIRouter()


@router.post("/inference")
async def start_inference(
    files: list[UploadFile] = File(...),
    model: str = Query(default=None),
    provider: str = Query(default="openai"),
    overwrite: bool = Query(default=False),
):
    model_name = model or settings.default_model

    # Validate and save uploaded files
    saved_filenames: list[str] = []
    for f in files:
        if not f.filename or not f.filename.endswith(".txt"):
            raise HTTPException(
                status_code=400,
                detail=f"Only .txt files are accepted (got: {f.filename})",
            )
        dest = settings.data_path / f.filename
        if dest.exists() and not overwrite:
            raise HTTPException(
                status_code=409,
                detail=f"File {f.filename} already exists. Use overwrite=true to replace.",
            )
        content = await f.read()
        dest.write_bytes(content)
        saved_filenames.append(f.filename)

    # Create job and launch pipeline
    job_id, queue = create_job()
    asyncio.create_task(
        run_pipeline_for_files(saved_filenames, model_name, provider, queue)
    )

    return {"job_id": job_id, "files": saved_filenames}


@router.get("/inference/status")
async def inference_status(job_id: str = Query(...)):
    queue = get_job_queue(job_id)
    if queue is None:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_stream() -> AsyncGenerator[dict, None]:
        while True:
            event: PipelineEvent = await queue.get()
            data = asdict(event)
            yield {"data": json.dumps(data)}
            if event.stage in ("all_complete",):
                remove_job(job_id)
                break

    return EventSourceResponse(event_stream())
