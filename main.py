import os
import shutil

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from rag.ingest import clear_store, ingest_file
from rag.retriever import ask_question

app = FastAPI(
    title="DocuChat API",
    description="Upload a document, ask questions about it.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class QuestionRequest(BaseModel):
    question: str

class UploadResponse(BaseModel):
    message: str
    filename: str
    chunks_created: int

class ChatResponse(BaseModel):
    question: str
    answer: str


@app.get("/")
def serve_frontend():
    return FileResponse("index.html")

app.mount("/static", StaticFiles(directory="."), name="static")


@app.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    filename = file.filename or "upload"

    if not filename.lower().endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files supported.")

    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        chunk_count = ingest_file(file_path)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=422, detail=str(e))

    return UploadResponse(
        message=f"'{filename}' ingested successfully.",
        filename=filename,
        chunks_created=chunk_count,
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: QuestionRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        answer = ask_question(request.question)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return ChatResponse(question=request.question, answer=answer)


@app.delete("/reset")
async def reset():
    clear_store()
    return {"message": "Vector store cleared. Ready for a new document."}


@app.get("/health")
def health():
    return {"status": "ok"}