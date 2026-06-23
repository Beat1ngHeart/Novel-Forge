from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.llm.base import LLMProvider
from app.llm.registry import get_llm_provider

DBSession = Annotated[AsyncSession, Depends(get_session)]
LLM = Annotated[LLMProvider, Depends(get_llm_provider)]
