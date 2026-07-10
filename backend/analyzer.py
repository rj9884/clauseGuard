import os
import json
import asyncio
from google import genai
from google.genai import types
from typing import List, Dict, Any

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY not set. API calls will fail.")

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

MODEL = 'gemini-2.0-flash'

async def analyze_single_clause(clause: str, contract_type: str) -> dict:
    prompt = f"""
System: You are a senior legal risk analyst specializing in commercial contracts.
Analyze the following contract clause and return ONLY a valid JSON object with no markdown and no explanation outside the JSON.
Contract Type: {contract_type}
Clause: {clause}

Format:
{{
  "risk_score": 0-100 (integer),
  "risk_level": "Low" | "Medium" | "High" | "Critical",
  "risk_category": "Financial" | "Legal" | "Compliance" | "Enforceability" | "Termination",
  "explanation": "2 sentence plain English explanation",
  "safer_alternative": "rewritten safe version",
  "negotiation_point": "what to ask the other side"
}}
"""
    if not client:
        return {
            "risk_score": 0, "risk_level": "Low", "risk_category": "Legal",
            "explanation": "API key not configured.",
            "safer_alternative": clause, "negotiation_point": "", "original_text": clause
        }
    try:
        response = await client.aio.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )
        data = json.loads(response.text)
        data["original_text"] = clause
        return data
    except Exception as e:
        print(f"Error analyzing clause: {e}")
        return {
            "risk_score": 0,
            "risk_level": "Low",
            "risk_category": "Legal",
            "explanation": "Error analyzing this clause.",
            "safer_alternative": clause,
            "negotiation_point": "",
            "original_text": clause
        }

async def generate_summary(full_text: str, contract_type: str) -> List[str]:
    prompt = f"""
Summarize this {contract_type} contract into exactly 5 plain English bullet points for a non-lawyer. 
Return ONLY a valid JSON string containing an array of strings, e.g. ["Point 1", "Point 2"].
Contract Text:
{full_text[:30000]}
"""
    if not client:
        return ["API key not configured."]
    try:
        response = await client.aio.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )
        data = json.loads(response.text)
        if isinstance(data, list):
            return data
        return ["Unable to parse summary."]
    except Exception as e:
         print(f"Error generating summary: {e}")
         return ["Failed to generate summary."]

def derive_negotiation_brief_and_flags(clauses: List[dict]) -> tuple[List[dict], List[dict]]:
    briefs = []
    flags = []
    for c in clauses:
        if c.get("risk_level") in ["High", "Critical"]:
            briefs.append({
                "clause_ref": c["original_text"][:50] + "...",
                "severity": c["risk_level"],
                "point": c.get("negotiation_point", "Request review of this term.")
            })
            flags.append({
                "severity": c["risk_level"],
                "reason": c.get("explanation", ""),
                "clause_text": c["original_text"]
            })
    return briefs, flags

def score_clause_relevance(clause: str) -> float:
    """Computes a heuristic risk relevance score for a clause to prioritize LLM budget."""
    text = clause.lower()
    score = 0.0
    
    # 1. Limitation of Liability / Cap on Liability
    if any(k in text for k in ["liability", "liable", " cap ", "limit", "damage", "remedy"]):
        score += 3.0
        if "limitation of liability" in text or "cap on liability" in text or "limit of liability" in text:
            score += 5.0
            
    # 2. Termination
    if any(k in text for k in ["terminate", "termination", "expire", "expiration", "convenience"]):
        score += 3.0
        if "termination for convenience" in text:
            score += 5.0
            
    # 3. IP Ownership / Assignment
    if any(k in text for k in ["intellectual", " ip ", "patent", "copyright", "trademark", "proprietary", "invention", "work product"]):
        score += 3.0
        if "intellectual property" in text or "work product" in text or "ipr" in text:
            score += 5.0
            
    # 4. Non-Compete / Non-Solicitation
    if any(k in text for k in ["compete", "solicit", "covenant", "restrictive"]):
        score += 3.0
        if "non-compete" in text or "noncompete" in text or "non-solicit" in text or "nonsolicit" in text:
            score += 5.0

    # 5. Indemnification / Warranties (Other commercial risks evaluated by ClauseGuard in production)
    if any(k in text for k in ["indemnify", "indemnification", "indemnity", "hold harmless"]):
        score += 2.0
    if any(k in text for k in ["warranty", "warranties", "disclaim", "disclaimer"]):
        score += 1.0
        
    return score

def select_top_clauses(clauses: List[str], max_clauses: int = 20) -> List[str]:
    """Selects the top N clauses based on relevance score, preserving their original document order."""
    if len(clauses) <= max_clauses:
        return clauses
        
    scored_clauses = []
    for idx, clause in enumerate(clauses):
        score = score_clause_relevance(clause)
        scored_clauses.append((score, idx, clause))
        
    # Sort by score descending, then by original index ascending (stable sort)
    scored_clauses.sort(key=lambda x: (-x[0], x[1]))
    
    # Pick the top max_clauses
    selected = scored_clauses[:max_clauses]
    
    # Sort them back into original document order
    selected.sort(key=lambda x: x[1])
    
    return [item[2] for item in selected]

async def analyze_clauses(clauses: List[str], contract_type: str, full_text: str) -> Dict[str, Any]:
    analyzed_clauses = []
    batch_size = 4
    delay_between_batches = 15

    limited_clauses = select_top_clauses(clauses, 20)

    for i in range(0, len(limited_clauses), batch_size):
        batch = limited_clauses[i:i + batch_size]
        tasks = [analyze_single_clause(c, contract_type) for c in batch]
        results = await asyncio.gather(*tasks)
        analyzed_clauses.extend(results)
        if i + batch_size < len(limited_clauses):
            await asyncio.sleep(delay_between_batches)
    
    if not analyzed_clauses:
         overall_score = 0
    else:
         total_score = sum(c.get("risk_score", 0) for c in analyzed_clauses)
         overall_score = int(total_score / len(analyzed_clauses))
         
    analyzed_clauses.sort(key=lambda x: x.get("risk_score", 0), reverse=True)
    
    summary = await generate_summary(full_text, contract_type)
    
    negotiation_brief, compliance_flags = derive_negotiation_brief_and_flags(analyzed_clauses)
    
    return {
        "overall_score": overall_score,
        "summary": summary,
        "clauses": analyzed_clauses,
        "negotiation_brief": negotiation_brief,
        "compliance_flags": compliance_flags
    }
