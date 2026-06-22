from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from main import CodeAnalyzer, CodeAnalyzerFromFile

app = FastAPI(title="W++ Token Analyzer", version="1.0.0")

# ── CORS so Next.js frontend can call this ────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000","https://cc-parser-frontend.vercel.app","*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── health check ──────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok"}


# ── analyze raw code sent as JSON ─────────────────────────────────────
class CodePayload(BaseModel):
    code: str
    filename: str = "snippet.wpp"

@app.post("/analyze/code")
def analyze_code(payload: CodePayload):
    if not payload.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty.")
    try:
        result = CodeAnalyzer(payload.code, file_name=payload.filename)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── analyze uploaded .wpp file ────────────────────────────────────────
@app.post("/analyze/file")
async def analyze_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".wpp"):
        raise HTTPException(status_code=400, detail="Only .wpp files are accepted.")
    try:
        raw = await file.read()
        source = raw.decode("utf-8")
        result = CodeAnalyzer(source, file_name=file.filename)
        return result
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))