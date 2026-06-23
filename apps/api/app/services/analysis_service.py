"""Analysis service — orchestrates story gene extraction for a single chapter."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Chapter, ChapterAnalysis, SourceDocument
from app.llm import get_llm_provider
from app.llm.call_logger import track_llm_call
from app.schemas.story_gene import SCHEMA_VERSION, StoryGene

logger = logging.getLogger(__name__)

PROMPT_VERSION = "v1"
MAX_RETRIES = 2

ANALYSIS_SYSTEM_PROMPT = """\
You are an expert fiction editor specializing in narrative structure analysis.
Analyze the given chapter text and extract its story gene according to the provided JSON Schema.
Output ONLY valid JSON matching the schema. No explanations or markdown.
If you are uncertain about a field, use the default value and add a note to "ambiguities"."""

ANALYSIS_USER_TEMPLATE = """\
Analyze the following chapter and extract its story gene.

Chapter title: {title}
Chapter content:
---
{content}
---

Output the story gene as JSON matching the StoryGene schema."""


async def analyze_chapter(
    session: AsyncSession,
    chapter_id: str,
    prompt_version: str = PROMPT_VERSION,
) -> ChapterAnalysis:
    """Analyze a single chapter and save the validated result.

    Steps:
    1. Load chapter and document
    2. Check rights (prohibited = block)
    3. Build prompt
    4. Call LLM with retry on validation failure
    5. Validate with StoryGene schema
    6. Save analysis record
    7. Log LLM call
    """
    # Load chapter
    chapter = await session.get(Chapter, chapter_id)
    if not chapter:
        raise ValueError(f"Chapter not found: {chapter_id}")

    # Load document
    doc = await session.get(SourceDocument, chapter.document_id)
    if not doc:
        raise ValueError(f"Document not found: {chapter.document_id}")

    # Rights check
    if doc.rights_status == "prohibited":
        raise PermissionError("该资料权利状态为「禁止使用」，不允许分析")

    # Get provider
    provider = get_llm_provider()

    # Build messages
    content_preview = chapter.content[:8000]
    messages = [
        {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": ANALYSIS_USER_TEMPLATE.format(
                title=chapter.title,
                content=content_preview,
            ),
        },
    ]

    schema = StoryGene.model_json_schema()

    # Try with retries
    last_error = ""
    analysis_id = str(__import__("uuid").uuid4())
    llm_call_id = ""

    for attempt in range(MAX_RETRIES + 1):
        try:
            async with track_llm_call(
                provider=provider.get_provider_name(),
                model=provider.get_model_name(),
                task_type="story_gene_analysis",
                prompt_version=prompt_version,
            ) as ctx:
                response = await provider.structured_output(
                    messages=messages,
                    schema=schema,
                    temperature=0.2,
                )
                llm_call_id = ctx.log_id

                # Validate response
                gene = StoryGene.model_validate_json(response.content)

                # Update context
                ctx.input_tokens = response.input_tokens
                ctx.output_tokens = response.output_tokens
                ctx.status = "success"

            # Validation succeeded — save
            gene.chapter_id = chapter_id
            gene_json = gene.model_dump_json()

            analysis = ChapterAnalysis(
                id=analysis_id,
                chapter_id=chapter_id,
                document_id=chapter.document_id,
                project_id=doc.project_id,
                schema_version=SCHEMA_VERSION,
                prompt_version=prompt_version,
                provider=provider.get_provider_name(),
                model=provider.get_model_name(),
                status="completed",
                result_json=gene_json,
                confidence=gene.confidence,
                chapter_function=(
                    gene.chapter_function.value
                    if hasattr(gene.chapter_function, "value")
                    else str(gene.chapter_function)
                ),
                chapter_summary=gene.chapter_summary,
                hook_type=(
                    gene.suspense.hook_type.value
                    if hasattr(gene.suspense.hook_type, "value")
                    else str(gene.suspense.hook_type)
                ),
                hook_intensity=gene.suspense.hook_intensity,
                llm_call_id=llm_call_id,
            )
            session.add(analysis)
            await session.flush()
            return analysis

        except Exception as e:
            last_error = f"Attempt {attempt + 1}: {type(e).__name__}: {e}"
            logger.warning("Analysis attempt failed: %s", last_error)
            if attempt < MAX_RETRIES:
                # Add error context to messages for retry
                messages.append({"role": "assistant", "content": response.content if "response" in dir() else ""})
                messages.append(
                    {
                        "role": "user",
                        "content": f"Your response was invalid: {e}. Please fix and output valid JSON only.",
                    }
                )

    # All retries exhausted — save failed analysis
    analysis = ChapterAnalysis(
        id=analysis_id,
        chapter_id=chapter_id,
        document_id=chapter.document_id,
        project_id=doc.project_id,
        schema_version=SCHEMA_VERSION,
        prompt_version=prompt_version,
        provider=provider.get_provider_name(),
        model=provider.get_model_name(),
        status="failed",
        confidence=0.0,
        error_message=last_error[:2000],
        llm_call_id=llm_call_id,
    )
    session.add(analysis)
    await session.flush()
    return analysis


async def get_analysis_history(
    session: AsyncSession,
    chapter_id: str,
) -> list[ChapterAnalysis]:
    """Get all analysis results for a chapter, newest first."""
    result = await session.execute(
        select(ChapterAnalysis)
        .where(ChapterAnalysis.chapter_id == chapter_id)
        .order_by(ChapterAnalysis.created_at.desc())
    )
    return result.scalars().all()


async def get_latest_analysis(
    session: AsyncSession,
    chapter_id: str,
) -> ChapterAnalysis | None:
    """Get the most recent completed analysis for a chapter."""
    result = await session.execute(
        select(ChapterAnalysis)
        .where(ChapterAnalysis.chapter_id == chapter_id, ChapterAnalysis.status == "completed")
        .order_by(ChapterAnalysis.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()
