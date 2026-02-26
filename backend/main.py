import os
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
import uuid
import shutil


from parser import process_document
from classifier import detect_contract_type
from analyzer import analyze_clauses
from comparator import compare_clauses

app = FastAPI(title="ClauseGuard API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "ClauseGuard API is running."}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class AnalyzeResponse(BaseModel):
    id: str
    filename: str
    contract_type: str
    type_confidence: float
    overall_score: int
    summary: List[str]
    clauses: List[dict]
    negotiation_brief: List[dict]
    compliance_flags: List[dict]

@app.post("/upload", response_model=AnalyzeResponse)
async def upload_contract(file: UploadFile = File(...)):
    if not file.filename.endswith(('.pdf', '.docx')):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported.")
    
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            

        clauses = process_document(file_path)
        if not clauses:
            raise HTTPException(status_code=400, detail="Could not extract text or clauses from the document.")
            
        full_text = " ".join(clauses)
        

        contract_type, confidence = detect_contract_type(full_text)
        

        result = await analyze_clauses(clauses, contract_type, full_text)
        
        return {
            "id": file_id,
            "filename": file.filename,
            "contract_type": contract_type,
            "type_confidence": confidence,
            "overall_score": result.get("overall_score", 0),
            "summary": result.get("summary", []),
            "clauses": result.get("clauses", []),
            "negotiation_brief": result.get("negotiation_brief", []),
            "compliance_flags": result.get("compliance_flags", [])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        pass

@app.post("/compare")
async def compare_contracts(file1: UploadFile = File(...), file2: UploadFile = File(...)):
    if not (file1.filename.endswith(('.pdf', '.docx')) and file2.filename.endswith(('.pdf', '.docx'))):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported.")
        
    f1_id = str(uuid.uuid4())
    f2_id = str(uuid.uuid4())
    p1 = os.path.join(UPLOAD_DIR, f"{f1_id}_{file1.filename}")
    p2 = os.path.join(UPLOAD_DIR, f"{f2_id}_{file2.filename}")
    
    try:
        with open(p1, "wb") as b1: shutil.copyfileobj(file1.file, b1)
        with open(p2, "wb") as b2: shutil.copyfileobj(file2.file, b2)
        
        c1 = process_document(p1)
        c2 = process_document(p2)
        
        if not c1 or not c2:
            raise HTTPException(status_code=400, detail="Could not extract text from one or both documents.")
            
        result = compare_clauses(c1, c2)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
