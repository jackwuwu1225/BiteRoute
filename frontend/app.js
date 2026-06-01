// 本機測試
const API_URL = 'http://127.0.0.1:8000/api/v1/generate_route';
// 內網測試(填入你電腦的IPv4地址)
//const API_URL = 'http://192.168.0.0:8000/api/v1/generate_route';

const SHAPE_ZH = {
  cassiopeia:      '仙后座',
  aries:           '牡羊座',
  triangulum:      '三角座',
  cepheus:         '仙王座',
  corvus:          '烏鴉座',
  corona_borealis: '北冕座',
  scutum:          '盾牌座',
  norma:           '矩尺座',
  circinus:        '圓規座',
  libra:           '天秤座',
  big_dipper:      '北斗七星',
};

const CONSTELLATION_COORDS = {
  cassiopeia:      [[-0.90, 0.10], [-0.45, 0.75], [0.00, 0.15], [0.45, 0.75], [0.90, 0.10]],
  aries:           [[-0.80, 0.80], [0.00, 0.20], [0.60, -0.50], [0.80, -0.80]],
  triangulum:      [[-0.70, -0.40], [0.00, 0.75], [0.80, -0.25]],
  cepheus:         [[-0.50, -0.55], [-0.50, 0.25], [0.00, 0.85], [0.50, 0.25], [0.50, -0.55]],
  corvus:          [[-0.65, -0.50], [-0.30, 0.55], [0.30, 0.55], [0.65, -0.50]],
  corona_borealis: [[-0.90, 0.00], [-0.73, 0.53], [-0.28, 0.86], [0.28, 0.86], [0.73, 0.53], [0.90, 0.00]],
  scutum:          [[0.00, 0.85], [0.60, 0.10], [0.00, -0.70], [-0.40, 0.25]],
  norma:           [[-0.75, 0.65], [-0.75, -0.55], [0.75, -0.55]],
  circinus:        [[-0.35, 0.75], [0.00, -0.65], [0.35, 0.75]],
  libra:           [[-0.80, -1.00], [-0.20, 0.20], [0.50, 1.00], [0.90, 0.00], [0.20, -0.80]],
  big_dipper:      [[-1.00, 0.35], [-0.55, 0.25], [-0.20, 0.00], [0.10, -0.30], [0.10, -0.80], [0.55, -0.95], [0.90, -0.50]],
};

const CLOSED_SHAPES_JS = new Set(['triangulum', 'cepheus', 'corvus', 'scutum']);

const FALLBACK_COORDS = { coords: { latitude: 22.9997, longitude: 120.2185 } };

const LOADING_MESSAGES = [
  '正在過濾高分餐廳...',
  '正在計算天文座標...',
  '正在為您連線星圖...',
];

let selectedTheme  = 'dessert_run';
let routeData      = null;
let _loadingTimer  = null;

function sliderBg(slider, color) {
  const pct = ((+slider.value - +slider.min) / (+slider.max - +slider.min)) * 100;
  slider.style.background =
    `linear-gradient(to right,${color} ${pct}%,rgba(255,255,255,0.13) ${pct}%)`;
}

function showState(state) {
  const panels = { input: 'inputPanel', loading: 'loadingPanel', result: 'resultPanel' };
  Object.entries(panels).forEach(([key, id]) => {
    document.getElementById(id).classList.toggle('hidden', key !== state);
  });
}

function setLoadingText(text) {
  document.getElementById('loadingText').textContent = text;
}

function setLoadingIcon(iconClass) {
  document.getElementById('loadingIcon').className = `fa-solid ${iconClass} text-cyan-400 text-2xl`;
}

function showToast(msg, type = 'info') {
  const container = document.getElementById('toastContainer');
  const el = document.createElement('div');

  const palette = { error: 'rgba(40,10,10,0.92)', success: 'rgba(5,30,15,0.92)', info: 'rgba(5,20,35,0.92)' };
  const border  = { error: 'rgba(255,80,80,0.45)', success: 'rgba(0,229,120,0.45)', info: 'rgba(0,229,255,0.45)' };

  el.style.cssText = `
    background:${palette[type] || palette.info};
    border:1px solid ${border[type] || border.info};
    backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);
    border-radius:14px;padding:10px 14px;font-size:13px;
    color:rgba(255,255,255,0.88);line-height:1.4;
    pointer-events:auto;box-shadow:0 4px 24px rgba(0,0,0,0.5);
  `;
  el.className = 'toast-enter';
  el.textContent = msg;
  container.appendChild(el);

  setTimeout(() => {
    el.classList.replace('toast-enter', 'toast-exit');
    el.addEventListener('animationend', () => el.remove(), { once: true });
  }, 3400);
}

function validateBudget(budget) {
  if (budget < 150) {
    showToast("這點錢只能畫一個『點』喔！去巷口買御飯糰吧 🍙", 'error');
    return false;
  }
  if (budget < 300) {
    showToast("演算法表示：臣妾做不到啊！加點預算解鎖星圖吧 ✨", 'error');
    return false;
  }
  if (budget > 3000) {
    showToast("乾爹您好！已為您啟動財富自由導航模式 💰", 'success');
  }
  return true;
}

function getPosition() {
  return new Promise((resolve) => {
    if (!navigator.geolocation) {
      showToast('GPS 訊號微弱，使用預設位置（成大光復校區）...', 'info');
      resolve(FALLBACK_COORDS);
      return;
    }
    navigator.geolocation.getCurrentPosition(resolve, () => {
      showToast('GPS 訊號微弱，使用預設位置（成大光復校區）...', 'info');
      resolve(FALLBACK_COORDS);
    }, { timeout: 5000, maximumAge: 60000, enableHighAccuracy: true });
  });
}

function startLoadingCycle() {
  let idx = 0;
  setLoadingText(LOADING_MESSAGES[idx]);
  setLoadingIcon('fa-star');
  _loadingTimer = setInterval(() => {
    idx = (idx + 1) % LOADING_MESSAGES.length;
    setLoadingText(LOADING_MESSAGES[idx]);
  }, 1500);
}

function stopLoadingCycle() {
  clearInterval(_loadingTimer);
  _loadingTimer = null;
}

function injectMap(mapHtml) {
  const container = document.getElementById('mapContainer');
  container.innerHTML = '';
  const blob  = new Blob([mapHtml], { type: 'text/html' });
  const url   = URL.createObjectURL(blob);
  const frame = document.createElement('iframe');
  frame.src = url;
  frame.style.cssText = 'position:absolute;top:0;left:0;width:100%;height:100%;border:none;';
  frame.onload = () => URL.revokeObjectURL(url);
  container.appendChild(frame);
}

async function generateRoute() {
  const budget = +document.getElementById('budgetSlider').value;
  const radius = +document.getElementById('radiusSlider').value;
  const showYoubike = document.getElementById('showYoubike').checked;

  if (!validateBudget(budget)) return;

  showState('loading');
  setLoadingText('📍 正在獲取定位...');
  setLoadingIcon('fa-location-crosshairs');

  const position = await getPosition();

  startLoadingCycle();

  const DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  const now          = new Date();
  const current_day  = DAYS[now.getDay()];
  const inputTime    = document.getElementById('departureTime').value;
  const current_time = inputTime || `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;

  try {
    const res = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ui_theme:             selectedTheme,
        search_radius_meters: radius,
        total_budget:         budget,
        user_lat:             position.coords.latitude,
        user_lng:             position.coords.longitude,
        departure_time:       inputTime || null,
        current_day,
        current_time,
        show_youbike:         showYoubike,
      }),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const data = await res.json();
    routeData = data;

    if (data.status !== 'success') {
      const errMap = {
        insufficient_restaurants: '附近主題餐廳不足，試試擴大探索半徑？',
        no_valid_route:           '預算內找不到合適組合，試試調高預算？',
      };
      showToast(errMap[data.status] || '路線生成失敗，請稍後再試', 'error');
      showState('input');
      return;
    }

    const displayName = data.matched_shape_name
      || SHAPE_ZH[data.constellation_matched]
      || data.constellation_matched;

    document.getElementById('constellationBadge').textContent = displayName;
    document.getElementById('priceBadge').textContent = `$ ${(+data.total_price).toLocaleString()}`;

    injectMap(data.map_html);
    showState('result');

  } catch (err) {
    showToast('連線失敗：請確認後端伺服器已啟動 (port 8000)', 'error');
    showState('input');
  } finally {
    stopLoadingCycle();
  }
}

function openMapsNavigation() {
  const stops = routeData?.assignments;
  if (!stops?.length) return;
  const origin      = `${stops[0].lat},${stops[0].lng}`;
  const destination = `${stops[stops.length - 1].lat},${stops[stops.length - 1].lng}`;
  const mid         = stops.slice(1, -1).map(s => `${s.lat},${s.lng}`).join('|');
  let url = `https://www.google.com/maps/dir/?api=1&origin=${origin}&destination=${destination}&travelmode=walking`;
  if (mid) url += `&waypoints=${encodeURIComponent(mid)}`;
  window.open(url, '_blank');
}

async function shareRoute() {
  if (!routeData) return;
  const name      = routeData.matched_shape_name || SHAPE_ZH[routeData.constellation_matched] || routeData.constellation_matched;
  const stops     = routeData.assignments?.map(a => a.name).join(' → ') || '';
  const text      = `我剛用 BiteRoute 生成了「${name}」路線！${stops ? `路線：${stops}` : ''}`;
  const shareData = { title: 'My BiteRoute Star Map!', text, url: window.location.href };

  const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
  if (isTouchDevice && navigator.share && navigator.canShare?.(shareData)) {
    try {
      await navigator.share(shareData);
      return;
    } catch (e) {
      if (e.name === 'AbortError') return;
    }
  }

  const copyText = `${shareData.text}\n${shareData.url}`;
  try {
    await navigator.clipboard.writeText(copyText);
    showToast('路線連結已複製到剪貼簿！', 'success');
  } catch {
    const ta = document.createElement('textarea');
    ta.value = copyText;
    ta.style.cssText = 'position:fixed;left:-9999px;top:-9999px;opacity:0;';
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    const ok = document.execCommand('copy');
    ta.remove();
    showToast(ok ? '路線連結已複製到剪貼簿！' : '分享失敗，請手動複製連結', ok ? 'success' : 'error');
  }
}

function resetApp() {
  routeData = null;
  document.getElementById('mapContainer').innerHTML = '';
  showState('input');
}

function buildConstellationSVG(shapeKey) {
  const W = 260, H = 200, pad = 22;
  const dw = W - 2 * pad, dh = H - 2 * pad;
  const pts = CONSTELLATION_COORDS[shapeKey];

  if (!pts) {
    return `<svg width="${W}" height="${H}"><rect width="${W}" height="${H}" fill="#020210"/></svg>`;
  }

  const toSVG = ([nx, ny]) => [
    pad + (nx + 1) / 2 * dw,
    pad + (1 - (ny + 1) / 2) * dh,
  ];

  const svgPts  = pts.map(toSVG);
  const drawPts = CLOSED_SHAPES_JS.has(shapeKey) ? [...svgPts, svgPts[0]] : svgPts;
  const polyStr = drawPts.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(' ');

  const rng   = (lo, hi) => Math.random() * (hi - lo) + lo;
  const stars = Array.from({ length: 55 }, () => {
    const x = rng(0, W), y = rng(0, H);
    const r = rng(0.3, 1.3), op = rng(0.08, 0.55);
    return `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${r.toFixed(1)}" fill="white" opacity="${op.toFixed(2)}"/>`;
  }).join('');

  const nodeDots = svgPts.map(([x, y]) => `
    <circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="10" fill="#00e5ff" opacity="0.06"/>
    <circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="5.5" fill="#00e5ff" opacity="0.16"/>
    <circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="2.8" fill="#00e5ff"/>
    <circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="1.1" fill="white" opacity="0.92"/>
  `).join('');

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" style="display:block;">
    <defs>
      <radialGradient id="cBg" cx="50%" cy="50%" r="65%">
        <stop offset="0%"   stop-color="#061540"/>
        <stop offset="100%" stop-color="#020210"/>
      </radialGradient>
    </defs>
    <rect width="${W}" height="${H}" fill="url(#cBg)"/>
    ${stars}
    <polyline points="${polyStr}" fill="none" stroke="#00e5ff" stroke-width="3.5"
      stroke-linecap="round" stroke-linejoin="round" opacity="0.10"/>
    <polyline points="${polyStr}" fill="none" stroke="#00e5ff" stroke-width="1.1"
      stroke-linecap="round" stroke-linejoin="round" opacity="0.82"/>
    ${nodeDots}
  </svg>`;
}

function buildStatsOverlay(displayName, price) {
  const shapeKey   = routeData?.constellation_matched;
  const svgMarkup  = buildConstellationSVG(shapeKey);

  const el = document.createElement('div');
  el.id = 'statsOverlay';
  el.style.cssText = `
    position:absolute;inset:0;z-index:9999;
    display:flex;flex-direction:column;align-items:center;justify-content:center;
    background:radial-gradient(ellipse at 50% 38%,rgba(6,18,54,0.95) 0%,rgba(2,2,14,0.97) 68%);
    padding:24px 28px;font-family:'Space Grotesk',sans-serif;box-sizing:border-box;
  `;

  el.innerHTML = `
    <div style="width:100%;max-width:320px;display:flex;flex-direction:column;align-items:center;">
      <div style="display:flex;align-items:center;gap:8px;width:100%;margin-bottom:14px;">
        <div style="flex:1;height:1px;background:linear-gradient(to right,transparent,rgba(0,229,255,0.5));"></div>
        <span style="color:rgba(0,229,255,0.65);font-size:10px;letter-spacing:.28em;text-transform:uppercase;">BiteRoute</span>
        <div style="flex:1;height:1px;background:linear-gradient(to left,transparent,rgba(0,229,255,0.5));"></div>
      </div>
      <div style="border:1px solid rgba(0,229,255,0.18);border-radius:14px;overflow:hidden;
                  margin-bottom:14px;box-shadow:0 0 40px rgba(0,229,255,0.10),inset 0 0 20px rgba(0,229,255,0.04);">
        ${svgMarkup}
      </div>
      <div style="color:rgba(255,255,255,0.35);font-size:10px;letter-spacing:.2em;text-transform:uppercase;margin-bottom:5px;">解鎖星座</div>
      <div style="color:#fff;font-size:26px;font-weight:700;letter-spacing:-.01em;line-height:1.15;
                  margin-bottom:14px;text-shadow:0 0 28px rgba(0,229,255,0.35);">${displayName}</div>
      <div style="display:block;text-align:center;
                  background:rgba(0,229,255,0.07);border:1px solid rgba(0,229,255,0.2);
                  border-radius:10px;padding:12px 24px;margin:0 auto 16px auto;
                  min-width:160px;box-sizing:border-box;white-space:nowrap;">
        <span style="color:rgba(255,255,255,0.38);font-size:11px;letter-spacing:.12em;
                     display:inline-block;vertical-align:middle;line-height:1;
                     white-space:nowrap;margin-right:8px;
                     position:relative;top:-4px;">TOTAL</span>
        <span style="color:#00e5ff;font-size:22px;font-weight:700;
                     display:inline-block;vertical-align:middle;line-height:1;
                     white-space:nowrap;position:relative;top:-4px;
                     text-shadow:0 0 14px rgba(0,229,255,0.65);">$ ${(+price).toLocaleString()}</span>
      </div>
      <div style="color:rgba(255,255,255,0.14);font-size:9px;letter-spacing:.2em;">biteroute.app</div>
    </div>
  `;
  return el;
}

function cropTo45(src) {
  const ratio = 4 / 5;
  const srcR  = src.width / src.height;
  let sx = 0, sy = 0, sw = src.width, sh = src.height;
  if (srcR > ratio) { sw = Math.round(sh * ratio); sx = Math.round((src.width - sw) / 2); }
  else               { sh = Math.round(sw / ratio); sy = Math.round((src.height - sh) / 2); }
  const out = document.createElement('canvas');
  out.width  = sw;
  out.height = sh;
  out.getContext('2d').drawImage(src, sx, sy, sw, sh, 0, 0, sw, sh);
  return out;
}

function applyFilmGrain(canvas, intensity) {
  const ctx  = canvas.getContext('2d');
  const data = ctx.getImageData(0, 0, canvas.width, canvas.height);
  const px   = data.data;
  for (let i = 0; i < px.length; i += 4) {
    const g = (Math.random() - 0.5) * intensity;
    px[i]     = Math.min(255, Math.max(0, px[i]     + g));
    px[i + 1] = Math.min(255, Math.max(0, px[i + 1] + g));
    px[i + 2] = Math.min(255, Math.max(0, px[i + 2] + g));
  }
  ctx.putImageData(data, 0, 0);
}

async function shareToIG() {
  if (!routeData) return;

  const displayName = routeData.matched_shape_name
    || SHAPE_ZH[routeData.constellation_matched]
    || routeData.constellation_matched;

  const mapContainer = document.getElementById('mapContainer');
  const overlay = buildStatsOverlay(displayName, routeData.total_price);
  mapContainer.style.position = 'relative';
  mapContainer.appendChild(overlay);

  await new Promise(r => setTimeout(r, 320));

  try {
    const canvas = await html2canvas(mapContainer, {
      allowTaint:             true,
      useCORS:                true,
      scale:                  2,
      backgroundColor:        '#05050f',
      logging:                false,
      foreignObjectRendering: false,
      ignoreElements:         el => el.tagName === 'IFRAME',
      onclone: (clonedDoc) => {
        const style = clonedDoc.createElement('style');
        style.innerHTML = `
          #statsOverlay span {
            transform: translateY(-4px) !important;
            display: inline-block !important;
          }
          #statsOverlay div[style*="font-size"] {
            transform: translateY(-4px) !important;
          }
        `;
        clonedDoc.head.appendChild(style);
      },
    });

    const cropped = cropTo45(canvas);
    applyFilmGrain(cropped, 38);

    const link = document.createElement('a');
    link.download = `biteroute_${routeData.constellation_matched || 'route'}.png`;
    link.href     = cropped.toDataURL('image/png', 0.95);
    link.click();

    showToast('截圖已儲存！快去 IG 曬出你的星圖 🌟', 'success');
  } catch (e) {
    showToast('截圖失敗，請手動截圖分享 📸', 'error');
  } finally {
    overlay.remove();
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const budgetSlider = document.getElementById('budgetSlider');
  const radiusSlider = document.getElementById('radiusSlider');

  sliderBg(budgetSlider, '#00e5ff');
  sliderBg(radiusSlider, '#ff006e');

  budgetSlider.addEventListener('input', () => {
    document.getElementById('budgetDisplay').textContent = `$ ${(+budgetSlider.value).toLocaleString()}`;
    sliderBg(budgetSlider, '#00e5ff');
  });

  radiusSlider.addEventListener('input', () => {
    const val = +radiusSlider.value;
    document.getElementById('radiusDisplay').textContent = `${val} m`;
    sliderBg(radiusSlider, '#ff006e');
    document.getElementById('bikeWarning').style.display = val > 1500 ? 'flex' : 'none';
  });

  document.querySelectorAll('.theme-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.theme-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      selectedTheme = btn.dataset.theme;
    });
  });

  document.getElementById('btnGenerate').addEventListener('click', generateRoute);
  document.getElementById('btnNavigate').addEventListener('click', openMapsNavigation);
  document.getElementById('btnShareRoute').addEventListener('click', shareRoute);
  document.getElementById('btnShare').addEventListener('click', shareToIG);
  document.getElementById('btnReset').addEventListener('click', resetApp);
});
