import os
import json
from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

CONTRACT_CANDIDATE_LABELS = [
    "Non-Disclosure Agreement (NDA)",
    "Employment Agreement",
    "SaaS / Software License",
    "Vendor Agreement",
    "Partnership Agreement",
    "Commercial Lease",
    "Consulting Agreement",
    "Share Purchase Agreement",
    "General Commercial Contract"
]

def detect_contract_type_fallback(text: str) -> tuple[str, float]:
    text_lower = text[:1500].lower()
    if "non-disclosure" in text_lower or "confidentiality" in text_lower:
        return "Non-Disclosure Agreement (NDA)", 0.85
    if "employment" in text_lower or "salary" in text_lower:
        return "Employment Agreement", 0.80
    if "software" in text_lower or "saas" in text_lower or "service level" in text_lower:
        return "SaaS / Software License", 0.75
    return "General Commercial Contract", 0.50

async def detect_contract_type(text: str) -> tuple[str, float]:
    """
    Detect the contract type using Gemini API (or fallback if API key is missing).
    Uses the first 3000 characters for more accurate classification.
    """
    snippet = text[:3000]
    
    if not client:
        return detect_contract_type_fallback(snippet)
        
    prompt = f"""
    You are a contract classifier. Classify the following contract snippet into exactly one of these categories:
    {", ".join(CONTRACT_CANDIDATE_LABELS)}
    
    Return ONLY a valid JSON object with the fields "category" (string) and "confidence" (float between 0.0 and 1.0).
    Contract Snippet:
    {snippet}
    """
    try:
        response = await client.aio.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )
        data = json.loads(response.text)
        category = data.get("category")
        confidence = data.get("confidence", 0.9)
        if category in CONTRACT_CANDIDATE_LABELS:
            return category, confidence
        return "General Commercial Contract", 0.5
    except Exception as e:
        print(f"Gemini classifier failed, using fallback: {e}")
        return detect_contract_type_fallback(snippet)
