// 현재 접속 환경(로컬 파일 열기, 로컬 서버, 외부 배포)을 감지하여 백엔드 주소를 자동 연결합니다.
const isLocal = window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost" || window.location.hostname === "";
const API_BASE = ""; 

let map, marker, chart;
let setupMap, setupMarker;
let startLat = 37.566, startLon = 126.978;
let overtonMu = 0.0, mediaStance = 0.0;
let clickedLat = startLat, clickedLon = startLon;

document.addEventListener("DOMContentLoaded", () => {
    // 셋업 모달창용 미니맵 초기화
    setupMap = L.map('setup-map').setView([startLat, startLon], 2);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(setupMap);
    setupMarker = L.marker([startLat, startLon]).addTo(setupMap);

    setupMap.on('click', function(e) { 
        startLat = e.latlng.lat; 
        startLon = e.latlng.lng;
        clickedLat = startLat;
        clickedLon = startLon;
        setupMarker.setLatLng([startLat, startLon]); 
        document.getElementById('selected-coords').innerText = `선택된 좌표: 위도 ${startLat.toFixed(3)}, 경도 ${startLon.toFixed(3)}`;
    });
});

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
        options: { responsive: true, maintainAspectRatio: false, scales: { x: { ticks: { color: '#94a3b8' } }, y: { display: false, max: 1.1 } }, animation: { duration: 400 } }
    });
}

function updateChart() {
    let labels = chart.data.labels;
    chart.data.datasets[0].data = labels.map(x => Math.exp(-0.5 * Math.pow((x - overtonMu) / 1.0, 2)));
    chart.data.datasets[1].data = labels.map(x => (Math.abs(x - mediaStance) < 0.05) ? 1.0 : 0);
    chart.update();
}

async function startGame() {
    const btn = document.getElementById('btn-start');
    btn.innerText = "시대 고증 중... (AI 지리 분석)";
    btn.disabled = true;

    const reqYear = parseInt(document.getElementById('start-year').value);

    try {
        const geoRes = await fetch(`${API_BASE}/api/get_historical_country`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({lat: startLat, lon: startLon, year: reqYear})
        });
        const geoData = await geoRes.json();
        const historicalCountry = geoData.country;

        const payload = {
            company_name: document.getElementById('company-name').value || "이름 없는 언론사",
            start_year: reqYear,
            difficulty: document.getElementById('difficulty').value,
            capital: parseInt(document.getElementById('start-cap').value)
        };
        
        const res = await fetch(`${API_BASE}/api/setup`, { 
            method: 'POST', 
            headers: {'Content-Type': 'application/json'}, 
            body: JSON.stringify(payload) 
        });
        
        if (!res.ok) throw new Error("게임 시작 실패");
        
        document.getElementById('setup-modal').style.display = 'none';
        document.getElementById('game-ui').style.display = 'grid';
        
        setTimeout(() => {
            if (!map) {
                map = L.map('map').setView([startLat, startLon], 5);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
                marker = L.marker([startLat, startLon]).addTo(map);
                map.on('click', function(e) { 
                    clickedLat = e.latlng.lat; 
                    clickedLon = e.latlng.lng; 
                    marker.setLatLng([clickedLat, clickedLon]); 
                });
            }
            map.invalidateSize();
        }, 300);
        
        initChart();
        fetchState();

        setTimeout(() => {
            alert(`${reqYear}년, ${historicalCountry}에서 위대한 미디어 제국의 역사가 시작됩니다!`);
        }, 500);

    } catch (e) {
        console.error("초기화 오류:", e);
        alert("서버와 연결할 수 없습니다. 파이썬 백엔드가 구동 중인지 확인하시오.");
        btn.innerText = "역사 속으로 뛰어들기";
        btn.disabled = false;
    }
}

async function fetchState() {
    try {
        const res = await fetch(`${API_BASE}/api/state`);
        const data = await res.json();
        if (!data.is_started) return;

        document.getElementById('ui-company-name').innerText = data.company_name;
        document.getElementById('ui-year').innerText = data.year;
        document.getElementById('ui-cap').innerText = '₩ ' + data.capital.toLocaleString();
        document.getElementById('ui-cred').innerText = data.credibility;
        document.getElementById('ui-reach').innerText = Math.round(data.reach).toLocaleString();
        
        overtonMu = data.overton_mu;
        mediaStance = data.media_stance;
        updateChart();

        let infraHtml = '';
        data.infra.forEach((inf, idx) => {
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
        data.reporters.forEach((r, idx) => {
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
        data.logs.slice().reverse().forEach(l => logHtml += `<div>${l}</div>`);
        document.getElementById('ui-logs').innerHTML = logHtml;

        loadTechs();
    } catch (e) {
        console.error("상태 갱신 오류:", e);
    }
}

async function loadTechs() {
    const res = await fetch(`${API_BASE}/api/techs`);
    const data = await res.json();
    let html = '';
    data.tree.forEach(t => {
        if(t.invent_year <= data.current_year && !data.researched.includes(t.id)) {
            html += `<div style="background:#0f172a; padding:10px; margin-bottom:8px; border:1px solid #334155; display:flex; justify-content:space-between;">
                <div><b>${t.name}</b> <span style="font-size:12px; color:#94a3b8;">(${t.invent_year}년)</span><br><span style="font-size:12px; color:#cbd5e1;">${t.desc}</span></div>
                <button onclick="researchTech('${t.id}')">₩${t.cost/1000}k</button>
            </div>`;
        }
    });
    document.getElementById('tech-list').innerHTML = html;
}

async function advanceTurn() {
    const res = await fetch(`${API_BASE}/api/advance_year`, {method: 'POST'});
    const result = await res.json();
    if (result.status === 'event') {
        document.getElementById('ev-title').innerText = result.event_data.title;
        document.getElementById('ev-desc').innerText = result.event_data.desc;
        let btns = '';
        result.event_data.choices.forEach(c => { btns += `<button class="event-btn" onclick="resolveEvent('${c.id}')"><b>${c.text}</b><br><span style="font-size:12px;color:#fbbf24;">${c.effect}</span></button>`; });
        document.getElementById('ev-choices').innerHTML = btns;
        document.getElementById('event-modal').style.display = 'flex';
    } else if (result.status === 'game_over') { alert(result.message); location.reload(); }
    else fetchState();
}

async function updateStance(val) {
    document.getElementById('ui-stance').innerText = val;
    await fetch(`${API_BASE}/api/stance`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({stance: parseFloat(val)}) });
    mediaStance = parseFloat(val); updateChart();
}

async function doAction(type) { await fetch(`${API_BASE}/api/action/${type}`, {method: 'POST'}); fetchState(); }
async function manageHR(action, idx) { await fetch(`${API_BASE}/api/hr/${action}?idx=${idx}`, {method: 'POST'}); fetchState(); }
async function resolveEvent(choiceId) { await fetch(`${API_BASE}/api/resolve_event`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({choice_id: choiceId}) }); document.getElementById('event-modal').style.display = 'none'; fetchState(); }
async function repairInfra(idx) { await fetch(`${API_BASE}/api/repair/${idx}`, {method: 'POST'}); fetchState(); }
async function researchTech(id) { await fetch(`${API_BASE}/api/research/${id}`, {method: 'POST'}); fetchState(); }

async function buildInfra() {
    const typeVal = document.getElementById('tx-type').value;
    const formatSelect = document.getElementById('tx-format');
    const callsignInput = document.getElementById('tx-callsign');
    
    const payload = {
        type: typeVal, 
        name: document.getElementById('tx-name').value || "지점",
        callsign: callsignInput.disabled ? "" : callsignInput.value,
        band: document.getElementById('tx-band').disabled ? "" : document.getElementById('tx-band').value, 
        format: formatSelect.disabled ? "" : formatSelect.value,
        power_kw: parseInt(document.getElementById('tx-power').value), 
        lat: clickedLat, lon: clickedLon
    };
    const res = await fetch(`${API_BASE}/api/build_infra`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) });
    if(res.ok) { 
        let color = typeVal === 'Print' ? 'gray' : (typeVal === 'Radio' ? 'green' : 'blue');
        L.circle([clickedLat, clickedLon], {radius: payload.power_kw * 1000, color: color, fillOpacity: 0.2}).addTo(map); 
        fetchState(); 
    } else alert("자본 부족 또는 지하 언론 상태입니다.");
}
