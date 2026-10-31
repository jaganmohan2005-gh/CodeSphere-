"""
CodeSphere - Services Package
-----------------------------
Exports core domain services:
- AIService: AI Learning Assistant & fallback engine
- CodeExecutor: Isolated subprocess code runner & testing sandbox
- AnalyticsService: Real-time analytics, metrics, and progress summaries
- seed_database: Safe initial database seeding helper
"""

from app.services.ai_service import ai_service, AIService
from app.services.code_executor import code_executor, CodeExecutor
from app.services.analytics_service import analytics_service, AnalyticsService
from app.services.seed_service import seed_database

__all__ = [
    'ai_service',
    'AIService',
    'code_executor',
    'CodeExecutor',
    'analytics_service',
    'AnalyticsService',
    'seed_database'
]
