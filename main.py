from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.encoders import jsonable_encoder
import os

# ==== Mongo 連線設定 ====
MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb+srv://csj011018_emogo_backend:jIGVVqMKWf8OqMaj@cluster0.vuhncwf.mongodb.net/",
)
DB_NAME = "emogo"
COLLECTION_NAME = "logs"

app = FastAPI()

# CORS：讓你的前端（手機 / Web）可以打這個 API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # 作業用簡單開全部
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==== Pydantic model ====
class LogCreate(BaseModel):
    timestamp: datetime
    mood: int = Field(ge=1, le=5)
    videoUri: Optional[str] = ""
    lat: float
    lng: float


@app.on_event("startup")
async def startup_db():
    app.mongodb_client = AsyncIOMotorClient(MONGODB_URI)
    app.mongodb = app.mongodb_client[DB_NAME]
    app.logs = app.mongodb[COLLECTION_NAME]


@app.on_event("shutdown")
async def shutdown_db():
    app.mongodb_client.close()


# ==== API：前端上傳一筆 log ====
@app.post("/api/logs")
async def create_log(log: LogCreate):
    doc = log.dict()
    result = await app.logs.insert_one(doc)
    return {"inserted_id": str(result.inserted_id)}


# ==== 匯出頁面（給 README 的 URI） ====
@app.get("/export", response_class=HTMLResponse)
async def export_page():
    html = """
    <html>
      <head><title>EmoGo Export</title></head>
      <body>
        <h1>EmoGo Data Export</h1>
        <ul>
          <li><a href="/export/sentiments">Download sentiments (JSON)</a></li>
          <li><a href="/export/gps">Download GPS coordinates (JSON)</a></li>
          <li><a href="/export/vlogs">Download vlogs (JSON, URI list)</a></li>
        </ul>
      </body>
    </html>
    """
    return HTMLResponse(content=html)


# ==== 三種資料的匯出 API ====
@app.get("/export/sentiments")
async def export_sentiments():
    cursor = app.logs.find({}, {"_id": 0, "timestamp": 1, "mood": 1})
    docs = await cursor.to_list(length=100000)  # 給一個足夠大的整數就好
    return JSONResponse(content=jsonable_encoder(docs))


@app.get("/export/gps")
async def export_gps():
    cursor = app.logs.find({}, {"_id": 0, "timestamp": 1, "lat": 1, "lng": 1})
    docs = await cursor.to_list(length=100000)
    return JSONResponse(content=jsonable_encoder(docs))


@app.get("/export/vlogs")
async def export_vlogs():
    cursor = app.logs.find({}, {"_id": 0, "timestamp": 1, "videoUri": 1})
    docs = await cursor.to_list(length=100000)
    return JSONResponse(content=jsonable_encoder(docs))

