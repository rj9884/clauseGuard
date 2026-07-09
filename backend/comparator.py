import os
import json
import asyncio
from typing import List, Dict
import numpy as np
from sentence_transformers import SentenceTransformer, util
from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# Load the local SentenceTransformer model (Cached in image during build)
model = None
try:
    model = SentenceTransformer('all-MiniLM-L6-v2')
except Exception as e:
    print(f"Warning: Failed to load local SentenceTransformer model: {e}")

async def explain_modification_risk(old_text: str, new_text: str) -> str:
    """
    Uses Gemini to explain the risk change between an old clause and a new clause.
    """
    if not client:
        return "Clause modified. Enable Gemini API to see risk analysis."
        
    prompt = f"""
    Compare the following two versions of a contract clause and explain the change and risk impact in one clear, concise sentence for a business person.
    
    Original Clause:
    {old_text}
    
    Revised Clause:
    {new_text}
    
    Return ONLY a single sentence explanation.
    """
    try:
        response = await client.aio.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=100
            )
        )
        return response.text.strip()
    except Exception as e:
        return f"Clause was modified (similarity match, failed to analyze risk: {e})."

async def compare_clauses(old_clauses: List[str], new_clauses: List[str]) -> Dict[str, any]:
    """
    Compares two sets of clauses using a Hybrid AI approach:
    1. Local ML: Uses SentenceTransformer embeddings to compute semantic similarities and map clause modifications, additions, and deletions.
    2. Cloud LLM: Uses Gemini to explain the specific risk changes of the modified clauses.
    """
    if not old_clauses and not new_clauses:
        return {
            "status": "success",
            "delta_score": 0,
            "message": "Both documents are empty.",
            "changes": []
        }

    if model is None:
        return {
            "status": "error",
            "message": "Local comparison model could not be loaded."
        }
        
    # 1. Generate local embeddings
    old_embeddings = model.encode(old_clauses, convert_to_tensor=True)
    new_embeddings = model.encode(new_clauses, convert_to_tensor=True)
    
    # 2. Compute cosine similarity matrix
    cosine_scores = util.cos_sim(old_embeddings, new_embeddings)
    scores_np = cosine_scores.cpu().numpy() if hasattr(cosine_scores, 'cpu') else np.array(cosine_scores)
    
    changes = []
    matched_old = set()
    matched_new = set()
    
    # Thresholds for matching
    SIMILARITY_THRESHOLD = 0.55
    IDENTICAL_THRESHOLD = 0.98
    
    # Greedy matching based on similarity scores
    num_old = len(old_clauses)
    num_new = len(new_clauses)
    match_candidates = []
    for r in range(num_old):
        for c in range(num_new):
            match_candidates.append((scores_np[r, c], r, c))
            
    match_candidates.sort(key=lambda x: x[0], reverse=True)
    
    delta_score = 0
    modifications_to_explain = []
    
    # Match pairs of old and new clauses
    for score, old_idx, new_idx in match_candidates:
        if old_idx in matched_old or new_idx in matched_new:
            continue
            
        if score >= SIMILARITY_THRESHOLD:
            matched_old.add(old_idx)
            matched_new.add(new_idx)
            
            old_text = old_clauses[old_idx]
            new_text = new_clauses[new_idx]
            
            if score < IDENTICAL_THRESHOLD:
                # Local ML detected a modification
                modifications_to_explain.append((old_text, new_text, float(score)))
                # Set dummy explanation until LLM runs
                changes.append({
                    "type": "Risk Modified",
                    "old_text": old_text,
                    "new_text": new_text,
                    "similarity": float(score),
                    "explanation": ""
                })
                delta_score -= 5  # Initial change
                
    # 3. Handle deletions (unmatched old clauses)
    for r in range(num_old):
        if r not in matched_old:
            changes.append({
                "type": "Risk Increased",  # Deleting old terms usually increases risk
                "old_text": old_clauses[r],
                "new_text": "",
                "similarity": 0.0,
                "explanation": "Original clause was completely removed from the revised contract."
            })
            delta_score += 10
            
    # 4. Handle additions (unmatched new clauses)
    for c in range(num_new):
        if c not in matched_new:
            changes.append({
                "type": "Risk Decreased",  # Adding custom protection terms usually decreases risk
                "old_text": "",
                "new_text": new_clauses[c],
                "similarity": 0.0,
                "explanation": "A new clause was added to the revised contract."
            })
            delta_score -= 10

    # 5. Call LLM in parallel to explain modified clauses
    if modifications_to_explain:
        tasks = [explain_modification_risk(old, new) for old, new, _ in modifications_to_explain]
        explanations = await asyncio.gather(*tasks)
        
        # Populate explanations back into list
        mod_idx = 0
        for ch in changes:
            if ch["type"] == "Risk Modified" and ch["explanation"] == "":
                ch["explanation"] = explanations[mod_idx]
                # Adjust delta score direction based on sentiment
                expl_lower = explanations[mod_idx].lower()
                if "risk reduced" in expl_lower or "decreased" in expl_lower or "favorable" in expl_lower:
                    ch["type"] = "Risk Decreased"
                    delta_score -= 5
                elif "risk increased" in expl_lower or "unfavorable" in expl_lower or "liability" in expl_lower:
                    ch["type"] = "Risk Increased"
                    delta_score += 5
                mod_idx += 1

    # Formulate summary message
    num_mod = len(modifications_to_explain)
    num_add = sum(1 for ch in changes if ch["old_text"] == "")
    num_del = sum(1 for ch in changes if ch["new_text"] == "")
    
    direction = "reduced" if delta_score < 0 else "increased"
    message = f"Semantic diff completed. Contract risk has been {direction} by {abs(delta_score)} points. ({num_mod} modifications, {num_add} additions, {num_del} deletions detected locally)."

    return {
        "status": "success",
        "delta_score": int(delta_score),
        "message": message,
        "changes": changes
    }
