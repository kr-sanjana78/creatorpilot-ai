from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Literal
from datetime import datetime

OverallSentiment = Literal["positive", "mostly_positive", "neutral", "mixed", "negative"]

class AudienceAnalyzeRequest(BaseModel):
    comments_text: Optional[str] = Field(
        default=None,
        description="Pasted raw comments, separated by newlines"
    )
    comments_list: Optional[List[str]] = Field(
        default=None,
        description="List of comment strings"
    )

    @model_validator(mode="after")
    def validate_input_not_empty(self):
        text_valid = bool(self.comments_text and self.comments_text.strip())
        list_valid = bool(
            self.comments_list and any(isinstance(c, str) and c.strip() for c in self.comments_list)
        )
        if not text_valid and not list_valid:
            raise ValueError(
                "Either 'comments_text' or 'comments_list' must be provided with at least one non-empty comment."
            )
        return self

class SentimentSummary(BaseModel):
    positive_pct: float = Field(..., ge=0.0, le=100.0, description="Percentage of positive sentiment")
    neutral_pct: float = Field(..., ge=0.0, le=100.0, description="Percentage of neutral sentiment")
    negative_pct: float = Field(..., ge=0.0, le=100.0, description="Percentage of negative sentiment")
    overall_sentiment: OverallSentiment = Field(..., description="Overall audience sentiment classification")

class AnalysisInsights(BaseModel):
    sentiment_summary: SentimentSummary
    top_themes: List[str] = Field(default_factory=list, description="Dominant themes identified in audience feedback")
    frequently_asked_questions: List[str] = Field(default_factory=list, description="Common questions asked by viewers")
    content_ideas: List[str] = Field(default_factory=list, description="Actionable video/content ideas based on feedback")

class AudienceAnalysisResponse(BaseModel):
    id: str
    user_email: str
    source_type: Literal["pasted_text", "comment_list"]
    total_comments_analyzed: int
    sentiment_summary: SentimentSummary
    top_themes: List[str]
    frequently_asked_questions: List[str]
    content_ideas: List[str]
    sample_comments: List[str]
    analyzed_by: str
    created_at: datetime

class AudienceAnalysisSummaryResponse(BaseModel):
    id: str
    user_email: str
    source_type: str
    total_comments_analyzed: int
    overall_sentiment: OverallSentiment
    analyzed_by: str
    created_at: datetime
