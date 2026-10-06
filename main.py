from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import math

app = FastAPI()

# 게임 글로벌 상태 초기화
game_state = {
    "year": 1960,
    "capital": 50000,
    "credibility": 70,
    "reach": 1000,
    "media_stance": 0.5,       # -3.0 ~ +3.0
    "overton_mu": 0.0,         # 대중 여론 중심
    "overton_sigma": 1.0,      # 오버톤의 창 너비
    "reporters": [
        {"id": 1, "name": "김사회 (사회부)", "stance": -1.0, "stress": 20, "skill": 80},
        {"id": 2, "name": "이정치 (정치부)", "stance": 1.5, "stress": 10, "skill": 75},
        {"id": 3, "name": "박경제 (경제부)", "stance": 2.0, "stress": 5, "skill": 90}
    ],
    "transmitters": [],        # [{"lat": 37.56, "lon": 126.97, "name": "서울탑", "power": 50, "format": "NTSC"}]
    "subsidiaries": [],        # M&A 항목들
    "unlocked_techs": ["tech_am_radio"]
}

class StanceUpdate(BaseModel.
    stance: float

class TransmitterAdd(BaseModel):
    lat: float
    lon: float
    name: str
    power: int
    format: str

@app.get("/api/state")
def get_state():
    return game_state

@app.post("/api/stance")
def update_stance(data: StanceUpdate):
    game_state["media_stance"] = data.stance
    return game_state

@app.post("/api/advance_year")
def advance_year():
    game_state["year"] += 1
    
    # 1. 오버톤의 창 이동 연산
    influence = (game_state["reach"] / 10000) * 0.1
    game_state["overton_mu"] += (game_state["media_stance"] - game_state["overton_mu"]) * influence
    
    # 2. 기자 스트레스 연산
    for rep in game_state["reporters"]:
        diff = abs(rep["stance"] - game_state["media_stance"])
        rep["stress"] += int(diff * 8)
        if rep["stress"] >= 100:
            game_state["credibility"] = max(0, game_state["credibility"] - 10)
            rep["stress"] = 50 # 파업 후 경감
            
    # 3. 유지비 차감
    maintenance = 3000 + (len(game_state["transmitters"]) * 500)
    game_state["capital"] -= maintenance
    
    if game_state["capital"] <= 0:
        return {"status": "game_over", "message": "자본 고갈로 파산했습니다!"}
        
    return game_state

@app.post("/api/action/{action_type}")
def perform_action(action_type: str):
    if action_type == "scandal":
        game_state["credibility"] = min(100, game_state["credibility"] + 15)
        game_state["reach"] += 300
        game_state["capital"] -= 10000 # 광고 보이콧 타격
    elif action_type == "advertorial":
        game_state["capital"] += 15000
        game_state["credibility"] = max(0, game_state["credibility"] - 8)
    elif action_type == "mna_cable":
        if game_state["capital"] >= 50000:
            game_state["capital"] -= 50000
            game_state["subsidiaries"].append("종합편성채널(케이블)")
    return game_state

@app.post("/api/transmitter")
def add_transmitter(tx: TransmitterAdd):
    cost = 20000
    if game_state["capital"] >= cost:
        game_state["capital"] -= cost
        game_state["transmitters"].append(tx.dict())
        game_state["reach"] += tx.power * 50
        return {"status": "success"}
    raise HTTPException(status_code=400, detail="자본이 부족합니다.")

@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()
