"""backend/services/brand.py

Service module that provides brand campaign proposal generation using Gemini.
It mirrors the pattern of ``backend.services.gemini`` but targets the
``BrandProposal`` schema defined in ``backend.schemas.brand``.
"""

import json
from fastapi import HTTPException, status
from backend.config import settings
from backend.schemas.brand import BrandProposal
from typing import Any, Dict, Optional
from google import genai
from google.genai import types


# Re‑use the placeholder‑key detection logic from the Gemini service.
def _is_placeholder_key(key: str) -> bool:
    placeholder_variants = {"", "your_gemini_api_key_here", "YOUR_GEMINI_API_KEY", None}
    return (key or "").strip() in placeholder_variants


async def generate_brand_proposal(campaign_data: Dict[str, Any], additional_guidance: Optional[str] = None) -> Dict[str, Any]:
    """Generate a structured brand proposal for a campaign using Gemini.

    Parameters
    ----------
    campaign_data:
        Dictionary that conforms to ``CampaignBase`` (the fields stored in the
        ``brand_campaigns`` collection).  It is passed directly to the prompt
        so the model can reference the data.
    additional_guidance:
        Optional free‑form instructions that are appended to the prompt.

    Returns
    -------
    dict
        A validated ``BrandProposal`` model represented as a plain ``dict``.

    Raises
    ------
    HTTPException
        If the Gemini API key is missing, the call fails, or the model returns
        JSON that does not match the ``BrandProposal`` schema.
    """
    # Guard against missing API key – we do *not* silently fall back.
    if _is_placeholder_key(getattr(settings, "GEMINI_API_KEY", "")):

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gemini API key is not configured. Set a valid key in .env.",
        )

    # Build the prompt.  The wording mirrors the audience service – we ask for a
    # JSON object that matches the ``BrandProposal`` schema.
    prompt_base = (
        "You are a brand‑strategy assistant. Generate a brand proposal based on the"
        " following campaign information. Return *only* a JSON object that matches"
        " the ``BrandProposal`` schema defined in the project. Include all fields"
        " exactly as defined, without extra keys."
    )
    # Inject the campaign fields as formatted JSON for clarity.
    campaign_json = json.dumps(campaign_data, ensure_ascii=False, indent=2)
    guidance = f"\nAdditional guidance: {additional_guidance}" if additional_guidance else ""
    prompt = f"""{prompt_base}\nCampaign data: {campaign_json}{guidance}"""

    try:



        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        raw = response.text
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # Attempt to extract a fenced JSON block.
            import re

            match = re.search(r"```json\n(?P<json>.*?\n)```", raw, re.DOTALL)
            if match:
                data = json.loads(match.group("json"))
            else:
                raise
        # Validate against the BrandProposal schema.
        proposal = BrandProposal.model_validate(data)
        return proposal.model_dump()
    except Exception as exc:
        # Any failure – surface a clear HTTP error.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini proposal generation failed: {exc}",
        )
