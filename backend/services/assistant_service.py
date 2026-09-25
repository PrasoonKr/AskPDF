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
    ):
        self.retrieval_pipeline = (
            retrieval_pipeline
        )

        self.context_builder = (
            context_builder
        )

        self.answer_generator = (
            answer_generator
        )

        self.conversation_formatter = (
            conversation_formatter
        )

        self.session_service = (
            session_service
        )

        self.trace_formatter = trace_formatter

    def create_session(self) -> str:

        return self.session_service.create_session()

    def delete_session(
        self,
        session_id: str,
    ):
        self.session_service.delete_session(
            session_id
        )

    def ask(self, session_id: str, question: str, cancel_flag: dict = None):
        
        memory = self.session_service.get_memory(session_id)
        
        summary = memory.get_summary()
        rewrite_history = memory.get_recent_turns(limit=ConversationConfig.GENERATION_HISTORY_TURNS)
        
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
            filename = result.document.source.filename
            stem = filename.replace('.pdf', '')
            doc_marker = f"[Document {index}]"
            
            # Check if LLM cited it by Document marker, or filename
            if doc_marker in answer or filename in answer or stem in answer:
                key = (filename, result.document.page)
                if key not in seen:
                    seen.add(key)
                    sources.append(
                        SourceResponse(
                            source=filename,
                            page=result.document.page,
                            score=result.score
                        )
                    )
                    
        # Fallback: if the LLM didn't explicitly format a citation, just list all the highly-relevant context we passed it
        if not sources:
            for result in results:
                key = (result.document.source.filename, result.document.page)
                if key not in seen:
                    seen.add(key)
                    sources.append(
                        SourceResponse(
                            source=result.document.source.filename,
                            page=result.document.page,
                            score=result.score
                        )
                    )

        # Clean citations from the text so they don't double up with the UI chips
        cleaned_answer = re.sub(r'\[[^\]]*(?:Page|page|PDF|pdf)\s*\d*[^\]]*\]', '', answer, flags=re.IGNORECASE)
        cleaned_answer = re.sub(r'\(\s*Source:[^\)]+\)', '', cleaned_answer, flags=re.IGNORECASE)
        cleaned_answer = re.sub(r'\[\d+\]', '', cleaned_answer)
        cleaned_answer = re.sub(r'\[Document\s*\d+\]', '', cleaned_answer, flags=re.IGNORECASE)
        
        for result in results:
            filename = result.document.source.filename
            stem = filename.replace('.pdf', '')
            cleaned_answer = cleaned_answer.replace(f"[{filename}]", "").replace(f"[{stem}]", "")
            
        if cancel_flag and cancel_flag.get("is_cancelled"):
            return ChatResponse(answer="Generation stopped.", sources=[], trace=None)
            
        memory.add_turn(user=question, assistant=cleaned_answer)
        
        trace_str = self.trace_formatter.format(trace) if self.trace_formatter else None
        
        return ChatResponse(
            answer=cleaned_answer,
            sources=sources,
            trace=trace_str
        )

    def ask_stream(self, session_id: str, question: str, cancel_flag: dict = None):
        import json
        import re

        memory = self.session_service.get_memory(session_id)
        summary = memory.get_summary()
        rewrite_history = memory.get_recent_turns(limit=ConversationConfig.GENERATION_HISTORY_TURNS)

        results, trace = self.retrieval_pipeline.search(
            query=question,
            recent_turns=rewrite_history,
            summary=summary
        )

        sources = []
        seen = set()
        for result in results:
            key = (result.document.source.filename, result.document.page)
            if key not in seen:
                seen.add(key)
                sources.append({
                    "source": result.document.source.filename,
                    "page": result.document.page,
                    "score": round(result.score, 3)
                })

        # Send retrieved sources metadata immediately so the UI can render source badges
        yield f"event: sources\ndata: {json.dumps(sources)}\n\n"

        context = self.context_builder.build(results)
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
            filename = result.document.source.filename
            stem = filename.replace('.pdf', '')
            cleaned_answer = cleaned_answer.replace(f"[{filename}]", "").replace(f"[{stem}]", "")

        memory.add_turn(user=question, assistant=cleaned_answer)
        yield f"event: done\ndata: {json.dumps({'answer': cleaned_answer})}\n\n"