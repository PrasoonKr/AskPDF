from backend.config import ConversationConfig
from backend.prompts.builder import build_prompt
from backend.api.schemas.chat import ChatResponse, SourceResponse

class ResearchAssistantService:

    def __init__(
        self,
        retrieval_pipeline,
        context_builder,
        answer_generator,
        conversation_formatter,
        session_service,
        trace_formatter=None,
        adaptive_pipeline=None,
    ):
        self.retrieval_pipeline = retrieval_pipeline
        self.context_builder = context_builder
        self.answer_generator = answer_generator
        self.conversation_formatter = conversation_formatter
        self.session_service = session_service
        self.trace_formatter = trace_formatter
        self.adaptive_pipeline = adaptive_pipeline
        self._session_map = {}  # DB session ID -> in-memory session ID

    def create_session(self) -> str:

        return self.session_service.create_session()

    def map_session(self, db_session_id: str, memory_session_id: str):
        """Map a persistent DB session ID to an in-memory RAG session ID."""
        self._session_map[db_session_id] = memory_session_id

    def _resolve_session(self, session_id: str) -> str:
        """Resolve a DB session ID to the in-memory session ID, creating one if needed."""
        if session_id in self._session_map:
            return self._session_map[session_id]
        # If no mapping exists, create a new in-memory session and map it
        memory_id = self.session_service.create_session()
        self._session_map[session_id] = memory_id
        return memory_id

    def delete_session(
        self,
        session_id: str,
    ):
        self.session_service.delete_session(
            session_id
        )

    def ask(self, session_id: str, question: str, cancel_flag: dict = None):
        memory_id = self._resolve_session(session_id)
        memory = self.session_service.get_memory(memory_id)
        
        summary = memory.get_summary()
        rewrite_history = memory.get_recent_turns(limit=ConversationConfig.GENERATION_HISTORY_TURNS)
        
        trace = None
        if self.adaptive_pipeline:
            adaptive_result = self.adaptive_pipeline.execute(
                query=question,
                recent_turns=rewrite_history,
                summary=summary,
            )
            context = adaptive_result.context_text
            results = adaptive_result.documents
        else:
            results, trace = self.retrieval_pipeline.search(
                query=question,
                recent_turns=rewrite_history,
                summary=summary
            )
            context = self.context_builder.build(results)
        
        generation_history = memory.get_recent_turns(limit=ConversationConfig.GENERATION_HISTORY_TURNS)
        formatted_conversation = self.conversation_formatter.format(generation_history)
        
        prompt = build_prompt(
            query=question,
            context=context,
            conversation=formatted_conversation,
            conversation_summary=summary
        )
        
        import re
        
        answer = self.answer_generator.generate(prompt)
        
        sources = []
        seen = set()
        for index, result in enumerate(results, start=1):
            if isinstance(result, dict):
                src_label = result.get("source", "Web Search")
                if src_label not in seen:
                    seen.add(src_label)
                    sources.append(SourceResponse(source=src_label, page=1, score=1.0))
            else:
                doc_obj = getattr(result, "document", result)
                filename = getattr(getattr(doc_obj, "source", None), "filename", "Document")
                page = getattr(doc_obj, "page", 1)
                score = getattr(result, "score", 1.0)
                stem = filename.replace('.pdf', '')
                doc_marker = f"[Document {index}]"
                
                if doc_marker in answer or filename in answer or stem in answer:
                    key = (filename, page)
                    if key not in seen:
                        seen.add(key)
                        sources.append(
                            SourceResponse(
                                source=filename,
                                page=page,
                                score=round(score, 3)
                            )
                        )
                    
        # Fallback: if the LLM didn't explicitly format a citation, list all retrieved context
        if not sources:
            for result in results:
                if isinstance(result, dict):
                    src_label = result.get("source", "Web Search")
                    if src_label not in seen:
                        seen.add(src_label)
                        sources.append(SourceResponse(source=src_label, page=1, score=1.0))
                else:
                    doc_obj = getattr(result, "document", result)
                    filename = getattr(getattr(doc_obj, "source", None), "filename", "Document")
                    page = getattr(doc_obj, "page", 1)
                    score = getattr(result, "score", 1.0)
                    key = (filename, page)
                    if key not in seen:
                        seen.add(key)
                        sources.append(
                            SourceResponse(
                                source=filename,
                                page=page,
                                score=round(score, 3)
                            )
                        )

        # Clean citations from the text so they don't double up with the UI chips
        cleaned_answer = re.sub(r'\[[^\]]*(?:Page|page|PDF|pdf)\s*\d*[^\]]*\]', '', answer, flags=re.IGNORECASE)
        cleaned_answer = re.sub(r'\(\s*Source:[^\)]+\)', '', cleaned_answer, flags=re.IGNORECASE)
        cleaned_answer = re.sub(r'\[\d+\]', '', cleaned_answer)
        cleaned_answer = re.sub(r'\[Document\s*\d+\]', '', cleaned_answer, flags=re.IGNORECASE)
        
        for result in results:
            if not isinstance(result, dict):
                doc_obj = getattr(result, "document", result)
                filename = getattr(getattr(doc_obj, "source", None), "filename", "")
                if filename:
                    stem = filename.replace('.pdf', '')
                    cleaned_answer = cleaned_answer.replace(f"[{filename}]", "").replace(f"[{stem}]", "")
            
        if cancel_flag and cancel_flag.get("is_cancelled"):
            return ChatResponse(answer="Generation stopped.", sources=[], trace=None)
            
        memory.add_turn(user=question, assistant=cleaned_answer)
        
        trace_str = self.trace_formatter.format(trace) if (trace and self.trace_formatter) else None
        
        return ChatResponse(
            answer=cleaned_answer,
            sources=sources,
            trace=trace_str
        )

    def ask_stream(self, session_id: str, question: str, cancel_flag: dict = None):
        import json
        import re
        memory_id = self._resolve_session(session_id)
        memory = self.session_service.get_memory(memory_id)
        summary = memory.get_summary()
        rewrite_history = memory.get_recent_turns(limit=ConversationConfig.GENERATION_HISTORY_TURNS)

        if self.adaptive_pipeline:
            adaptive_result = self.adaptive_pipeline.execute(
                query=question,
                recent_turns=rewrite_history,
                summary=summary,
            )
            context = adaptive_result.context_text
            results = adaptive_result.documents
        else:
            results, trace = self.retrieval_pipeline.search(
                query=question,
                recent_turns=rewrite_history,
                summary=summary
            )
            context = self.context_builder.build(results)

        sources = []
        seen = set()
        for result in results:
            if isinstance(result, dict):
                src_label = result.get("source", "Web Search")
                if src_label not in seen:
                    seen.add(src_label)
                    sources.append({
                        "source": src_label,
                        "page": 1,
                        "score": 1.0
                    })
            else:
                doc_obj = getattr(result, "document", result)
                filename = getattr(getattr(doc_obj, "source", None), "filename", "Document")
                page = getattr(doc_obj, "page", 1)
                score = getattr(result, "score", 1.0)
                key = (filename, page)
                if key not in seen:
                    seen.add(key)
                    sources.append({
                        "source": filename,
                        "page": page,
                        "score": round(score, 3)
                    })

        # Send retrieved sources metadata immediately so the UI can render source badges
        yield f"event: sources\ndata: {json.dumps(sources)}\n\n"

        generation_history = memory.get_recent_turns(limit=ConversationConfig.GENERATION_HISTORY_TURNS)
        formatted_conversation = self.conversation_formatter.format(generation_history)

        prompt = build_prompt(
            query=question,
            context=context,
            conversation=formatted_conversation,
            conversation_summary=summary
        )

        full_answer = []
        for token in self.answer_generator.generate_stream(prompt):
            if cancel_flag and cancel_flag.get("is_cancelled"):
                break
            full_answer.append(token)
            yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"

        combined = "".join(full_answer)
        cleaned_answer = re.sub(r'\[[^\]]*(?:Page|page|PDF|pdf)\s*\d*[^\]]*\]', '', combined, flags=re.IGNORECASE)
        cleaned_answer = re.sub(r'\(\s*Source:[^\)]+\)', '', cleaned_answer, flags=re.IGNORECASE)
        cleaned_answer = re.sub(r'\[\d+\]', '', cleaned_answer)
        cleaned_answer = re.sub(r'\[Document\s*\d+\]', '', cleaned_answer, flags=re.IGNORECASE)
        for result in results:
            if not isinstance(result, dict):
                doc_obj = getattr(result, "document", result)
                filename = getattr(getattr(doc_obj, "source", None), "filename", "")
                if filename:
                    stem = filename.replace('.pdf', '')
                    cleaned_answer = cleaned_answer.replace(f"[{filename}]", "").replace(f"[{stem}]", "")

        memory.add_turn(user=question, assistant=cleaned_answer)
        yield f"event: done\ndata: {json.dumps({'answer': cleaned_answer})}\n\n"