from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


class RouteType(str, Enum):
    SIMPLE_RAG = "simple_rag"
    MULTI_QUERY_RAG = "multi_query_rag"
    WEB_SEARCH = "web_search"


@dataclass
class RouteDecision:
    route: RouteType
    confidence: float
    reasoning: str
    sub_queries: List[str] = field(default_factory=list)


@dataclass
class GradeResult:
    is_relevant: bool
    confidence: float
    reasoning: str
    missing_aspects: List[str] = field(default_factory=list)
    filtered_documents: List[Any] = field(default_factory=list)


@dataclass
class AdaptiveStepTrace:
    step_number: int
    step_type: str
    query_used: str
    decision_or_grade: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AdaptiveRAGResult:
    route_chosen: RouteType
    total_attempts: int
    is_relevant: bool
    documents: List[Any]
    context_text: str
    trace: List[AdaptiveStepTrace] = field(default_factory=list)
    answer: Optional[str] = None
