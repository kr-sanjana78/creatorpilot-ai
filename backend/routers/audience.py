'''backend/routers/audience.py

FastAPI router for the Audience Intelligence module.
Implements CRUD‑style endpoints that store analysis results in MongoDB
and enforce per‑user ownership using the existing ``get_current_user``
dependency.
'''
from backend.services.gemini import analyze_comments
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from typing import List
from datetime import datetime, timezone
from bson import ObjectId

# Standard imports using the correct package prefix
from backend.database import get_database
from backend.dependencies import get_current_user
from backend.schemas.audience import (
    AudienceAnalyzeRequest,
    AudienceAnalysisResponse,
    AudienceAnalysisSummaryResponse,
    AnalysisInsights,
)
import csv
import io

router = APIRouter(prefix="/api/audience", tags=["Audience Intelligence"])


def _serialize_analysis(doc: dict) -> dict:
    """Convert a raw MongoDB document to the public response shape.
    The function extracts the ``_id`` field, keeps timestamps as ``datetime``
    objects (FastAPI will serialise them to ISO strings), and returns the fields
    required by ``AudienceAnalysisResponse``.
    """
    return {
        "id": str(doc["_id"]),
        "user_email": doc["user_email"],
        "source_type": doc["source_type"],
        "total_comments_analyzed": doc["total_comments_analyzed"],
        "sentiment_summary": doc["sentiment_summary"],
        "top_themes": doc.get("top_themes", []),
        "frequently_asked_questions": doc.get("frequently_asked_questions", []),
        "content_ideas": doc.get("content_ideas", []),
        "sample_comments": doc.get("sample_comments", []),
        "analyzed_by": doc["analyzed_by"],
        "created_at": doc["created_at"],
    }


# ---------------------------------------------------------------------------
# POST /api/audience/analyze-csv
# ---------------------------------------------------------------------------
@router.post("/analyze-csv", response_model=AudienceAnalysisResponse, status_code=status.HTTP_201_CREATED)
async def analyze_audience_csv(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Accept a CSV file, extract comments, run analysis, and store the result.

    Supported comment column names (case‑insensitive):
    `comment`, `comments`, `text`, `message`.
    """
    # Validate file type
    filename = file.filename or ""
    if not filename.lower().endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a CSV (.csv) file.",
        )
    # Read file content
    try:
        content_bytes = await file.read()
        content_str = content_bytes.decode('utf-8')
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read CSV file. Ensure it is UTF‑8 encoded.",
        )

    # Parse CSV
    csv_file = io.StringIO(content_str)
    try:
        reader = csv.DictReader(csv_file)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to parse CSV file.",
        )

    # Detect comment column
    comment_col = None
    if reader.fieldnames:
        for col in reader.fieldnames:
            if col.strip().lower() in {"comment", "comments", "text", "message"}:
                comment_col = col
                break
    if not comment_col:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV must contain a column named one of: comment, comments, text, message.",
        )

    comments: List[str] = []
    for row in reader:
        val = row.get(comment_col)
        if val is not None:
            comment = val.strip()
            if comment:
                comments.append(comment)

    if not comments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid comments found in the CSV file.",
        )

    # Analyze using Gemini (or fallback)
    analysis_data = await analyze_comments(comments)

    # Persist the analysis document
    db = get_database()
    now = datetime.now(timezone.utc)
    doc: dict = {
        "user_email": current_user["email"],
        "source_type": "csv_upload",
        "total_comments_analyzed": len(comments),
        "sentiment_summary": analysis_data["sentiment_summary"],
        "top_themes": analysis_data.get("top_themes", []),
        "frequently_asked_questions": analysis_data.get("frequently_asked_questions", []),
        "content_ideas": analysis_data.get("content_ideas", []),
        "sample_comments": comments[:5],
        "analyzed_by": analysis_data.get("analyzed_by", "unknown"),
        "created_at": now,
    }
    result = await db.audience_analyses.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _serialize_analysis(doc)

@router.post("/analyze", response_model=AudienceAnalysisResponse, status_code=status.HTTP_201_CREATED)
async def analyze_audience(
    payload: AudienceAnalyzeRequest,
    current_user: dict = Depends(get_current_user),
):
    # Normalise input – accept either raw text or a list of strings.
    comments: List[str] = []
    if payload.comments_text:
        comments = [c.strip() for c in payload.comments_text.splitlines() if c.strip()]
    if payload.comments_list:
        comments.extend([c.strip() for c in payload.comments_list if isinstance(c, str) and c.strip()])
    if not comments:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid comments provided.")

    # Call the Gemini service (or heuristic fallback).
    analysis_data = await analyze_comments(comments)

    # Persist the analysis document.
    db = get_database()
    now = datetime.now(timezone.utc)
    doc: dict = {
        "user_email": current_user["email"],
        "source_type": "pasted_text" if payload.comments_text else "comment_list",
        "total_comments_analyzed": len(comments),
        "sentiment_summary": analysis_data["sentiment_summary"],
        "top_themes": analysis_data.get("top_themes", []),
        "frequently_asked_questions": analysis_data.get("frequently_asked_questions", []),
        "content_ideas": analysis_data.get("content_ideas", []),
        "sample_comments": comments[:5],
        "analyzed_by": analysis_data.get("analyzed_by", "unknown"),
        "created_at": now,
    }
    result = await db.audience_analyses.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _serialize_analysis(doc)

# ---------------------------------------------------------------------------
# GET /api/audience/analyses – list user analyses
# ---------------------------------------------------------------------------
@router.get("/analyses", response_model=List[AudienceAnalysisSummaryResponse])
async def list_audience_analyses(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    db = get_database()
    cursor = (
        db.audience_analyses.find({"user_email": current_user["email"]})
        .sort("created_at", -1)
        .limit(limit)
    )
    analyses: List[dict] = []
    async for doc in cursor:
        analyses.append({
            "id": str(doc["_id"]),
            "user_email": doc["user_email"],
            "source_type": doc["source_type"],
            "total_comments_analyzed": doc["total_comments_analyzed"],
            "overall_sentiment": doc["sentiment_summary"]["overall_sentiment"],
            "analyzed_by": doc["analyzed_by"],
            "created_at": doc["created_at"],
        })
    return analyses

# ---------------------------------------------------------------------------
# GET /api/audience/analyses/{analysis_id}
# ---------------------------------------------------------------------------
@router.get("/analyses/{analysis_id}", response_model=AudienceAnalysisResponse)
async def get_audience_analysis(
    analysis_id: str,
    current_user: dict = Depends(get_current_user),
):
    if not ObjectId.is_valid(analysis_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid analysis ID format")
    db = get_database()
    # Updated query to enforce ownership at DB level
    doc = await db.audience_analyses.find_one({"_id": ObjectId(analysis_id), "user_email": current_user["email"]})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    return _serialize_analysis(doc)

# ---------------------------------------------------------------------------
# DELETE /api/audience/analyses/{analysis_id}
# ---------------------------------------------------------------------------
@router.delete("/analyses/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_audience_analysis(
    analysis_id: str,
    current_user: dict = Depends(get_current_user),
):
    if not ObjectId.is_valid(analysis_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid analysis ID format")
    db = get_database()
    result = await db.audience_analyses.delete_one({
        "_id": ObjectId(analysis_id),
        "user_email": current_user["email"]
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    return None
