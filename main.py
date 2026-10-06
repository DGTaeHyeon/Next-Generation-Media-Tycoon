import os
import json
import random
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import google.generativeai as genai

# ==========================================
# 1. 생성형 AI (Gemini) API 설정
# ==========================================
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"
if GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE":
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
else:
    model = None

def generate_dynamic_event_via_llm(year: int):
    if model is None: return None
    prompt = f"""당신은 ‘글로벌 미디어 제국 대전략 게임’의 역사 이벤트 엔진입니다.
현재 게임 연도는 {year}년입니다. 1577년부터 2026년 사이의 위키백과 역사를 바탕으로, {year}년 전후의 ‘언론, 검열, 통신’ 관련 글로벌 사건을 하나 선정하여 HOI4 스타일 선택지 5가지를 생성하십시오. 
반드시 마크다운 없이 순수 JSON으로 응답하십시오:
{{
  "id": "dynamic_event_{year}",
  "title": "국기 이모지 + 연도 + 사건 명칭",
  "desc": "위협이나 기회 서술",
  "choices": [
    {{"id": "c1", "text": "“순응”", "effect": "신뢰도 하락, 자본 보존"}},
    {{"id": "c2", "text": "“결탁”", "effect": "타사 흡수, 신뢰도 0, 막대한 자금"}},
    {{"id": "c3", "text": "“회피”", "effect": "영향력 대폭 감소"}},
    {{"id": "c4", "text": "“외세 개입”", "effect": "매 턴 외화 유출(페널티)"}},
    {{"id": "c5", "text": "“전면전”", "effect": "인프라 몰수, 지하 언론화, 신뢰도 100 달성"}}
  ]
}}"""
    try:
        response = model.generate_content(prompt)
        text_response = response.text.strip()
        if text_response.startswith("```"):
            text_response = text_response.split("```")[1]
            if text_response.lower().startswith("json"): text_response = text_response[4:]
        return json.loads(text_response.strip())
    except: return None

# ==========================================
# 2. 게임 코어 엔진
# ==========================================
app = FastAPI()

TECH_TREE = [
    {"id": "tech_jobo", "name": "민간 조보", "invent_year": 1577, "comm_year": 1577, "cost": 1000, "desc": "수기 필사 정보 전달"},
    {"id": "tech_steam_press", "name": "증기 구동 인쇄기", "invent_year": 1814, "comm_year": 1814, "cost": 15000, "desc": "대량 인쇄 시대 개막"},
    {"id": "tech_telegraph", "name": "유선 전신망", "invent_year": 1837, "comm_year": 1844, "cost": 45000, "desc": "해외 속보 수신"},
    {"id": "tech_rotary_press", "name": "윤전기", "invent_year": 1843, "comm_year": 1846, "cost": 30000, "desc": "옐로 저널리즘 탄생"},
    {"id": "tech_am_radio", "name": "AM 라디오", "invent_year": 1901, "comm_year": 1920, "cost": 80000, "desc": "실시간 전파 방송"},
    {"id": "tech_bw_tv", "name": "흑백 TV", "invent_year": 1927, "comm_year": 1941, "cost": 150000, "desc": "영상 광고 해금"},
    {"id": "tech_fm_radio", "name": "FM 라디오", "invent_year": 1933, "comm_year": 1940, "cost": 120000, "desc": "고음질 채널 세분화"},
    {"id": "tech_color_tv", "name": "컬러 TV", "invent_year": 1953, "comm_year": 1960, "cost": 250000, "desc": "시청자 몰입도 극대화"},
    {"id": "tech_cable_24h", "name": "24시간 뉴스 케이블", "invent_year": 1980, "comm_year": 1980, "cost": 400000, "desc": "지상파 독과점 붕괴"},
    {"id": "tech_web_news", "name": "웹 신문", "invent_year": 1989, "comm_year": 1994, "cost": 150000, "desc": "디지털 뉴스룸"},
    {"id": "tech_dtv", "name": "디지털 방송", "invent_year": 1998, "comm_year": 2000, "cost": 600000, "desc": "대역폭 분할"},
    {"id": "tech_smartphone", "name": "스마트폰 앱", "invent_year": 2007, "comm_year": 2010, "cost": 350000, "desc": "알고리즘 피드 해금"},
    {"id": "tech_ai_news", "name": "AI 기사", "invent_year": 2020, "comm_year": 2023, "cost": 200000, "desc": "제작비 제로화"}
]

game_state = {}

def init_game(company_name: str, start_year: int, difficulty: str, capital: int):
    global game_state
    game_state = {
        "is_started": True,
        "company_name": company_name,
        "year": start_year,
        "difficulty": difficulty,
        "capital": capital,
        "credibility": 70,
        "reach": 1000,
        "media_stance": 0.0,
        "overton_mu": 0.0,
        "overton_sigma": 1.0,
        "news_ratio": 30,
        "infra": [],
        "reporters": [
            {"id": 1, "name": "초창기 기자 A", "stance": -1.0, "stress": 0, "skill": 75},
            {"id": 2, "name": "초창기 책임자 B", "stance": 1.5, "stress": 0, "skill": 80}
        ],
        "researched_techs": [],
        "triggered_events": [],
        "pending_event": None,
        "foreign_penalty": False,
        "underground_mode": False,
        "subsidiaries": [],
        "logs": [f"[{start_year}년] ‘{company_name}’ 언론사를 창간했습니다."]
    }

class SetupRequest(BaseModel): company_name: str; start_year: int; difficulty: str; capital: int
class InfraRequest(BaseModel): type: str; name: str; callsign: str = ""; band: str = ""; format: str = ""; power_kw: int; lat: float; lon: float
class StanceRequest(BaseModel): stance: float

@app.post("/api/setup")
def setup_game(req: SetupRequest):
    init_game(req.company_name, req.start_year, req.difficulty, req.capital)
    return game_state

@app.get("/api/state")
def get_state(): return game_state

@app.post("/api/advance_year")
def advance_year():
    if not game_state.get("is_started"): raise HTTPException(status_code=400, detail="게임이 시작되지 않았습니다.")
    game_state["year"] += 1; cy = game_state["year"]

    # 1. 10년 주기 AI 동적 이벤트
    if cy % 10 == 0 and cy not in game_state["triggered_events"]:
        dyn_ev = generate_dynamic_event_via_llm(cy)
        if not dyn_ev: # Fallback
            dyn_ev = {"id": f"ev_{cy}", "title": f"🌍 {cy}년: 미디어 격변기", "desc": "거대한 사회적 변화가 도래했습니다.", 
                      "choices": [{"id":"c1","text":"“순응”","effect":"신뢰도 하락"},{"id":"c2","text":"“결탁”","effect":"타사 흡수"},
                                  {"id":"c3","text":"“회피”","effect":"영향력 감소"},{"id":"c4","text":"“외세 개입”","effect":"외화 유출"},
                                  {"id":"c5","text":"“지하 언론화”","effect":"인프라 몰수"}]}
        game_state["pending_event"] = dyn_ev
        return {"status": "event", "event_data": game_state["pending_event"]}

    # 2. 오버톤의 창 이동
    influence = min(0.4, (game_state["reach"] / 30000))
    game_state["overton_mu"] += (game_state["media_stance"] - game_state["overton_mu"]) * influence

    # 3. 기자/PD 스트레스 처리 (HR)
    for rep in game_state["reporters"]:
        diff = abs(rep["stance"] - game_state["media_stance"])
        rep["stress"] += int(diff * 12)
        if rep["stress"] >= 100:
            game_state["credibility"] = max(0, game_state["credibility"] - 15)
            rep["stress"] = 30
            game_state["logs"].append(f"🚨 ‘{rep['name']}’ 직원이 편집 방향에 반발해 파업을 선언했습니다! (신뢰도 급락)")

    # 4. 감가상각(Decay)
    maintenance = 3000 + (len(game_state["reporters"]) * 1000)
    for item in game_state["infra"]:
        item["durability"] -= 5
        if item["durability"] <= 20:
            maintenance += 8000
            game_state["logs"].append(f"⚠ ‘{item['name']}’의 내구도가 한계입니다. 대규모 수리가 필요합니다!")
        else: maintenance += int(1000 + (item["power_kw"] * 15))

    if game_state.get("foreign_penalty"): maintenance += 15000
    if game_state.get("underground_mode"): maintenance = 1000; game_state["reach"] += 500

    game_state["capital"] -= maintenance
    if game_state["capital"] <= 0: return {"status": "game_over", "message": "자본이 고갈되어 파산했습니다!"}
    
    return {"status": "success", "state": game_state}

@app.post("/api/action/{action_type}")
def perform_action(action_type: str):
    if action_type == "scoop":
        game_state["credibility"] = min(100, game_state["credibility"] + 25)
        game_state["reach"] += 1500
        game_state["capital"] -= 20000
        game_state["logs"].append("🔥 “권력 비리” 폭로! 신뢰도가 치솟았으나 분노한 기업이 광고를 보이콧했습니다.")
    elif action_type == "advertorial":
        game_state["capital"] += 30000
        game_state["credibility"] = max(0, game_state["credibility"] - 12)
        game_state["logs"].append("🤝 “기사형 광고(협찬)” 대거 게재. 자본은 늘었으나 저널리즘 신뢰도가 하락합니다.")
    elif action_type == "mna":
        if game_state["capital"] >= 80000:
            game_state["capital"] -= 80000
            game_state["subsidiaries"].append("케이블/종편 채널")
            game_state["reach"] += 8000
            game_state["logs"].append("📺 “케이블 방송사” 인수 성공! 크로스미디어 시너지가 발생합니다.")
        else: raise HTTPException(status_code=400, detail="자본이 부족합니다.")
    elif action_type == "paywall":
        if game_state["credibility"] >= 80:
            revenue = int(game_state["reach"] * 12)
            game_state["capital"] += revenue
            game_state["reach"] = int(game_state["reach"] * 0.7)
            game_state["logs"].append(f"🧱 “페이월” 도입 성공! 충성 독자들이 ₩{revenue:,}을 과금했습니다.")
        else:
            game_state["reach"] = int(game_state["reach"] * 0.3)
            game_state["logs"].append("📉 “페이월” 도입 대실패. 퀄리티 낮은 매체에 지갑을 열 독자는 없습니다.")
    return {"status": "success"}

@app.post("/api/hr/{action}")
def manage_hr(action: str, idx: int = 0):
    if action == "hire":
        if game_state["capital"] >= 10000:
            game_state["capital"] -= 10000
            r_stance = round(random.uniform(-3.0, 3.0), 1)
            r_skill = random.randint(60, 100)
            game_state["reporters"].append({"id": random.randint(100,999), "name": f"신입 에이스 #{random.randint(100,999)}", "stance": r_stance, "stress": 0, "skill": r_skill})
            game_state["logs"].append(f"👤 새 직원을 영입했습니다. (성향: {r_stance})")
        else: raise HTTPException(status_code=400, detail="자본이 부족합니다.")
    elif action == "fire":
        if game_state["capital"] >= 5000:
            game_state["capital"] -= 5000
            name = game_state["reporters"].pop(idx)["name"]
            game_state["logs"].append(f"👋 ‘{name}’ 직원을 해고했습니다. (위로금 ₩5,000 지출)")
        else: raise HTTPException(status_code=400, detail="해고 위로금이 부족합니다.")
    return {"status": "success"}

@app.post("/api/stance")
def update_stance(req: StanceRequest):
    game_state["media_stance"] = req.stance
    return {"status": "success"}

@app.post("/api/build_infra")
def build_infra(req: InfraRequest):
    if game_state.get("underground_mode"): raise HTTPException(status_code=400, detail="지하 언론은 인프라를 지을 수 없습니다.")
    
    if req.type == "Print":
        cost = 10000 + (req.power_kw * 100)
        actual_format = "활자 매체"
        actual_band = "인쇄 지국"
        reach_gain = req.power_kw * 15
        log_msg = f"🗞️ ‘{req.name}’ 인쇄/조보 지국 가동 시작! (발행량: {req.power_kw}천 부)"
    else:
        cost = 20000 + (req.power_kw * 150)
        if req.type == "TV" and req.format in ["ATSC", "DVB", "ISDB", "DTMB"]: cost += 50000
        actual_format = req.format if req.type == "TV" else "해당 없음"
        actual_band = req.band
        reach_gain = req.power_kw * 20
        cs_str = f"[{req.callsign}] " if req.callsign else ""
        log_msg = f"📡 {cs_str}‘{req.name}’ ({actual_band}/{actual_format}) 송출 가동 시작!"
        
    if game_state["capital"] >= cost:
        game_state["capital"] -= cost
        game_state["infra"].append({"type": req.type, "name": req.name, "callsign": req.callsign, "band": actual_band, "format": actual_format, "power_kw": req.power_kw, "durability": 100, "lat": req.lat, "lon": req.lon})
        game_state["reach"] += reach_gain
        game_state["logs"].append(log_msg)
        return {"status": "success"}
    raise HTTPException(status_code=400, detail="자본이 부족합니다.")

@app.post("/api/repair/{index}")
def repair_infra(index: int):
    if game_state["capital"] >= 15000:
        game_state["capital"] -= 15000
        game_state["infra"][index]["durability"] = 100
        return {"status": "success"}
    raise HTTPException(status_code=400, detail="자본이 부족합니다.")

@app.post("/api/research/{tech_id}")
def research_tech(tech_id: str):
    tech = next((t for t in TECH_TREE if t["id"] == tech_id), None)
    if tech and game_state["year"] >= tech["invent_year"] and game_state["capital"] >= tech["cost"]:
        game_state["capital"] -= tech["cost"]
        game_state["researched_techs"].append(tech_id)
        game_state["reach"] += 1000 if game_state["year"] < tech["comm_year"] else 300
        game_state["logs"].append(f"🧪 ‘{tech['name']}’ R&D 완료.")
        return {"status": "success"}
    raise HTTPException(status_code=400, detail="조건이 충족되지 않았습니다.")

@app.post("/api/resolve_event")
def resolve_event(req: dict):
    c = req.get("choice_id")
    if c == "c1": game_state["credibility"] = max(0, game_state["credibility"] - 30); game_state["capital"] += 20000
    elif c == "c2": game_state["credibility"] = 0; game_state["capital"] += 150000; game_state["media_stance"] = 3.0
    elif c == "c3": game_state["reach"] = int(game_state["reach"] * 0.4)
    elif c == "c4": game_state["foreign_penalty"] = True
    elif c == "c5": game_state["capital"] = 10000; game_state["infra"] = []; game_state["credibility"] = 100; game_state["underground_mode"] = True
    game_state["triggered_events"].append(game_state["year"])
    game_state["pending_event"] = None
    return {"status": "success"}

@app.get("/api/techs")
def get_techs(): return {"tree": TECH_TREE, "researched": game_state.get("researched_techs", []), "current_year": game_state.get("year", 1577)}

@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    with open("index.html", "r", encoding="utf-8") as f: return f.read()
