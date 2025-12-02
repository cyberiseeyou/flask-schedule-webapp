# RAG Implementation Plan: AI-Powered Scheduling Assistant

## Project Overview

**Goal:** Integrate an AI assistant into the Flask Schedule Webapp that can answer questions about schedules, suggest optimizations, detect conflicts, and provide intelligent insights—all grounded in real-time data from your database.

**Approach:** Retrieval-Augmented Generation (RAG) with local LLM (Ollama + DeepSeek-R1:8b)

**Estimated Timeline:** 3-4 weeks for full implementation

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Feature List & Rationale](#2-feature-list--rationale)
3. [Prerequisites & Setup](#3-prerequisites--setup)
4. [Phase 1: Foundation](#4-phase-1-foundation-week-1)
5. [Phase 2: Context Retrieval System](#5-phase-2-context-retrieval-system-week-2)
6. [Phase 3: AI Service Integration](#6-phase-3-ai-service-integration-week-2-3)
7. [Phase 4: API Endpoints & Frontend](#7-phase-4-api-endpoints--frontend-week-3)
8. [Phase 5: Production Hardening](#8-phase-5-production-hardening-week-4)
9. [Testing Strategy](#9-testing-strategy)
10. [Backup & Rollback Plan](#10-backup--rollback-plan)
11. [Future Enhancements](#11-future-enhancements)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Flask Schedule Webapp                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐    ┌──────────────────┐    ┌───────────────────────┐ │
│  │   Frontend   │───▶│  /ai/chat API    │───▶│  AI Service Layer     │ │
│  │  (Chat UI)   │    │  /ai/suggestions │    │                       │ │
│  └──────────────┘    └──────────────────┘    │  ┌─────────────────┐  │ │
│                                              │  │ Query Classifier │  │ │
│                                              │  └────────┬────────┘  │ │
│                                              │           │           │ │
│                                              │  ┌────────▼────────┐  │ │
│                                              │  │Context Retriever│  │ │
│                                              │  └────────┬────────┘  │ │
│                                              │           │           │ │
│                                              │  ┌────────▼────────┐  │ │
│                                              │  │ Prompt Builder  │  │ │
│                                              │  └────────┬────────┘  │ │
│                                              │           │           │ │
│                                              └───────────┼───────────┘ │
│                                                          │             │
│  ┌──────────────────────────────────────┐    ┌──────────▼───────────┐ │
│  │          PostgreSQL/SQLite           │    │    LLM Provider      │ │
│  │  ┌─────────┐ ┌─────────┐ ┌────────┐  │    │  ┌────────────────┐  │ │
│  │  │Employee │ │ Event   │ │Schedule│  │    │  │ Ollama (local) │  │ │
│  │  │Avail.   │ │TimeOff  │ │Rotation│  │    │  │ DeepSeek-R1:8b │  │ │
│  │  └─────────┘ └─────────┘ └────────┘  │    │  └────────────────┘  │ │
│  └──────────────────────────────────────┘    │         or           │ │
│                                              │  ┌────────────────┐  │ │
│                                              │  │ Cloud API      │  │ │
│                                              │  │ (fallback)     │  │ │
│                                              │  └────────────────┘  │ │
│                                              └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. User submits question via chat interface
2. Query classifier determines what type of question it is
3. Context retriever fetches relevant data from database
4. Prompt builder constructs optimized prompt with context
5. LLM generates response grounded in retrieved data
6. Response returned to user with optional citations

---

## 2. Feature List & Rationale

### Core Features

| Feature | Description | Why It's Important | How It Works |
|---------|-------------|-------------------|--------------|
| **Natural Language Queries** | Ask questions like "Who can work Friday?" | Reduces friction for managers; no need to navigate complex UI | Query classifier + context retrieval + LLM |
| **Schedule Conflict Detection** | "Are there any conflicts next week?" | Prevents scheduling errors before they happen | Queries overlapping schedules, flags issues |
| **Employee Recommendations** | "Who should I assign to Event X?" | Leverages skills, availability, workload balance | Scores employees based on multiple factors |
| **Availability Summaries** | "Show me availability for the team this week" | Quick overview without manual checking | Aggregates availability data into readable format |
| **Workload Analysis** | "Who is overworked this month?" | Prevents burnout, ensures fair distribution | Calculates hours/assignments per employee |
| **Time-Off Impact** | "What happens if John takes Friday off?" | Scenario planning for managers | Simulates impact on existing schedules |

### Advanced Features (Phase 2+)

| Feature | Description | Why It's Important | How It Works |
|---------|-------------|-------------------|--------------|
| **Proactive Alerts** | AI notices issues before you ask | Catches problems early | Background analysis + notifications |
| **Schedule Optimization** | "Optimize next week's schedule" | Reduces manual balancing work | Multi-factor optimization algorithm + AI explanation |
| **Conversation Memory** | Follow-up questions work naturally | More natural interaction | Session-based context preservation |
| **Action Suggestions** | AI can suggest specific actions | Moves from insight to action | Structured output with actionable items |

---

## 3. Prerequisites & Setup

### 3.1 System Requirements

```yaml
# Minimum requirements for running alongside your existing stack
RAM: 16GB total (8GB for Ollama + 8GB for existing services)
CPU: 4+ cores recommended
Storage: 20GB free for model files
GPU: Optional but recommended (8GB+ VRAM for faster inference)
```

### 3.2 Software Dependencies

Add to your `requirements.txt`:

```txt
# AI/LLM Dependencies
ollama>=0.4.0          # Python client for Ollama
litellm>=1.50.0        # Unified LLM interface (optional, for cloud fallback)
tiktoken>=0.5.0        # Token counting for context management

# Optional but recommended
langchain>=0.3.0       # If you want more sophisticated RAG later
chromadb>=0.4.0        # Vector store for semantic search (future enhancement)
```

### 3.3 Ollama Installation

**Option A: Direct Installation (Recommended for development)**

```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve

# Pull the model (in another terminal)
ollama pull deepseek-r1:8b
```

**Option B: Docker (Recommended for production)**

Add to your `docker-compose.yml`:

```yaml
services:
  # ... your existing services ...

  ollama:
    image: ollama/ollama:latest
    container_name: scheduler_ollama
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - "11434:11434"
    environment:
      - OLLAMA_HOST=0.0.0.0
    # GPU support (uncomment if you have NVIDIA GPU)
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: 1
    #           capabilities: [gpu]
    restart: unless-stopped
    networks:
      - scheduler_network

volumes:
  ollama_data:
```

After starting, pull the model:

```bash
docker exec -it scheduler_ollama ollama pull deepseek-r1:8b
```

### 3.4 Environment Variables

Add to your `.env`:

```bash
# AI Configuration
AI_ENABLED=true
AI_PROVIDER=ollama                    # ollama | openai | anthropic
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:8b

# Cloud API fallback (optional)
OPENAI_API_KEY=sk-...                 # Optional fallback
ANTHROPIC_API_KEY=sk-ant-...          # Optional fallback

# AI Behavior
AI_MAX_CONTEXT_TOKENS=4000            # Max tokens for context
AI_MAX_RESPONSE_TOKENS=1000           # Max tokens for response
AI_TEMPERATURE=0.3                    # Lower = more consistent
AI_TIMEOUT_SECONDS=60                 # Request timeout
```

---

## 4. Phase 1: Foundation (Week 1)

### 4.1 Create AI Module Structure

```
app/
├── ai/
│   ├── __init__.py
│   ├── config.py           # AI configuration
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base.py         # Abstract base class
│   │   ├── ollama.py       # Ollama provider
│   │   └── cloud.py        # Cloud API provider (fallback)
│   ├── context/
│   │   ├── __init__.py
│   │   ├── retriever.py    # Context retrieval logic
│   │   ├── formatters.py   # Format data for prompts
│   │   └── queries.py      # Database query helpers
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── templates.py    # Prompt templates
│   │   └── builder.py      # Dynamic prompt construction
│   ├── services/
│   │   ├── __init__.py
│   │   ├── chat.py         # Chat service
│   │   └── suggestions.py  # Suggestion service
│   └── routes.py           # API endpoints
```

### 4.2 Configuration Module

```python
# app/ai/config.py
"""AI Configuration Management"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class AIConfig:
    """Configuration for AI services"""
    
    # Feature flags
    enabled: bool = True
    
    # Provider settings
    provider: str = "ollama"  # ollama | openai | anthropic
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "deepseek-r1:8b"
    
    # Cloud fallback
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    fallback_enabled: bool = False
    
    # Generation settings
    max_context_tokens: int = 4000
    max_response_tokens: int = 1000
    temperature: float = 0.3
    timeout_seconds: int = 60
    
    # RAG settings
    max_employees_in_context: int = 50
    max_events_in_context: int = 30
    max_schedules_in_context: int = 100
    context_date_range_days: int = 14  # Look ahead/behind
    
    @classmethod
    def from_env(cls) -> "AIConfig":
        """Load configuration from environment variables"""
        return cls(
            enabled=os.getenv("AI_ENABLED", "true").lower() == "true",
            provider=os.getenv("AI_PROVIDER", "ollama"),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            ollama_model=os.getenv("OLLAMA_MODEL", "deepseek-r1:8b"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            fallback_enabled=os.getenv("AI_FALLBACK_ENABLED", "false").lower() == "true",
            max_context_tokens=int(os.getenv("AI_MAX_CONTEXT_TOKENS", "4000")),
            max_response_tokens=int(os.getenv("AI_MAX_RESPONSE_TOKENS", "1000")),
            temperature=float(os.getenv("AI_TEMPERATURE", "0.3")),
            timeout_seconds=int(os.getenv("AI_TIMEOUT_SECONDS", "60")),
        )


# Global config instance
ai_config = AIConfig.from_env()
```

### 4.3 Base Provider Interface

```python
# app/ai/providers/base.py
"""Abstract base class for LLM providers"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Generator
import logging

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Chat message"""
    role: str  # system | user | assistant
    content: str


@dataclass
class AIResponse:
    """Standardized AI response"""
    content: str
    model: str
    provider: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None
    error: Optional[str] = None
    
    @property
    def success(self) -> bool:
        return self.error is None


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def chat(
        self,
        messages: List[Message],
        temperature: float = 0.3,
        max_tokens: int = 1000,
    ) -> AIResponse:
        """Send chat completion request"""
        pass
    
    @abstractmethod
    def chat_stream(
        self,
        messages: List[Message],
        temperature: float = 0.3,
        max_tokens: int = 1000,
    ) -> Generator[str, None, None]:
        """Stream chat completion response"""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check if provider is available"""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider identifier"""
        pass
```

### 4.4 Ollama Provider Implementation

```python
# app/ai/providers/ollama.py
"""Ollama LLM Provider"""

import logging
from typing import List, Generator, Optional
import ollama
from ollama import ResponseError

from .base import BaseLLMProvider, Message, AIResponse
from ..config import ai_config

logger = logging.getLogger(__name__)


class OllamaProvider(BaseLLMProvider):
    """Ollama local LLM provider"""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.base_url = base_url or ai_config.ollama_base_url
        self.model = model or ai_config.ollama_model
        
        # Configure ollama client
        self.client = ollama.Client(host=self.base_url)
        
    @property
    def provider_name(self) -> str:
        return "ollama"
    
    def health_check(self) -> bool:
        """Check if Ollama is running and model is available"""
        try:
            # List available models
            models = self.client.list()
            model_names = [m['name'] for m in models.get('models', [])]
            
            # Check if our model is available
            model_available = any(
                self.model in name or name.startswith(self.model.split(':')[0])
                for name in model_names
            )
            
            if not model_available:
                logger.warning(
                    f"Model {self.model} not found. Available: {model_names}"
                )
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
    
    def chat(
        self,
        messages: List[Message],
        temperature: float = 0.3,
        max_tokens: int = 1000,
    ) -> AIResponse:
        """Send chat completion request to Ollama"""
        try:
            # Convert messages to Ollama format
            ollama_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
            
            response = self.client.chat(
                model=self.model,
                messages=ollama_messages,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            )
            
            return AIResponse(
                content=response['message']['content'],
                model=self.model,
                provider=self.provider_name,
                tokens_used=response.get('eval_count'),
                finish_reason="stop",
            )
            
        except ResponseError as e:
            logger.error(f"Ollama response error: {e}")
            return AIResponse(
                content="",
                model=self.model,
                provider=self.provider_name,
                error=str(e),
            )
        except Exception as e:
            logger.error(f"Ollama request failed: {e}")
            return AIResponse(
                content="",
                model=self.model,
                provider=self.provider_name,
                error=f"Request failed: {str(e)}",
            )
    
    def chat_stream(
        self,
        messages: List[Message],
        temperature: float = 0.3,
        max_tokens: int = 1000,
    ) -> Generator[str, None, None]:
        """Stream chat completion response"""
        try:
            ollama_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
            
            stream = self.client.chat(
                model=self.model,
                messages=ollama_messages,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
                stream=True,
            )
            
            for chunk in stream:
                if 'message' in chunk and 'content' in chunk['message']:
                    yield chunk['message']['content']
                    
        except Exception as e:
            logger.error(f"Ollama stream failed: {e}")
            yield f"[Error: {str(e)}]"
    
    def pull_model(self) -> bool:
        """Pull the model if not available"""
        try:
            logger.info(f"Pulling model {self.model}...")
            self.client.pull(self.model)
            logger.info(f"Model {self.model} pulled successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to pull model: {e}")
            return False
```

### 4.5 Provider Factory

```python
# app/ai/providers/__init__.py
"""LLM Provider Factory"""

from typing import Optional
import logging

from .base import BaseLLMProvider
from .ollama import OllamaProvider
from ..config import ai_config

logger = logging.getLogger(__name__)


class ProviderFactory:
    """Factory for creating LLM providers"""
    
    _primary_provider: Optional[BaseLLMProvider] = None
    _fallback_provider: Optional[BaseLLMProvider] = None
    
    @classmethod
    def get_provider(cls, use_fallback: bool = False) -> BaseLLMProvider:
        """Get the configured LLM provider"""
        
        if use_fallback and cls._fallback_provider:
            return cls._fallback_provider
        
        if cls._primary_provider is None:
            cls._initialize_providers()
        
        return cls._primary_provider
    
    @classmethod
    def _initialize_providers(cls):
        """Initialize providers based on configuration"""
        
        # Primary provider
        if ai_config.provider == "ollama":
            cls._primary_provider = OllamaProvider()
        else:
            # Default to Ollama
            cls._primary_provider = OllamaProvider()
            
        # TODO: Add cloud fallback providers
        # if ai_config.fallback_enabled:
        #     if ai_config.openai_api_key:
        #         cls._fallback_provider = OpenAIProvider()
        
        logger.info(f"AI Provider initialized: {cls._primary_provider.provider_name}")
    
    @classmethod
    def health_check(cls) -> dict:
        """Check health of all providers"""
        provider = cls.get_provider()
        
        return {
            "primary": {
                "provider": provider.provider_name,
                "healthy": provider.health_check(),
            },
            "fallback": {
                "enabled": ai_config.fallback_enabled,
                "healthy": cls._fallback_provider.health_check() if cls._fallback_provider else None,
            }
        }


def get_llm_provider() -> BaseLLMProvider:
    """Convenience function to get the LLM provider"""
    return ProviderFactory.get_provider()
```

---

## 5. Phase 2: Context Retrieval System (Week 2)

### 5.1 Query Classification

```python
# app/ai/context/classifier.py
"""Query classification for determining what context to retrieve"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional
import re
from datetime import datetime, timedelta


class QueryType(Enum):
    """Types of scheduling queries"""
    AVAILABILITY = "availability"          # Who's available?
    SCHEDULE_VIEW = "schedule_view"        # What's the schedule?
    CONFLICT_CHECK = "conflict_check"      # Any conflicts?
    EMPLOYEE_SUGGEST = "employee_suggest"  # Who should I assign?
    WORKLOAD_ANALYSIS = "workload"         # Who's overworked?
    TIME_OFF_IMPACT = "time_off_impact"    # What if X takes off?
    EVENT_INFO = "event_info"              # Tell me about event X
    EMPLOYEE_INFO = "employee_info"        # Tell me about employee X
    GENERAL = "general"                    # General question


@dataclass
class QueryAnalysis:
    """Result of query analysis"""
    query_type: QueryType
    date_range: tuple  # (start_date, end_date)
    mentioned_employees: List[str]
    mentioned_events: List[str]
    keywords: List[str]
    confidence: float


class QueryClassifier:
    """Classify user queries to determine context needs"""
    
    # Pattern matching for query types
    PATTERNS = {
        QueryType.AVAILABILITY: [
            r'\bavailable?\b', r'\bfree\b', r'\bopen\b', 
            r'\bwho can\b', r'\bwho.{0,10}work\b'
        ],
        QueryType.CONFLICT_CHECK: [
            r'\bconflict', r'\boverlap', r'\bdouble.?book',
            r'\bclash', r'\bissue', r'\bproblem'
        ],
        QueryType.EMPLOYEE_SUGGEST: [
            r'\bsuggest\b', r'\brecommend\b', r'\bwho should\b',
            r'\bbest (person|employee|candidate)\b', r'\bassign\b'
        ],
        QueryType.WORKLOAD_ANALYSIS: [
            r'\bworkload\b', r'\boverwork', r'\bhours\b',
            r'\bbusy\b', r'\bovertime\b', r'\bbalance\b'
        ],
        QueryType.TIME_OFF_IMPACT: [
            r'\bif.{0,20}(off|leave|vacation|sick)\b',
            r'\bwhat happens\b', r'\bimpact\b'
        ],
        QueryType.SCHEDULE_VIEW: [
            r'\bschedule\b', r'\bwhat.{0,10}(today|tomorrow|this week)\b',
            r'\bshow\b', r'\blist\b'
        ],
    }
    
    # Date extraction patterns
    DATE_PATTERNS = {
        'today': lambda: (datetime.now().date(), datetime.now().date()),
        'tomorrow': lambda: (
            (datetime.now() + timedelta(days=1)).date(),
            (datetime.now() + timedelta(days=1)).date()
        ),
        'this week': lambda: (
            datetime.now().date(),
            (datetime.now() + timedelta(days=7)).date()
        ),
        'next week': lambda: (
            (datetime.now() + timedelta(days=7)).date(),
            (datetime.now() + timedelta(days=14)).date()
        ),
        'this month': lambda: (
            datetime.now().date(),
            (datetime.now() + timedelta(days=30)).date()
        ),
    }
    
    def __init__(self, employees: List[str] = None, events: List[str] = None):
        """Initialize with known employee and event names for extraction"""
        self.known_employees = employees or []
        self.known_events = events or []
    
    def analyze(self, query: str) -> QueryAnalysis:
        """Analyze a query and return structured analysis"""
        query_lower = query.lower()
        
        # Determine query type
        query_type = self._classify_type(query_lower)
        
        # Extract date range
        date_range = self._extract_date_range(query_lower)
        
        # Extract mentioned entities
        employees = self._extract_employees(query)
        events = self._extract_events(query)
        
        # Extract keywords
        keywords = self._extract_keywords(query_lower)
        
        # Calculate confidence
        confidence = self._calculate_confidence(query_type, query_lower)
        
        return QueryAnalysis(
            query_type=query_type,
            date_range=date_range,
            mentioned_employees=employees,
            mentioned_events=events,
            keywords=keywords,
            confidence=confidence,
        )
    
    def _classify_type(self, query: str) -> QueryType:
        """Classify the query type based on patterns"""
        scores = {}
        
        for query_type, patterns in self.PATTERNS.items():
            score = sum(
                1 for pattern in patterns 
                if re.search(pattern, query, re.IGNORECASE)
            )
            scores[query_type] = score
        
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        
        return QueryType.GENERAL
    
    def _extract_date_range(self, query: str) -> tuple:
        """Extract date range from query"""
        for pattern, date_func in self.DATE_PATTERNS.items():
            if pattern in query:
                return date_func()
        
        # Default to next 7 days
        return (
            datetime.now().date(),
            (datetime.now() + timedelta(days=7)).date()
        )
    
    def _extract_employees(self, query: str) -> List[str]:
        """Extract mentioned employee names"""
        mentioned = []
        for name in self.known_employees:
            if name.lower() in query.lower():
                mentioned.append(name)
        return mentioned
    
    def _extract_events(self, query: str) -> List[str]:
        """Extract mentioned event names"""
        mentioned = []
        for event in self.known_events:
            if event.lower() in query.lower():
                mentioned.append(event)
        return mentioned
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract relevant keywords"""
        # Remove common words
        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'can', 'could', 'would', 'should', 'will', 'do', 'does', 'did',
            'who', 'what', 'when', 'where', 'why', 'how', 'i', 'me', 'my',
            'for', 'to', 'of', 'in', 'on', 'at', 'by', 'with', 'from'
        }
        
        words = re.findall(r'\b[a-z]+\b', query)
        return [w for w in words if w not in stop_words and len(w) > 2]
    
    def _calculate_confidence(self, query_type: QueryType, query: str) -> float:
        """Calculate confidence in classification"""
        if query_type == QueryType.GENERAL:
            return 0.5
        
        # Count matching patterns
        patterns = self.PATTERNS.get(query_type, [])
        matches = sum(
            1 for p in patterns 
            if re.search(p, query, re.IGNORECASE)
        )
        
        # Higher matches = higher confidence
        return min(0.9, 0.6 + (matches * 0.1))
```

### 5.2 Context Retriever

```python
# app/ai/context/retriever.py
"""Retrieve relevant context from database based on query analysis"""

from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

# Import your existing models
from app.models import (
    Employee, Event, Schedule, 
    EmployeeWeeklyAvailability, EmployeeAvailability,
    EmployeeTimeOff, RotationAssignment, CompanyHoliday
)
from ..config import ai_config
from .classifier import QueryAnalysis, QueryType

logger = logging.getLogger(__name__)


@dataclass
class SchedulingContext:
    """Container for all retrieved scheduling context"""
    employees: List[Dict[str, Any]]
    events: List[Dict[str, Any]]
    schedules: List[Dict[str, Any]]
    availability: Dict[str, List[Dict[str, Any]]]
    time_off: List[Dict[str, Any]]
    rotations: List[Dict[str, Any]]
    holidays: List[Dict[str, Any]]
    
    # Metadata
    date_range: tuple
    query_type: str
    retrieved_at: datetime
    
    def to_prompt_context(self) -> str:
        """Format context for inclusion in LLM prompt"""
        sections = []
        
        # Date context
        sections.append(f"**Date Range:** {self.date_range[0]} to {self.date_range[1]}")
        sections.append(f"**Current Date:** {datetime.now().strftime('%Y-%m-%d %A')}")
        
        # Employees
        if self.employees:
            emp_lines = ["**Employees:**"]
            for emp in self.employees[:ai_config.max_employees_in_context]:
                skills = ", ".join(emp.get('skills', [])) or "No specific skills"
                emp_lines.append(
                    f"- {emp['name']} (ID: {emp['id']}) - {skills}"
                )
            sections.append("\n".join(emp_lines))
        
        # Events
        if self.events:
            event_lines = ["**Events:**"]
            for evt in self.events[:ai_config.max_events_in_context]:
                event_lines.append(
                    f"- {evt['name']} on {evt['date']} ({evt['status']})"
                )
            sections.append("\n".join(event_lines))
        
        # Current Schedules
        if self.schedules:
            sched_lines = ["**Current Schedules:**"]
            for sched in self.schedules[:ai_config.max_schedules_in_context]:
                sched_lines.append(
                    f"- {sched['employee_name']} → {sched['event_name']} on {sched['date']}"
                )
            sections.append("\n".join(sched_lines))
        
        # Time Off
        if self.time_off:
            to_lines = ["**Scheduled Time Off:**"]
            for to in self.time_off:
                to_lines.append(
                    f"- {to['employee_name']}: {to['start_date']} to {to['end_date']} ({to['reason']})"
                )
            sections.append("\n".join(to_lines))
        
        # Holidays
        if self.holidays:
            hol_lines = ["**Company Holidays:**"]
            for hol in self.holidays:
                hol_lines.append(f"- {hol['date']}: {hol['name']}")
            sections.append("\n".join(hol_lines))
        
        return "\n\n".join(sections)


class ContextRetriever:
    """Retrieve scheduling context from database"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def retrieve(self, analysis: QueryAnalysis) -> SchedulingContext:
        """Retrieve context based on query analysis"""
        start_date, end_date = analysis.date_range
        
        # Always get basic context
        employees = self._get_employees(analysis.mentioned_employees)
        holidays = self._get_holidays(start_date, end_date)
        
        # Get context based on query type
        events = []
        schedules = []
        availability = {}
        time_off = []
        rotations = []
        
        if analysis.query_type in [
            QueryType.AVAILABILITY, 
            QueryType.EMPLOYEE_SUGGEST,
            QueryType.SCHEDULE_VIEW
        ]:
            events = self._get_events(start_date, end_date, analysis.mentioned_events)
            schedules = self._get_schedules(start_date, end_date)
            availability = self._get_availability(start_date, end_date)
            time_off = self._get_time_off(start_date, end_date)
            
        elif analysis.query_type == QueryType.CONFLICT_CHECK:
            schedules = self._get_schedules(start_date, end_date)
            events = self._get_events(start_date, end_date)
            time_off = self._get_time_off(start_date, end_date)
            
        elif analysis.query_type == QueryType.WORKLOAD_ANALYSIS:
            # Extend date range for workload analysis
            extended_start = start_date - timedelta(days=30)
            schedules = self._get_schedules(extended_start, end_date)
            
        elif analysis.query_type == QueryType.TIME_OFF_IMPACT:
            schedules = self._get_schedules(start_date, end_date)
            events = self._get_events(start_date, end_date)
            time_off = self._get_time_off(start_date, end_date)
            
        else:  # GENERAL or unknown
            events = self._get_events(start_date, end_date)
            schedules = self._get_schedules(start_date, end_date)
        
        return SchedulingContext(
            employees=employees,
            events=events,
            schedules=schedules,
            availability=availability,
            time_off=time_off,
            rotations=rotations,
            holidays=holidays,
            date_range=(start_date, end_date),
            query_type=analysis.query_type.value,
            retrieved_at=datetime.now(),
        )
    
    def _get_employees(
        self, 
        specific_names: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Get employee information"""
        query = self.db.query(Employee).filter(Employee.active == True)
        
        if specific_names:
            query = query.filter(Employee.name.in_(specific_names))
        
        employees = query.all()
        
        return [
            {
                "id": emp.id,
                "name": emp.name,
                "email": emp.email,
                "skills": emp.skills if hasattr(emp, 'skills') else [],
                "role": emp.role if hasattr(emp, 'role') else None,
            }
            for emp in employees
        ]
    
    def _get_events(
        self,
        start_date: date,
        end_date: date,
        specific_events: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Get events in date range"""
        query = self.db.query(Event).filter(
            and_(
                Event.date >= start_date,
                Event.date <= end_date
            )
        )
        
        if specific_events:
            query = query.filter(Event.name.in_(specific_events))
        
        events = query.order_by(Event.date).all()
        
        return [
            {
                "id": evt.id,
                "name": evt.name,
                "date": evt.date.isoformat(),
                "status": evt.status if hasattr(evt, 'status') else "active",
                "location": evt.location if hasattr(evt, 'location') else None,
                "required_staff": evt.required_staff if hasattr(evt, 'required_staff') else 1,
            }
            for evt in events
        ]
    
    def _get_schedules(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """Get schedules in date range"""
        schedules = self.db.query(Schedule).join(Event).join(Employee).filter(
            and_(
                Event.date >= start_date,
                Event.date <= end_date
            )
        ).all()
        
        return [
            {
                "id": sched.id,
                "employee_id": sched.employee_id,
                "employee_name": sched.employee.name,
                "event_id": sched.event_id,
                "event_name": sched.event.name,
                "date": sched.event.date.isoformat(),
            }
            for sched in schedules
        ]
    
    def _get_availability(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get employee availability"""
        # Get daily availability
        avail_records = self.db.query(EmployeeAvailability).filter(
            and_(
                EmployeeAvailability.date >= start_date,
                EmployeeAvailability.date <= end_date
            )
        ).all()
        
        availability = {}
        for record in avail_records:
            emp_name = record.employee.name
            if emp_name not in availability:
                availability[emp_name] = []
            availability[emp_name].append({
                "date": record.date.isoformat(),
                "available": record.is_available,
                "start_time": str(record.start_time) if hasattr(record, 'start_time') else None,
                "end_time": str(record.end_time) if hasattr(record, 'end_time') else None,
            })
        
        return availability
    
    def _get_time_off(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """Get time off requests"""
        time_off = self.db.query(EmployeeTimeOff).filter(
            or_(
                and_(
                    EmployeeTimeOff.start_date >= start_date,
                    EmployeeTimeOff.start_date <= end_date
                ),
                and_(
                    EmployeeTimeOff.end_date >= start_date,
                    EmployeeTimeOff.end_date <= end_date
                )
            )
        ).all()
        
        return [
            {
                "employee_id": to.employee_id,
                "employee_name": to.employee.name,
                "start_date": to.start_date.isoformat(),
                "end_date": to.end_date.isoformat(),
                "reason": to.reason if hasattr(to, 'reason') else "Time off",
                "approved": to.approved if hasattr(to, 'approved') else True,
            }
            for to in time_off
        ]
    
    def _get_holidays(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """Get company holidays"""
        holidays = self.db.query(CompanyHoliday).filter(
            and_(
                CompanyHoliday.date >= start_date,
                CompanyHoliday.date <= end_date
            )
        ).all()
        
        return [
            {
                "date": hol.date.isoformat(),
                "name": hol.name,
            }
            for hol in holidays
        ]
```

---

## 6. Phase 3: AI Service Integration (Week 2-3)

### 6.1 Prompt Templates

```python
# app/ai/prompts/templates.py
"""Prompt templates for different query types"""


SYSTEM_PROMPT = """You are an AI scheduling assistant for an employee scheduling system.

Your capabilities:
- Answer questions about schedules, availability, and assignments
- Identify scheduling conflicts and issues
- Suggest optimal employee assignments
- Analyze workload distribution
- Provide insights about scheduling patterns

Guidelines:
1. ONLY use the provided context data - do not make up information
2. Be specific with dates, names, and details
3. If you cannot answer from the provided data, say so clearly
4. When suggesting assignments, explain your reasoning
5. Flag any potential conflicts or concerns you notice
6. Keep responses concise but complete

Current scheduling context will be provided with each query."""


AVAILABILITY_PROMPT = """Based on the scheduling data below, answer the user's question about employee availability.

{context}

User Question: {question}

Provide a clear, specific answer about who is available. List names and relevant dates."""


CONFLICT_CHECK_PROMPT = """Analyze the scheduling data below for conflicts and issues.

{context}

User Question: {question}

Look for:
- Double-booked employees
- Events without enough staff
- Assignments during time-off
- Overtime concerns

Report any issues found with specific details."""


EMPLOYEE_SUGGEST_PROMPT = """Based on the scheduling data below, suggest the best employee(s) for assignment.

{context}

User Question: {question}

Consider these factors:
1. Availability on the required date(s)
2. Current workload (avoid overloading anyone)
3. Skills match (if applicable)
4. Recent assignments (fair distribution)

Provide ranked suggestions with brief explanations."""


WORKLOAD_ANALYSIS_PROMPT = """Analyze the workload distribution based on the scheduling data below.

{context}

User Question: {question}

Calculate and report:
- Total assignments per employee
- Identify anyone with unusually high/low workload
- Suggest rebalancing if needed"""


GENERAL_PROMPT = """Use the scheduling data below to answer the user's question.

{context}

User Question: {question}

Provide a helpful, accurate response based only on the available data."""


def get_prompt_template(query_type: str) -> str:
    """Get the appropriate prompt template for a query type"""
    templates = {
        "availability": AVAILABILITY_PROMPT,
        "conflict_check": CONFLICT_CHECK_PROMPT,
        "employee_suggest": EMPLOYEE_SUGGEST_PROMPT,
        "workload": WORKLOAD_ANALYSIS_PROMPT,
        "schedule_view": GENERAL_PROMPT,
        "time_off_impact": CONFLICT_CHECK_PROMPT,
        "event_info": GENERAL_PROMPT,
        "employee_info": GENERAL_PROMPT,
        "general": GENERAL_PROMPT,
    }
    return templates.get(query_type, GENERAL_PROMPT)
```

### 6.2 Chat Service

```python
# app/ai/services/chat.py
"""Main chat service for AI interactions"""

import logging
from datetime import datetime
from typing import Optional, Generator
from dataclasses import dataclass

from sqlalchemy.orm import Session

from ..config import ai_config
from ..providers import get_llm_provider
from ..providers.base import Message, AIResponse
from ..context.classifier import QueryClassifier, QueryAnalysis
from ..context.retriever import ContextRetriever, SchedulingContext
from ..prompts.templates import SYSTEM_PROMPT, get_prompt_template

# Import your models for entity extraction
from app.models import Employee, Event

logger = logging.getLogger(__name__)


@dataclass
class ChatResponse:
    """Response from chat service"""
    answer: str
    query_type: str
    context_summary: str
    confidence: float
    model_used: str
    processing_time_ms: int
    error: Optional[str] = None


class SchedulerChatService:
    """AI chat service for scheduling assistance"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.provider = get_llm_provider()
        self.classifier = self._initialize_classifier()
        self.retriever = ContextRetriever(db_session)
        
        # Conversation history for follow-up context
        self.conversation_history: list = []
        self.max_history_turns: int = 5
    
    def _initialize_classifier(self) -> QueryClassifier:
        """Initialize classifier with known entities from database"""
        # Get employee names for entity extraction
        employees = self.db.query(Employee.name).filter(
            Employee.active == True
        ).all()
        employee_names = [e[0] for e in employees]
        
        # Get event names
        events = self.db.query(Event.name).limit(100).all()
        event_names = [e[0] for e in events]
        
        return QueryClassifier(
            employees=employee_names,
            events=event_names
        )
    
    def chat(self, user_message: str) -> ChatResponse:
        """Process a chat message and return response"""
        start_time = datetime.now()
        
        try:
            # Step 1: Analyze the query
            analysis = self.classifier.analyze(user_message)
            logger.info(f"Query classified as: {analysis.query_type.value}")
            
            # Step 2: Retrieve relevant context
            context = self.retriever.retrieve(analysis)
            context_text = context.to_prompt_context()
            
            # Step 3: Build the prompt
            prompt_template = get_prompt_template(analysis.query_type.value)
            user_prompt = prompt_template.format(
                context=context_text,
                question=user_message
            )
            
            # Step 4: Build message list
            messages = [
                Message(role="system", content=SYSTEM_PROMPT),
            ]
            
            # Add conversation history for context
            for hist in self.conversation_history[-self.max_history_turns:]:
                messages.append(Message(role="user", content=hist["user"]))
                messages.append(Message(role="assistant", content=hist["assistant"]))
            
            # Add current message
            messages.append(Message(role="user", content=user_prompt))
            
            # Step 5: Get LLM response
            response = self.provider.chat(
                messages=messages,
                temperature=ai_config.temperature,
                max_tokens=ai_config.max_response_tokens,
            )
            
            if not response.success:
                return ChatResponse(
                    answer="I encountered an error processing your request.",
                    query_type=analysis.query_type.value,
                    context_summary=f"Retrieved {len(context.employees)} employees, {len(context.events)} events",
                    confidence=0.0,
                    model_used=response.model,
                    processing_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                    error=response.error,
                )
            
            # Step 6: Update conversation history
            self.conversation_history.append({
                "user": user_message,
                "assistant": response.content,
            })
            
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return ChatResponse(
                answer=response.content,
                query_type=analysis.query_type.value,
                context_summary=f"Retrieved {len(context.employees)} employees, {len(context.events)} events, {len(context.schedules)} schedules",
                confidence=analysis.confidence,
                model_used=response.model,
                processing_time_ms=processing_time,
            )
            
        except Exception as e:
            logger.exception("Chat service error")
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return ChatResponse(
                answer="I'm sorry, I encountered an unexpected error. Please try again.",
                query_type="error",
                context_summary="",
                confidence=0.0,
                model_used="",
                processing_time_ms=processing_time,
                error=str(e),
            )
    
    def chat_stream(self, user_message: str) -> Generator[str, None, None]:
        """Stream chat response for real-time UI updates"""
        # Analyze and retrieve context
        analysis = self.classifier.analyze(user_message)
        context = self.retriever.retrieve(analysis)
        context_text = context.to_prompt_context()
        
        # Build prompt
        prompt_template = get_prompt_template(analysis.query_type.value)
        user_prompt = prompt_template.format(
            context=context_text,
            question=user_message
        )
        
        messages = [
            Message(role="system", content=SYSTEM_PROMPT),
            Message(role="user", content=user_prompt),
        ]
        
        # Stream response
        full_response = ""
        for chunk in self.provider.chat_stream(
            messages=messages,
            temperature=ai_config.temperature,
            max_tokens=ai_config.max_response_tokens,
        ):
            full_response += chunk
            yield chunk
        
        # Update history after streaming completes
        self.conversation_history.append({
            "user": user_message,
            "assistant": full_response,
        })
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
```

---

## 7. Phase 4: API Endpoints & Frontend (Week 3)

### 7.1 API Routes

```python
# app/ai/routes.py
"""AI API endpoints"""

from flask import Blueprint, request, jsonify, Response, stream_with_context, g
import logging

from .services.chat import SchedulerChatService
from .providers import ProviderFactory
from .config import ai_config
from app import db

logger = logging.getLogger(__name__)

ai_bp = Blueprint('ai', __name__, url_prefix='/ai')


def get_chat_service() -> SchedulerChatService:
    """Get or create chat service for current request"""
    if 'chat_service' not in g:
        g.chat_service = SchedulerChatService(db.session)
    return g.chat_service


@ai_bp.route('/health', methods=['GET'])
def health_check():
    """Check AI service health"""
    if not ai_config.enabled:
        return jsonify({
            "status": "disabled",
            "message": "AI features are disabled"
        }), 200
    
    health = ProviderFactory.health_check()
    
    status = "healthy" if health["primary"]["healthy"] else "unhealthy"
    status_code = 200 if health["primary"]["healthy"] else 503
    
    return jsonify({
        "status": status,
        "providers": health,
        "config": {
            "provider": ai_config.provider,
            "model": ai_config.ollama_model,
        }
    }), status_code


@ai_bp.route('/chat', methods=['POST'])
def chat():
    """Process a chat message"""
    if not ai_config.enabled:
        return jsonify({
            "error": "AI features are disabled"
        }), 503
    
    data = request.get_json()
    
    if not data or 'message' not in data:
        return jsonify({
            "error": "Missing 'message' in request body"
        }), 400
    
    message = data['message'].strip()
    
    if not message:
        return jsonify({
            "error": "Message cannot be empty"
        }), 400
    
    if len(message) > 2000:
        return jsonify({
            "error": "Message too long (max 2000 characters)"
        }), 400
    
    service = get_chat_service()
    response = service.chat(message)
    
    return jsonify({
        "answer": response.answer,
        "metadata": {
            "query_type": response.query_type,
            "context_summary": response.context_summary,
            "confidence": response.confidence,
            "model": response.model_used,
            "processing_time_ms": response.processing_time_ms,
        },
        "error": response.error,
    })


@ai_bp.route('/chat/stream', methods=['POST'])
def chat_stream():
    """Stream chat response"""
    if not ai_config.enabled:
        return jsonify({"error": "AI features are disabled"}), 503
    
    data = request.get_json()
    
    if not data or 'message' not in data:
        return jsonify({"error": "Missing 'message' in request body"}), 400
    
    message = data['message'].strip()
    service = get_chat_service()
    
    def generate():
        for chunk in service.chat_stream(message):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
        }
    )


@ai_bp.route('/chat/clear', methods=['POST'])
def clear_chat():
    """Clear conversation history"""
    service = get_chat_service()
    service.clear_history()
    
    return jsonify({
        "status": "success",
        "message": "Conversation history cleared"
    })


@ai_bp.route('/suggestions', methods=['GET'])
def get_suggestions():
    """Get AI suggestions for current scheduling state"""
    if not ai_config.enabled:
        return jsonify({"error": "AI features are disabled"}), 503
    
    service = get_chat_service()
    
    # Generate proactive suggestions
    suggestions_prompt = """Review the current scheduling data and provide:
    1. Any potential conflicts or issues that need attention
    2. Employees who might be overworked this week
    3. Events that still need staff assignments
    4. General optimization suggestions
    
    Keep the response brief and actionable."""
    
    response = service.chat(suggestions_prompt)
    
    return jsonify({
        "suggestions": response.answer,
        "generated_at": response.processing_time_ms,
    })
```

### 7.2 Register Blueprint

```python
# In app/__init__.py, add:

def create_app():
    # ... existing code ...
    
    # Register AI blueprint
    from app.ai.routes import ai_bp
    app.register_blueprint(ai_bp)
    
    return app
```

### 7.3 Frontend Integration (JavaScript)

```javascript
// static/js/ai-chat.js
/**
 * AI Chat Widget for Scheduling Assistant
 */

class SchedulerAIChat {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.messages = [];
        this.isLoading = false;
        
        this.init();
    }
    
    init() {
        this.render();
        this.attachEventListeners();
        this.checkHealth();
    }
    
    render() {
        this.container.innerHTML = `
            <div class="ai-chat-widget">
                <div class="ai-chat-header">
                    <h3>🤖 Scheduling Assistant</h3>
                    <span class="ai-status" id="ai-status">Checking...</span>
                </div>
                <div class="ai-chat-messages" id="ai-messages">
                    <div class="ai-message assistant">
                        <p>Hello! I'm your scheduling assistant. Ask me about:</p>
                        <ul>
                            <li>Employee availability</li>
                            <li>Schedule conflicts</li>
                            <li>Assignment suggestions</li>
                            <li>Workload analysis</li>
                        </ul>
                    </div>
                </div>
                <div class="ai-chat-input">
                    <input 
                        type="text" 
                        id="ai-input" 
                        placeholder="Ask about schedules..."
                        maxlength="2000"
                    />
                    <button id="ai-send" class="btn btn-primary">
                        Send
                    </button>
                </div>
            </div>
        `;
    }
    
    attachEventListeners() {
        const input = document.getElementById('ai-input');
        const sendBtn = document.getElementById('ai-send');
        
        sendBtn.addEventListener('click', () => this.sendMessage());
        
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
    }
    
    async checkHealth() {
        const statusEl = document.getElementById('ai-status');
        
        try {
            const response = await fetch('/ai/health');
            const data = await response.json();
            
            if (data.status === 'healthy') {
                statusEl.textContent = '🟢 Online';
                statusEl.className = 'ai-status online';
            } else {
                statusEl.textContent = '🔴 Offline';
                statusEl.className = 'ai-status offline';
            }
        } catch (error) {
            statusEl.textContent = '🔴 Error';
            statusEl.className = 'ai-status error';
        }
    }
    
    async sendMessage() {
        const input = document.getElementById('ai-input');
        const message = input.value.trim();
        
        if (!message || this.isLoading) return;
        
        // Add user message
        this.addMessage('user', message);
        input.value = '';
        
        // Show loading
        this.isLoading = true;
        const loadingId = this.addMessage('assistant', '⏳ Thinking...');
        
        try {
            const response = await fetch('/ai/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message }),
            });
            
            const data = await response.json();
            
            // Remove loading message
            this.removeMessage(loadingId);
            
            if (data.error) {
                this.addMessage('assistant', `❌ Error: ${data.error}`);
            } else {
                this.addMessage('assistant', data.answer, data.metadata);
            }
            
        } catch (error) {
            this.removeMessage(loadingId);
            this.addMessage('assistant', '❌ Failed to get response. Please try again.');
        } finally {
            this.isLoading = false;
        }
    }
    
    addMessage(role, content, metadata = null) {
        const messagesEl = document.getElementById('ai-messages');
        const id = Date.now();
        
        const messageEl = document.createElement('div');
        messageEl.className = `ai-message ${role}`;
        messageEl.id = `msg-${id}`;
        
        let html = `<p>${this.formatMessage(content)}</p>`;
        
        if (metadata) {
            html += `
                <div class="ai-metadata">
                    <small>
                        ${metadata.query_type} • 
                        ${metadata.processing_time_ms}ms • 
                        ${metadata.model}
                    </small>
                </div>
            `;
        }
        
        messageEl.innerHTML = html;
        messagesEl.appendChild(messageEl);
        messagesEl.scrollTop = messagesEl.scrollHeight;
        
        return id;
    }
    
    removeMessage(id) {
        const el = document.getElementById(`msg-${id}`);
        if (el) el.remove();
    }
    
    formatMessage(text) {
        // Basic markdown-like formatting
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>')
            .replace(/- (.*?)(?=<br>|$)/g, '<li>$1</li>')
            .replace(/(<li>.*<\/li>)+/g, '<ul>$&</ul>');
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('ai-chat-container')) {
        window.schedulerAI = new SchedulerAIChat('ai-chat-container');
    }
});
```

### 7.4 CSS Styles

```css
/* static/css/ai-chat.css */

.ai-chat-widget {
    display: flex;
    flex-direction: column;
    height: 500px;
    border: 1px solid #ddd;
    border-radius: 8px;
    overflow: hidden;
    background: #fff;
}

.ai-chat-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background: #f8f9fa;
    border-bottom: 1px solid #ddd;
}

.ai-chat-header h3 {
    margin: 0;
    font-size: 16px;
}

.ai-status {
    font-size: 12px;
    padding: 4px 8px;
    border-radius: 12px;
}

.ai-status.online {
    background: #d4edda;
    color: #155724;
}

.ai-status.offline {
    background: #f8d7da;
    color: #721c24;
}

.ai-chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
}

.ai-message {
    margin-bottom: 12px;
    padding: 10px 14px;
    border-radius: 12px;
    max-width: 85%;
}

.ai-message.user {
    background: #007bff;
    color: white;
    margin-left: auto;
}

.ai-message.assistant {
    background: #f1f3f4;
    color: #333;
}

.ai-message p {
    margin: 0;
}

.ai-message ul {
    margin: 8px 0 0 0;
    padding-left: 20px;
}

.ai-metadata {
    margin-top: 8px;
    opacity: 0.7;
}

.ai-chat-input {
    display: flex;
    padding: 12px;
    border-top: 1px solid #ddd;
    background: #f8f9fa;
}

.ai-chat-input input {
    flex: 1;
    padding: 10px 14px;
    border: 1px solid #ddd;
    border-radius: 20px;
    outline: none;
}

.ai-chat-input input:focus {
    border-color: #007bff;
}

.ai-chat-input button {
    margin-left: 8px;
    padding: 10px 20px;
    border-radius: 20px;
}
```

---

## 8. Phase 5: Production Hardening (Week 4)

### 8.1 Caching Layer

```python
# app/ai/cache.py
"""Caching for AI responses"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional
import logging

from redis import Redis
from ..config import ai_config

logger = logging.getLogger(__name__)


class AIResponseCache:
    """Cache AI responses to reduce latency and costs"""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.default_ttl = 300  # 5 minutes
        self.prefix = "ai_cache:"
    
    def _make_key(self, query: str, context_hash: str) -> str:
        """Generate cache key from query and context"""
        combined = f"{query}:{context_hash}"
        hash_val = hashlib.md5(combined.encode()).hexdigest()[:16]
        return f"{self.prefix}{hash_val}"
    
    def _hash_context(self, context: dict) -> str:
        """Create hash of context for cache key"""
        # Only hash key identifiers, not full content
        key_data = {
            "employee_ids": sorted([e['id'] for e in context.get('employees', [])]),
            "event_ids": sorted([e['id'] for e in context.get('events', [])]),
            "date_range": context.get('date_range'),
        }
        return hashlib.md5(json.dumps(key_data).encode()).hexdigest()[:8]
    
    def get(self, query: str, context: dict) -> Optional[str]:
        """Get cached response if available"""
        try:
            context_hash = self._hash_context(context)
            key = self._make_key(query, context_hash)
            
            cached = self.redis.get(key)
            if cached:
                logger.debug(f"Cache hit for query: {query[:50]}...")
                return cached.decode('utf-8')
            
            return None
            
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None
    
    def set(self, query: str, context: dict, response: str, ttl: int = None):
        """Cache a response"""
        try:
            context_hash = self._hash_context(context)
            key = self._make_key(query, context_hash)
            
            self.redis.setex(
                key,
                ttl or self.default_ttl,
                response
            )
            
            logger.debug(f"Cached response for query: {query[:50]}...")
            
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
    
    def invalidate_all(self):
        """Clear all AI cache entries"""
        try:
            keys = self.redis.keys(f"{self.prefix}*")
            if keys:
                self.redis.delete(*keys)
            logger.info(f"Invalidated {len(keys)} cache entries")
        except Exception as e:
            logger.warning(f"Cache invalidate error: {e}")
```

### 8.2 Rate Limiting

```python
# app/ai/rate_limit.py
"""Rate limiting for AI endpoints"""

from functools import wraps
from flask import request, jsonify
from redis import Redis
import time


class AIRateLimiter:
    """Rate limiter for AI requests"""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.prefix = "ai_ratelimit:"
        
        # Limits
        self.requests_per_minute = 20
        self.requests_per_hour = 200
    
    def is_allowed(self, identifier: str) -> tuple[bool, dict]:
        """Check if request is allowed"""
        now = int(time.time())
        minute_key = f"{self.prefix}{identifier}:min:{now // 60}"
        hour_key = f"{self.prefix}{identifier}:hour:{now // 3600}"
        
        # Check minute limit
        minute_count = int(self.redis.get(minute_key) or 0)
        if minute_count >= self.requests_per_minute:
            return False, {
                "error": "Rate limit exceeded",
                "retry_after": 60 - (now % 60),
                "limit": "minute"
            }
        
        # Check hour limit
        hour_count = int(self.redis.get(hour_key) or 0)
        if hour_count >= self.requests_per_hour:
            return False, {
                "error": "Rate limit exceeded", 
                "retry_after": 3600 - (now % 3600),
                "limit": "hour"
            }
        
        # Increment counters
        pipe = self.redis.pipeline()
        pipe.incr(minute_key)
        pipe.expire(minute_key, 60)
        pipe.incr(hour_key)
        pipe.expire(hour_key, 3600)
        pipe.execute()
        
        return True, {
            "remaining_minute": self.requests_per_minute - minute_count - 1,
            "remaining_hour": self.requests_per_hour - hour_count - 1,
        }


def rate_limit(limiter: AIRateLimiter):
    """Decorator for rate-limited endpoints"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Use IP or user ID as identifier
            identifier = request.remote_addr
            
            allowed, info = limiter.is_allowed(identifier)
            
            if not allowed:
                return jsonify(info), 429
            
            response = f(*args, **kwargs)
            
            # Add rate limit headers
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Remaining-Minute'] = info['remaining_minute']
                response.headers['X-RateLimit-Remaining-Hour'] = info['remaining_hour']
            
            return response
        return wrapper
    return decorator
```

### 8.3 Error Handling & Fallback

```python
# app/ai/fallback.py
"""Fallback handling when primary AI provider fails"""

import logging
from typing import Optional

from .providers import ProviderFactory, get_llm_provider
from .providers.base import Message, AIResponse
from .config import ai_config

logger = logging.getLogger(__name__)


class AIFallbackHandler:
    """Handle failures with graceful degradation"""
    
    def __init__(self):
        self.failure_count = 0
        self.max_failures = 3
        self.in_fallback_mode = False
    
    def execute_with_fallback(
        self,
        messages: list[Message],
        temperature: float = 0.3,
        max_tokens: int = 1000,
    ) -> AIResponse:
        """Execute chat with automatic fallback on failure"""
        
        # Try primary provider
        provider = get_llm_provider()
        response = provider.chat(messages, temperature, max_tokens)
        
        if response.success:
            self.failure_count = 0
            self.in_fallback_mode = False
            return response
        
        # Primary failed
        self.failure_count += 1
        logger.warning(f"Primary AI provider failed ({self.failure_count}/{self.max_failures})")
        
        # Try fallback if enabled
        if ai_config.fallback_enabled:
            fallback = ProviderFactory.get_provider(use_fallback=True)
            if fallback:
                logger.info("Attempting fallback provider...")
                fallback_response = fallback.chat(messages, temperature, max_tokens)
                
                if fallback_response.success:
                    self.in_fallback_mode = True
                    return fallback_response
        
        # All failed - return graceful error
        return AIResponse(
            content=self._get_fallback_message(),
            model="fallback",
            provider="none",
            error="All AI providers unavailable",
        )
    
    def _get_fallback_message(self) -> str:
        """Return helpful message when AI is unavailable"""
        return """I'm currently unable to process your request due to a temporary issue.

In the meantime, you can:
- Use the standard scheduling interface to view availability
- Check the daily view for current assignments
- Use filters to find available employees

Please try again in a few minutes."""
```

---

## 9. Testing Strategy

### 9.1 Unit Tests

```python
# tests/ai/test_classifier.py
"""Tests for query classifier"""

import pytest
from datetime import date, timedelta
from app.ai.context.classifier import QueryClassifier, QueryType


class TestQueryClassifier:
    
    @pytest.fixture
    def classifier(self):
        return QueryClassifier(
            employees=["John Smith", "Jane Doe", "Bob Wilson"],
            events=["Store Opening", "Training Session"]
        )
    
    def test_availability_classification(self, classifier):
        queries = [
            "Who is available tomorrow?",
            "Who can work Friday?",
            "Is anyone free this weekend?",
        ]
        
        for query in queries:
            result = classifier.analyze(query)
            assert result.query_type == QueryType.AVAILABILITY
    
    def test_conflict_classification(self, classifier):
        queries = [
            "Are there any conflicts next week?",
            "Check for double bookings",
            "Any scheduling issues?",
        ]
        
        for query in queries:
            result = classifier.analyze(query)
            assert result.query_type == QueryType.CONFLICT_CHECK
    
    def test_employee_extraction(self, classifier):
        query = "Is John Smith available tomorrow?"
        result = classifier.analyze(query)
        
        assert "John Smith" in result.mentioned_employees
    
    def test_date_extraction_today(self, classifier):
        query = "Who is working today?"
        result = classifier.analyze(query)
        
        assert result.date_range[0] == date.today()
    
    def test_date_extraction_next_week(self, classifier):
        query = "Schedule for next week"
        result = classifier.analyze(query)
        
        expected_start = date.today() + timedelta(days=7)
        assert result.date_range[0] == expected_start
```

### 9.2 Integration Tests

```python
# tests/ai/test_chat_service.py
"""Integration tests for chat service"""

import pytest
from unittest.mock import Mock, patch
from app.ai.services.chat import SchedulerChatService


class TestChatService:
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        db = Mock()
        # Setup mock query returns
        db.query.return_value.filter.return_value.all.return_value = []
        return db
    
    @pytest.fixture
    def service(self, mock_db):
        with patch('app.ai.services.chat.get_llm_provider') as mock_provider:
            mock_provider.return_value.chat.return_value = Mock(
                success=True,
                content="Test response",
                model="test-model",
            )
            return SchedulerChatService(mock_db)
    
    def test_basic_chat(self, service):
        response = service.chat("Who is available today?")
        
        assert response.answer == "Test response"
        assert response.error is None
    
    def test_conversation_history(self, service):
        service.chat("First question")
        service.chat("Follow up question")
        
        assert len(service.conversation_history) == 2
    
    def test_clear_history(self, service):
        service.chat("Test message")
        service.clear_history()
        
        assert len(service.conversation_history) == 0
```

### 9.3 End-to-End Tests

```python
# tests/ai/test_api_endpoints.py
"""API endpoint tests"""

import pytest
from app import create_app


class TestAIEndpoints:
    
    @pytest.fixture
    def client(self):
        app = create_app()
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_health_endpoint(self, client):
        response = client.get('/ai/health')
        assert response.status_code in [200, 503]
        
        data = response.get_json()
        assert 'status' in data
    
    def test_chat_endpoint(self, client):
        response = client.post('/ai/chat', json={
            'message': 'Who is available today?'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'answer' in data
    
    def test_chat_validation(self, client):
        # Missing message
        response = client.post('/ai/chat', json={})
        assert response.status_code == 400
        
        # Empty message
        response = client.post('/ai/chat', json={'message': ''})
        assert response.status_code == 400
```

---

## 10. Backup & Rollback Plan

### 10.1 Pre-Implementation Backup

```bash
#!/bin/bash
# backup_before_ai.sh

echo "Creating backup before AI implementation..."

# Backup database
./backup.sh --now

# Backup current codebase
BACKUP_DIR="backups/pre_ai_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Copy relevant directories
cp -r app/ "$BACKUP_DIR/"
cp -r tests/ "$BACKUP_DIR/"
cp requirements.txt "$BACKUP_DIR/"
cp docker-compose.yml "$BACKUP_DIR/"

echo "Backup created at: $BACKUP_DIR"
```

### 10.2 Feature Flag for Safe Rollout

```python
# app/ai/feature_flags.py
"""Feature flags for gradual rollout"""

import os

class AIFeatureFlags:
    """Control AI feature availability"""
    
    @staticmethod
    def is_enabled() -> bool:
        return os.getenv('AI_ENABLED', 'false').lower() == 'true'
    
    @staticmethod
    def is_chat_enabled() -> bool:
        return (
            AIFeatureFlags.is_enabled() and
            os.getenv('AI_CHAT_ENABLED', 'true').lower() == 'true'
        )
    
    @staticmethod
    def is_suggestions_enabled() -> bool:
        return (
            AIFeatureFlags.is_enabled() and
            os.getenv('AI_SUGGESTIONS_ENABLED', 'true').lower() == 'true'
        )
    
    @staticmethod
    def is_streaming_enabled() -> bool:
        return (
            AIFeatureFlags.is_enabled() and
            os.getenv('AI_STREAMING_ENABLED', 'false').lower() == 'true'
        )
```

### 10.3 Rollback Procedure

```bash
#!/bin/bash
# rollback_ai.sh

echo "Rolling back AI implementation..."

# Disable AI features immediately
export AI_ENABLED=false

# Restart services with AI disabled
docker-compose restart web

# If needed, restore from backup
# ./backup.sh --restore backups/pre_ai_TIMESTAMP/

echo "AI features disabled. Monitor logs for stability."
```

---

## 11. Future Enhancements

### Phase 2 Features (Month 2-3)

| Feature | Description | Complexity |
|---------|-------------|------------|
| **Semantic Search** | Use embeddings for better context retrieval | Medium |
| **Proactive Alerts** | Background job to detect issues | Medium |
| **Action Execution** | AI can make schedule changes (with approval) | High |
| **Multi-language** | Support for Spanish, etc. | Low |
| **Voice Input** | Speech-to-text for queries | Medium |

### Phase 3 Features (Month 4+)

| Feature | Description | Complexity |
|---------|-------------|------------|
| **Learning from Feedback** | Improve based on user corrections | High |
| **Predictive Scheduling** | Suggest schedules based on patterns | High |
| **Integration with Calendar** | Sync with Google/Outlook calendars | Medium |
| **Mobile App** | Dedicated mobile chat interface | High |

---

## Quick Start Checklist

- [ ] Backup existing codebase and database
- [ ] Install Ollama and pull deepseek-r1:8b model
- [ ] Add AI dependencies to requirements.txt
- [ ] Create AI module structure
- [ ] Implement configuration and providers
- [ ] Build context retrieval system
- [ ] Create chat service
- [ ] Add API endpoints
- [ ] Build frontend chat widget
- [ ] Write tests
- [ ] Deploy with feature flag disabled
- [ ] Enable gradually and monitor

---

## Support & Resources

- **Ollama Documentation:** https://ollama.com/docs
- **DeepSeek-R1 Model:** https://ollama.com/library/deepseek-r1:8b
- **LiteLLM (for multi-provider):** https://docs.litellm.ai/
- **Flask Best Practices:** https://flask.palletsprojects.com/

---

*Document Version: 1.0*
*Last Updated: December 2024*
*Author: AI Implementation Plan for Flask Schedule Webapp*
