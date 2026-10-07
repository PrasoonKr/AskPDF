from fastapi import APIRouter, Depends, Request
from starlette.responses import StreamingResponse
from sqlalchemy.orm import Session as DBSession
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
from backend.database.session import get_db
from backend.database import repository as repo

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
    db: DBSession = Depends(get_db),
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
        # Save user message to DB
        repo.add_message(db, chat_request.session_id, "user", chat_request.question)

        response = await run_in_threadpool(
            application.assistant_service.ask,
            chat_request.session_id,
            chat_request.question,
            cancel_flag
        )

        # Save assistant response to DB
        repo.add_message(
            db, chat_request.session_id, "assistant", response.answer,
            sources=[s.dict() for s in response.sources] if response.sources else None,
            trace=response.trace,
        )

        # Auto-title the session from the first question
        _auto_title_session(db, chat_request.session_id, chat_request.question)

        return response
    finally:
        task.cancel()


@router.post("/stream")
async def chat_stream(
    request: Request,
    chat_request: ChatRequest,
    application=Depends(get_application),
    current_user=Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    cancel_flag = {"is_cancelled": False}

    # Save user message to DB
    repo.add_message(db, chat_request.session_id, "user", chat_request.question)

    # Auto-title the session from the first question
    _auto_title_session(db, chat_request.session_id, chat_request.question)

    # We'll collect the full answer to save after streaming completes
    collected_answer = []
    collected_sources = []

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

                # Collect sources and final answer for DB persistence
                if isinstance(item, str):
                    if item.startswith("event: sources\n"):
                        try:
                            data_line = item.split("data: ", 1)[1].split("\n")[0]
                            collected_sources.extend(json.loads(data_line))
                        except Exception:
                            pass
                    elif item.startswith("event: done\n"):
                        try:
                            data_line = item.split("data: ", 1)[1].split("\n")[0]
                            done_data = json.loads(data_line)
                            collected_answer.append(done_data.get("answer", ""))
                        except Exception:
                            pass

                yield item
        except asyncio.CancelledError:
            cancel_flag["is_cancelled"] = True

        # Save assistant response to DB after streaming completes
        if collected_answer:
            repo.add_message(
                db, chat_request.session_id, "assistant",
                collected_answer[0],
                sources=collected_sources if collected_sources else None,
            )

    return StreamingResponse(
        sse_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


def _auto_title_session(db: DBSession, session_id: str, question: str):
    """Set the session title to the first question (truncated) if it's still 'New Chat'."""
    session = repo.get_session_by_id(db, session_id)
    if session and session.title == "New Chat":
        title = question[:60] + ("..." if len(question) > 60 else "")
        repo.update_session_title(db, session_id, title)