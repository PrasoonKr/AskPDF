from dataclasses import dataclass

from backend.services.assistant_service import (
    ResearchAssistantService,
)

from backend.services.ingestion_service import (
    IngestionService,
)


@dataclass(slots=True)
class Application:

    assistant_service: ResearchAssistantService

    ingestion_service: IngestionService