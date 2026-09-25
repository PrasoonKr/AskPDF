from fastapi import APIRouter, Depends, Request
from starlette.responses import StreamingResponse
import asyncio
import queue
import threading
import json
from fastapi.concurrency import run_in_threadpool

from backend.api.dependencies import (
    get_application,
    get_current_user,
)

from backend.api.schemas.chat import (
    ChatRequest,
)

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post("")
async def chat(
    request: Request,
    chat_request: ChatRequest,
    application=Depends(get_application),
    current_user=Depends(get_current_user),
):
    cancel_flag = {"is_cancelled": False}

    async def check_disconnect():
        while True:
            if await request.is_disconnected():
                cancel_flag["is_cancelled"] = True
                break
            await asyncio.sleep(0.5)

    task = asyncio.create_task(check_disconnect())

    try:
        response = await run_in_threadpool(
            application.assistant_service.ask,
            chat_request.session_id,
            chat_request.question,
            cancel_flag
        )
        return response
    finally:
        task.cancel()


@router.post("/stream")
async def chat_stream(
    request: Request,
    chat_request: ChatRequest,
    application=Depends(get_application),
    current_user=Depends(get_current_user),
):
    cancel_flag = {"is_cancelled": False}

    async def sse_event_generator():
        q = queue.Queue()
        sentinel = object()

        def worker():
            try:
                for chunk in application.assistant_service.ask_stream(
                    chat_request.session_id,
                    chat_request.question,
                    cancel_flag
                ):
                    q.put(chunk)
            except Exception as e:
                q.put(f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n")
            finally:
                q.put(sentinel)

        t = threading.Thread(target=worker, daemon=True)
        t.start()

        try:
            while True:
                if await request.is_disconnected():
                    cancel_flag["is_cancelled"] = True
                    break

                try:
                    item = q.get_nowait()
                except queue.Empty:
                    await asyncio.sleep(0.015)
                    continue

                if item is sentinel:
                    break
                yield item
        except asyncio.CancelledError:
            cancel_flag["is_cancelled"] = True

    return StreamingResponse(
        sse_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )