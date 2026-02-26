from transformers import pipeline


classifier = None
try:
    classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
except Exception as e:
    print(f"Warning: Could not load HuggingFace zero-shot pipeline: {e}")

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

def detect_contract_type(text: str) -> tuple[str, float]:
    """
    Detect the contract type using the first 1500 characters of the document.
    """
    snippet = text[:1500]
    
    if classifier is None:
        return detect_contract_type_fallback(snippet)
        
    try:

        result = classifier(snippet, CONTRACT_CANDIDATE_LABELS)
        best_label = result['labels'][0]
        best_score = result['scores'][0]
        

        if best_score < 0.4:
            return "General Commercial Contract", best_score
            
        return best_label, best_score
    except Exception as e:
        print(f"Fallback due to classifier error: {e}")
        return detect_contract_type_fallback(snippet)
