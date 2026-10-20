"""
Database Models and Session Management.
"""

from backend.app.db.models import (
    Base,
    ProfileModel,
    ProductModel,
    ResearchRunModel,
    TasteAnchorModel,
    MarketHypothesisModel,
    LeadModel,
    LeadEvidenceModel,
    OutreachDraftModel,
    ProviderCallModel,
    AICallLogModel,
)
from backend.app.db.session import (
    engine,
    async_session_maker,
    get_db_session,
    init_db,
    close_db,
)

__all__ = [
    "Base",
    "ProfileModel",
    "ProductModel",
    "ResearchRunModel",
    "TasteAnchorModel",
    "MarketHypothesisModel",
    "LeadModel",
    "LeadEvidenceModel",
    "OutreachDraftModel",
    "ProviderCallModel",
    "AICallLogModel",
    "engine",
    "async_session_maker",
    "get_db_session",
    "init_db",
    "close_db",
]
