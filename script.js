let map, marker, chart;
let setupMap, setupMarker;
let startLat = 37.566, startLon = 126.978;
let overtonMu = 0.0, mediaStance = 0.0;
let clickedLat = startLat, clickedLon = startLon;

// ==========================================
// 1. 게임 상태 및 데이터베이스 (Python 백엔드 흡수)
// ==========================================
let gameState = {
    is_started: false, company_name: "", year: 1577, difficulty: "Normal", capital: 0,
    credibility: 70, reach: 1000, media_stance: 0.0, overton_mu: 0.0, overton_sigma: 1.0,
    infra: [], reporters: [], researched_techs: [], logs: [], flags: new Set()
};

const TECH_TREE = [
    {id: "tech_jobo", name: "민간 조보", invent_year: 1577, comm_year: 1577, cost: 1000, desc: "수기 필사 정보 전달"},
    {id: "tech_steam_press", name: "증기 구동 인쇄기", invent_year: 1814, comm_year: 1814, cost: 15000, desc: "대량 인쇄 시대 개막"},
    {id: "tech_telegraph", name: "유선 전신망", invent_year: 1837, comm_year: 1844, cost: 45000, desc: "해외 속보 수신"},
    {id: "tech_rotary_press", name: "윤전기", invent_year: 1843, comm_year: 1846, cost: 30000, desc: "옐로 저널리즘 탄생"},
    {id: "tech_am_radio", name: "AM 라디오", invent_year: 1901, comm_year: 1920, cost: 80000, desc: "실시간 전파 방송"},
    {id: "tech_bw_tv", name: "흑백 TV", invent_year: 1927, comm_year: 1941, cost: 150000, desc: "영상 광고 해금"},
    {id: "tech_fm_radio", name: "FM 라디오", invent_year: 1933, comm_year: 1940, cost: 120000, desc: "고음질 채널 세분화"},
    {id: "tech_color_tv", name: "컬러 TV", invent_year: 1953, comm_year: 1960, cost: 250000, desc: "시청자 몰입도 극대화"},
    {id: "tech_cable_24h", name: "24시간 뉴스 케이블", invent_year: 1980, comm_year: 1980, cost: 400000, desc: "지상파 독과점 붕괴"},
    {id: "tech_web_news", name: "웹 신문", invent_year: 1989, comm_year: 1994, cost: 150000, desc: "디지털 뉴스룸"},
    {id: "tech_dtv", name: "디지털 방송", invent_year: 1998, comm_year: 2000, cost: 600000, desc: "대역폭 분할"},
    {id: "tech_smartphone", name: "스마트폰 앱", invent_year: 2007, comm_year: 2010, cost: 350000, desc: "알고리즘 피드 해금"},
    {id: "tech_ai_news", name: "AI 기사", invent_year: 2020, comm_year: 2023, cost: 200000, desc: "제작비 제로화"}
];

// ==========================================
// 2. HOI4 스타일 조건부 이벤트 엔진
// ==========================================
const EVENT_POOL = [
    {
        id: "ev_yellow_journalism",
        title: "🗞️ 옐로 저널리즘의 시대",
        trigger: (state) => state.year >= 1890 && state.year <= 1899 && state.researched_techs.includes("tech_steam_press") && !state.flags.has("yellow_journalism_done"),
        desc: "자극적인 폭로와 과장 보도가 부수를 올리는 시대입니다. 정론직필을 지킬 것인지, 대중의 입맛에 맞출 것인지 결정해야 합니다.",
        choices: [
            { text: "선정주의에 편승하여 부수를 늘린다", effect: (state) => { state.capital += 50000; state.credibility -= 20; state.reach += 5000; state.flags.add("yellow_journalism_done"); state.flags.add("tainted_reputation"); } },
            { text: "고결한 저널리즘 원칙을 고수한다", effect: (state) => { state.credibility += 15; state.capital -= 10000; state.flags.add("yellow_journalism_done"); state.flags.add("respected_press"); } }
        ]
    },
    {
        id: "ev_war_censorship",
        title: "⚔️ 전시 보도 통제",
        trigger: (state) => state.year >= 1914 && state.year <= 1918 && !state.flags.has("ww1_censorship"),
        desc: "전쟁이 발발하여 정부가 강력한 보도 지침을 내렸습니다. 군부의 검열관이 윤전기를 감시하고 있습니다.",
        choices: [
            { text: "애국주의 보도에 앞장선다", effect: (state) => { state.capital += 20000; state.credibility -= 10; state.flags.add("ww1_censorship"); } },
            { text: "검열을 우회해 전황의 진실을 알린다", effect: (state) => { state.credibility += 30; state.capital -= 30000; state.flags.add("ww1_censorship"); state.flags.add("gov_target"); } }
        ]
    }
    // 여기에 전 세계 역사 고증 이벤트를 무한정 추가할 수 있습니다.
];

document.addEventListener("DOMContentLoaded", () => {
    setupMap = L.map('setup-map').setView([startLat, startLon], 2);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(setupMap);
    setupMarker = L.marker([startLat, startLon]).addTo(setupMap);

    setupMap.on('click', function(e) { 
        startLat = e.latlng.lat; startLon = e.latlng.lng;
        clickedLat = startLat; clickedLon = startLon;
        setupMarker.setLatLng([startLat, startLon]); 
        document.getElementById('selected-coords').innerText = `선택된 좌표: 위도 ${startLat.toFixed(3)}, 경도 ${startLon.toFixed(3)}`;
    });
});

async function getHistoricalContext(lat, lon, year) {
    try {
        const res = await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=json&accept-language=ko`);
        const data = await res.json();
        const country = data.address.country || "미지의 영토";
        return country;
    } catch (e) { return "오프라인 영토"; }
}

async function startGame() {
    const btn = document.getElementById('btn-start');
    btn.innerText = "지리 정보 고증 중... (무료 API)";
    btn.disabled = true;

    const reqYear = parseInt(document.getElementById('start-year').value);
    const countryName = await getHistoricalContext(startLat, startLon, reqYear);

    gameState = {
        is_started: true,
        company_name: document.getElementById('company-name').value || "이름 없는 언론사",
        year: reqYear,
        difficulty: document.getElementById('difficulty').value,
        capital: parseInt(document.getElementById('start-cap').value),
        credibility: 70, reach: 1000, media_stance: 0.0, overton_mu: 0.0, overton_sigma: 1.0,
        infra: [], researched_techs: [], flags: new Set(),
        reporters: [
            {id: 1, name: "초창기 기자 A", stance: -1.0, stress: 0, skill: 75},
            {id: 2, name: "초창기 책임자 B", stance: 1.5, stress: 0, skill: 80}
        ],
        logs: [`[${reqYear}년] ${countryName}에서 ‘${document.getElementById('company-name').value}’ 언론사를 창간했습니다.`]
    };

    document.getElementById('setup-modal').style.display = 'none';
    document.getElementById('game-ui').style.display = 'grid';
    
    setTimeout(() => {
        if (!map) {
            map = L.map('map').setView([startLat, startLon], 5);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
            marker = L.marker([startLat, startLon]).addTo(map);
            map.on('click', function(e) { 
                clickedLat = e.latlng.lat; clickedLon = e.latlng.lng; 
                marker.setLatLng([clickedLat, clickedLon]); 
            });
        }
        map.invalidateSize();
    }, 300);
    
    initChart();
    updateUI();
    alert(`“${reqYear}년, ${countryName}에서 위대한 미디어 제국의 역사가 시작됩니다!”`);
}

function updateUI() {
    document.getElementById('ui-company-name').innerText = gameState.company_name;
    document.getElementById('ui-year').innerText = gameState.year;
    document.getElementById('ui-cap').innerText = '₩ ' + gameState.capital.toLocaleString();
    document.getElementById('ui-cred').innerText = gameState.credibility;
    document.getElementById('ui-reach').innerText = Math.round(gameState.reach).toLocaleString();
    
    overtonMu = gameState.overton_mu; mediaStance = gameState.media_stance;
    updateChart();

    let infraHtml = '';
    gameState.infra.forEach((inf, idx) => {
        let cs_str = inf.callsign ? `[${inf.callsign}] ` : "";
        infraHtml += `<div class="infra-item" style="padding: 10px; background: #0f172a; margin-bottom: 5px; border: 1px solid #475569; border-radius: 4px;">
            <div style="display:flex; justify-content:space-between;">
                <b>${cs_str}${inf.name} <span style="font-size:12px; color:#94a3b8;">(${inf.band}/${inf.format})</span></b>
                <button style="padding: 2px 8px; font-size:12px;" onclick="repairInfra(${idx})">수리</button>
            </div>
            <div style="font-size:12px; margin-top:5px; color:#cbd5e1;">출력/부수: ${inf.power_kw} | 내구도: ${inf.durability}%</div>
        </div>`;
    });
    document.getElementById('infra-list').innerHTML = infraHtml;

    let hrHtml = '';
    gameState.reporters.forEach((r, idx) => {
        hrHtml += `<div class="reporter-item">
            <div><b>${r.name}</b> <span style="font-size:12px; color:#94a3b8;">(성향:${r.stance.toFixed(1)})</span></div>
            <div style="display:flex; align-items:center;">
                <span style="font-size:12px; color:#ef4444;">${r.stress}%</span>
                <div class="progress-bg"><div class="progress-fill" style="width:${r.stress}%;"></div></div>
                <button style="margin-left:10px; font-size:11px; padding:2px 5px;" onclick="manageHR('fire', ${idx})">해고</button>
            </div>
        </div>`;
    });
    document.getElementById('ui-reporters').innerHTML = hrHtml;

    let logHtml = '';
    gameState.logs.slice().reverse().forEach(l => logHtml += `<div>${l}</div>`);
    document.getElementById('ui-logs').innerHTML = logHtml;

    let techHtml = '';
    TECH_TREE.forEach(t => {
        if(t.invent_year <= gameState.year && !gameState.researched_techs.includes(t.id)) {
            techHtml += `<div style="background:#0f172a; padding:10px; margin-bottom:8px; border:1px solid #334155; display:flex; justify-content:space-between;">
                <div><b>${t.name}</b> <span style="font-size:12px; color:#94a3b8;">(${t.invent_year}년)</span><br><span style="font-size:12px; color:#cbd5e1;">${t.desc}</span></div>
                <button onclick="researchTech('${t.id}')">₩${t.cost/1000}k</button>
            </div>`;
        }
    });
    document.getElementById('tech-list').innerHTML = techHtml;
}

function advanceTurn() {
    gameState.year += 1;
    let eventFired = false;

    // 이벤트 검사 엔진 가동
    for (let event of EVENT_POOL) {
        if (event.trigger(gameState)) {
            document.getElementById('ev-title').innerText = event.title;
            document.getElementById('ev-desc').innerText = event.desc;
            let btns = '';
            event.choices.forEach((c, idx) => { 
                btns += `<button class="event-btn" onclick="resolveEvent('${event.id}', ${idx})"><b>${c.text}</b></button>`; 
            });
            document.getElementById('ev-choices').innerHTML = btns;
            document.getElementById('event-modal').style.display = 'flex';
            eventFired = true;
            break; // 한 턴에 하나만 발생
        }
    }

    // 유지비 계산 및 상태 업데이트 로직 (백엔드 코드 이식)
    let influence = Math.min(0.4, (gameState.reach / 30000));
    gameState.overton_mu += (gameState.media_stance - gameState.overton_mu) * influence;
    let maintenance = 3000 + (gameState.reporters.length * 1000);
    
    gameState.infra.forEach(item => {
        item.durability -= 5;
        if (item.durability <= 20) { maintenance += 8000; gameState.logs.push(`⚠ ‘${item.name}’ 대규모 수리 필요!`); }
        else { maintenance += Math.floor(1000 + (item.power_kw * 15)); }
    });
    
    gameState.capital -= maintenance;
    if (gameState.capital <= 0) { alert("자본이 고갈되어 파산했습니다!"); location.reload(); return; }

    if(!eventFired) updateUI();
}

function resolveEvent(eventId, choiceIdx) {
    const event = EVENT_POOL.find(e => e.id === eventId);
    event.choices[choiceIdx].effect(gameState); // 선택지에 배정된 효과 함수 실행
    gameState.logs.push(`역사적 선택: [${event.title}]에서 결단을 내렸습니다.`);
    document.getElementById('event-modal').style.display = 'none';
    updateUI();
}

function doAction(type) {
    if (type === "scoop") { gameState.credibility = Math.min(100, gameState.credibility + 25); gameState.reach += 1500; gameState.capital -= 20000; gameState.logs.push("🔥 “거악 폭로!” 신뢰도 상승."); }
    else if (type === "advertorial") { gameState.capital += 30000; gameState.credibility = Math.max(0, gameState.credibility - 12); gameState.logs.push("🤝 “기사형 광고” 자본 확보."); }
    else if (type === "mna") { if(gameState.capital >= 80000){ gameState.capital-=80000; gameState.reach+=8000; gameState.logs.push("📺 종편 인수 성공!");} else alert("자본 부족!"); }
    else if (type === "paywall") { if(gameState.credibility >= 80){ let rev = Math.floor(gameState.reach*12); gameState.capital+=rev; gameState.reach=Math.floor(gameState.reach*0.7); gameState.logs.push(`🧱 “페이월” 성공! ₩${rev} 확보.`); } else { gameState.reach=Math.floor(gameState.reach*0.3); gameState.logs.push("📉 “페이월” 실패."); } }
    updateUI();
}

function manageHR(action, idx) {
    if (action === "hire" && gameState.capital >= 10000) {
        gameState.capital -= 10000;
        gameState.reporters.push({id: Date.now(), name: `신입 에이스 #${Math.floor(Math.random()*900)+100}`, stance: parseFloat((Math.random()*6 - 3).toFixed(1)), stress: 0, skill: 80});
        gameState.logs.push("👤 새 직원을 영입했습니다.");
    } else if (action === "fire" && gameState.capital >= 5000) {
        gameState.capital -= 5000;
        let name = gameState.reporters.splice(idx, 1)[0].name;
        gameState.logs.push(`👋 ‘${name}’ 직원을 해고했습니다.`);
    }
    updateUI();
}

function researchTech(id) {
    let t = TECH_TREE.find(x => x.id === id);
    if(gameState.capital >= t.cost) {
        gameState.capital -= t.cost;
        gameState.researched_techs.push(id);
        gameState.reach += (gameState.year < t.comm_year) ? 1000 : 300;
        gameState.logs.push(`🧪 ‘${t.name}’ R&D 완료.`);
        updateUI();
    }
}

function updateBandFormatOptions() {
    const typeSelect = document.getElementById('tx-type').value;
    const bandSelect = document.getElementById('tx-band');
    const formatSelect = document.getElementById('tx-format');
    const callsignInput = document.getElementById('tx-callsign');

    if (typeSelect === 'Print') {
        bandSelect.innerHTML = '<option value="Print">인쇄/필사</option>';
        bandSelect.disabled = true;
        formatSelect.innerHTML = '<option value="None">해당 없음</option>';
        formatSelect.disabled = true;
        callsignInput.disabled = true;
        callsignInput.value = '';
        callsignInput.placeholder = "호출부호 없음 (인쇄)";
    } else if (typeSelect === 'Radio') {
        bandSelect.innerHTML = '<option value="LW">AM 장파 (LW)</option><option value="MW">AM 중파 (MW)</option><option value="SW">AM 단파 (SW)</option><option value="FM">FM 초단파</option>';
        bandSelect.disabled = false;
        formatSelect.innerHTML = '<option value="None">해당 없음</option>';
        formatSelect.disabled = true;
        callsignInput.disabled = false;
        callsignInput.placeholder = "호출부호 (예: HLKV)";
    } else {
        bandSelect.innerHTML = '<option value="VHF">TV VHF</option><option value="UHF">TV UHF</option>';
        bandSelect.disabled = false;
        formatSelect.innerHTML = '<option value="NTSC">NTSC</option><option value="PAL">PAL</option><option value="SECAM">SECAM</option><option value="ATSC">ATSC</option><option value="DVB">DVB</option><option value="ISDB">ISDB</option><option value="DTMB">DTMB</option>';
        formatSelect.disabled = false;
        callsignInput.disabled = false;
        callsignInput.placeholder = "호출부호 (예: HLKV)";
    }
}

function buildInfra() {
    const typeVal = document.getElementById('tx-type').value;
    const nameVal = document.getElementById('tx-name').value || "지점";
    const powerVal = parseInt(document.getElementById('tx-power').value);
    const formatSelect = document.getElementById('tx-format');
    const callsignInput = document.getElementById('tx-callsign');
    const bandSelect = document.getElementById('tx-band');
    
    let callsign = callsignInput.disabled ? "" : callsignInput.value;
    let band = bandSelect.disabled ? "인쇄 지국" : bandSelect.value;
    let format = formatSelect.disabled ? "활자 매체" : formatSelect.value;
    
    let cost = 0;
    let reachGain = 0;
    let logMsg = "";

    if (typeVal === "Print") {
        cost = 10000 + (powerVal * 100);
        reachGain = powerVal * 15;
        logMsg = `🗞️ ‘${nameVal}’ 인쇄 지국 가동! (발행량: ${powerVal}천 부)`;
    } else {
        cost = 20000 + (powerVal * 150);
        // 디지털 TV 방송망 구축 시 막대한 추가 비용 고증 부활
        if (typeVal === "TV" && ["ATSC", "DVB", "ISDB", "DTMB"].includes(format)) {
            cost += 50000; 
        }
        reachGain = powerVal * 20;
        let cs_str = callsign ? `[${callsign}] ` : "";
        logMsg = `📡 ${cs_str}‘${nameVal}’ (${band}/${format}) 송출 가동!`;
    }

    if (gameState.capital >= cost) {
        gameState.capital -= cost;
        gameState.infra.push({
            type: typeVal, name: nameVal, callsign: callsign, band: band, format: format,
            power_kw: powerVal, durability: 100, lat: clickedLat, lon: clickedLon
        });
        gameState.reach += reachGain;
        gameState.logs.push(logMsg);
        updateUI();
    } else {
        alert("자본이 부족합니다.");
    }
}

function repairInfra(idx) { if(gameState.capital >= 15000) { gameState.capital-=15000; gameState.infra[idx].durability = 100; updateUI(); } }
function updateStance(val) { gameState.media_stance = parseFloat(val); document.getElementById('ui-stance').innerText = val; updateUI(); }

function initChart() {
    const ctx = document.getElementById('overtonChart').getContext('2d');
    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array.from({length: 61}, (_, i) => (i - 30) / 10),
            datasets: [
                { label: '대중 여론', data: [], borderColor: '#3b82f6', backgroundColor: 'rgba(59, 130, 246, 0.3)', fill: true, pointRadius: 0 },
                { label: '데스크 논조', data: [], borderColor: '#ef4444', borderDash: [5, 5], pointRadius: 0, borderWidth: 2, fill: false }
            ]
        },
        options: { 
            responsive: true, 
            maintainAspectRatio: false, 
            scales: { 
                x: { ticks: { color: '#94a3b8' } }, 
                y: { display: false, max: 1.1 } 
            }, 
            animation: { duration: 400 } 
        }
    });
}

function updateChart() {
    let labels = chart.data.labels;
    // 대중 여론 (정규분포 곡선)
    chart.data.datasets[0].data = labels.map(x => Math.exp(-0.5 * Math.pow((x - overtonMu) / 1.0, 2)));
    // 데스크 논조 (막대형 표시)
    chart.data.datasets[1].data = labels.map(x => (Math.abs(x - mediaStance) < 0.05) ? 1.0 : 0);
    chart.update();
}
