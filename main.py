import os
import json
import random
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
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
    prompt = f"""당신은 '글로벌 미디어 제국 대전략 게임'의 역사 이벤트 엔진입니다.
현재 게임 연도는 {year}년입니다. 1577년부터 2026년 사이의 위키백과 역사를 바탕으로, {year}년 전후의 언론, 미디어, 검열, 통신 기술 관련 글로벌 역사 사건을 하나 선정하여 5개의 대체 역사 선택지를 생성하십시오. 
어떠한 예시나 가이드라인도 제공하지 않으니, 사건의 역사적 맥락에 맞춰 플레이어가 선택할 수 있는 5가지의 다양한 경로(권력 순응, 극단적 저항, 자본 결탁, 해외 도피 등)를 직접 구상하십시오.
반드시 마크다운 없이 순수 JSON 객체로만 응답하십시오:

{{
  "id": "dynamic_event_{year}",
  "title": "국기 이모지 + 연도 + 사건 명칭",
  "desc": "이 사건이 미디어 생태계에 미치는 위협이나 기회를 서술",
  "choices": [
    {{"id": "c1", "text": "선택지 텍스트 1", "effect": "선택에 따른 게임 내 결과 요약 1"}},
    {{"id": "c2", "text": "선택지 텍스트 2", "effect": "선택에 따른 게임 내 결과 요약 2"}},
    {{"id": "c3", "text": "선택지 텍스트 3", "effect": "선택에 따른 게임 내 결과 요약 3"}},
    {{"id": "c4", "text": "선택지 텍스트 4", "effect": "선택에 따른 게임 내 결과 요약 4"}},
    {{"id": "c5", "text": "선택지 텍스트 5", "effect": "선택에 따른 게임 내 결과 요약 5"}}
  ]
}}"""
    try:
        response = model.generate_content(prompt)
        text = response.text
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            return json.loads(text[start:end+1])
    except: return None

# ==========================================
# 2. 게임 코어 엔진 및 API 라우트
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

class SetupRequest(BaseModel): company_name: str; start_year: int; difficulty: str; capital: int
class InfraRequest(BaseModel): type: str; name: str; callsign: str = ""; band: str = ""; format: str = ""; power_kw: int; lat: float; lon: float
class StanceRequest(BaseModel): stance: float
class GeoRequest(BaseModel): lat: float; lon: float; year: int

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
        "logs": [f"[{start_year}년] '{company_name}' 언론사를 창간했습니다."]
    }

@app.post("/api/get_historical_country")
def get_historical_country(req: GeoRequest):
    if model is None: 
        return {"country": "오프라인 영토"}
        
    prompt = f"""당신은 '글로벌 미디어 제국 시뮬레이터'의 역사 지리 엔진입니다.
현재 연도는 {req.year}년이며, 플레이어가 언론사를 창간하려는 거점의 좌표는 위도 {req.lat}, 경도 {req.lon}입니다.
이 좌표가 {req.year}년 당시에 속해 있던 국가, 제국, 부족 국가, 혹은 식민지 명칭을 정확히 하나만 도출하십시오.
(예시: '조선', '대영제국', '신성 로마 제국', '오스만 제국', '청나라' 등)
반드시 국기 이모지를 포함하여 어떠한 부연 설명도 없이 국가 명칭만 단답형 문자열로 응답하십시오."""
    
    try:
        response = model.generate_content(prompt)
        country_name = response.text.strip().replace("\"", "").replace("'", "").replace("`", "")
        return {"country": country_name}
    except Exception as e:
        print(f"지리 판별 실패: {e}")
        return {"country": "미지의 영토"}

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

    if cy % 10 == 0 and cy not in game_state["triggered_events"]:
        dyn_ev = generate_dynamic_event_via_llm(cy)
        if not dyn_ev: 
            dyn_ev = {"id": f"ev_{cy}", "title": f"🌍 {cy}년: 미디어 격변기", "desc": "거대한 사회적 변화가 도래했습니다.", 
                      "choices": [{"id":"c1","text":"선택 1","effect":"-"},{"id":"c2","text":"선택 2","effect":"-"},
                                  {"id":"c3","text":"선택 3","effect":"-"},{"id":"c4","text":"선택 4","effect":"-"},
                                  {"id":"c5","text":"선택 5","effect":"-"}]}
        game_state["pending_event"] = dyn_ev
        return {"status": "event", "event_data": game_state["pending_event"]}

    influence = min(0.4, (game_state["reach"] / 30000))
    game_state["overton_mu"] += (game_state["media_stance"] - game_state["overton_mu"]) * influence

    for rep in game_state["reporters"]:
        diff = abs(rep["stance"] - game_state["media_stance"])
        rep["stress"] += int(diff * 12)
        if rep["stress"] >= 100:
            game_state["credibility"] = max(0, game_state["credibility"] - 15)
            rep["stress"] = 30
            game_state["logs"].append(f"🚨 '{rep['name']}' 직원이 편집 방향에 반발해 파업을 선언했습니다! (신뢰도 급락)")

    maintenance = 3000 + (len(game_state["reporters"]) * 1000)
    for item in game_state["infra"]:
        item["durability"] -= 5
        if item["durability"] <= 20:
            maintenance += 8000
            game_state["logs"].append(f"⚠ '{item['name']}'의 내구도가 한계입니다. 대규모 수리가 필요합니다!")
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
        game_state["logs"].append("🔥 “거악 폭로!” 신뢰도가 치솟았으나 분노한 권력과 대기업이 보이콧했습니다.")
    elif action_type == "advertorial":
        game_state["capital"] += 30000
        game_state["credibility"] = max(0, game_state["credibility"] - 12)
        game_state["logs"].append("🤝 “기사형 광고” 대거 게재. 자본은 늘었으나 신뢰도가 하락합니다.")
    elif action_type == "mna":
        if game_state["capital"] >= 80000:
            game_state["capital"] -= 80000
            game_state["subsidiaries"].append("종편 채널")
            game_state["reach"] += 8000
            game_state["logs"].append("📺 “방송사” 인수 성공! 크로스미디어 시너지가 발생합니다.")
        else: raise HTTPException(status_code=400, detail="자본이 부족합니다.")
    elif action_type == "paywall":
        if game_state["credibility"] >= 80:
            revenue = int(game_state["reach"] * 12)
            game_state["capital"] += revenue
            game_state["reach"] = int(game_state["reach"] * 0.7)
            game_state["logs"].append(f"🧱 “페이월” 성공! 충성 독자들이 ₩{revenue:,}을 과금했습니다.")
        else:
            game_state["reach"] = int(game_state["reach"] * 0.3)
            game_state["logs"].append("📉 “페이월” 대실패. 매체 영향력이 폭락했습니다.")
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
            game_state["logs"].append(f"👋 '{name}' 직원을 해고했습니다. (위로금 ₩5,000 지출)")
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
        log_msg = f"🗞️ '{req.name}' 인쇄 지국 가동! (발행량: {req.power_kw}천 부)"
    else:
        cost = 20000 + (req.power_kw * 150)
        if req.type == "TV" and req.format in ["ATSC", "DVB", "ISDB", "DTMB"]: cost += 50000
        actual_format = req.format if req.type == "TV" else "해당 없음"
        actual_band = req.band
        reach_gain = req.power_kw * 20
        cs_str = f"[{req.callsign}] " if req.callsign else ""
        log_msg = f"📡 {cs_str}'{req.name}' ({actual_band}/{actual_format}) 송출 가동!"
        
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
        game_state["logs"].append(f"🧪 '{tech['name']}' R&D 완료.")
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
    
    event_title = game_state["pending_event"]["title"]
    game_state["logs"].append(f"역사적 선택: [{event_title}]에서 결단을 내렸습니다.")
    game_state["triggered_events"].append(game_state["year"])
    game_state["pending_event"] = None
    return {"status": "success"}

@app.get("/api/techs")
def get_techs(): return {"tree": TECH_TREE, "researched": game_state.get("researched_techs", []), "current_year": game_state.get("year", 1577)}

# ==========================================
# 3. 프론트엔드 (UI) 직접 서빙 라우트
# ==========================================
@app.get("/")
def serve_html():
    return FileResponse("index.html")

@app.get("/style.css")
def serve_css():
    return FileResponse("style.css")

@app.get("/script.js")
def serve_js():
    return FileResponse("script.js")

