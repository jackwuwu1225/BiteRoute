// API endpoint for route generation
const API_URL = 'http://127.0.0.1:8000/api/v1/generate_route';

// Shape Chinese display names (mirrors backend SHAPE_ZH_NAMES)
const SHAPE_ZH = {
  triangle:       '三角',
  square:         '正方',
  v_shape:        'V形',
  diamond:        '菱形',
  orion:          '獵戶座',
  big_dipper:     '北斗七星',
  southern_cross: '南十字座',
  cassiopeia:     '仙后座',
  scorpius:       '天蠍座',
};

let selectedTheme = 'dessert_run';
let routeData     = null;

// Update slider fill gradient based on current value
function sliderBg(slider, color) {
  const pct = ((+slider.value - +slider.min) / (+slider.max - +slider.min)) * 100;
  slider.style.background =
    `linear-gradient(to right,${color} ${pct}%,rgba(255,255,255,0.13) ${pct}%)`;
}

// Show one of the three app panels, hide the others
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

// Slide-in toast notification (auto-dismisses after 3.4 s)
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

// Humorous budget gate — blocks clearly impossible budgets
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

// Wrap Geolocation API in a Promise
function getPosition() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('瀏覽器不支援定位功能'));
      return;
    }
    navigator.geolocation.getCurrentPosition(resolve, reject, {
      timeout: 12000, maximumAge: 60000, enableHighAccuracy: true,
    });
  });
}

function geoErrorMsg(err) {
  const msgs = {
    1: '定位權限被拒絕，請在瀏覽器設定中允許位置存取',
    2: '無法取得位置，請確認 GPS 已開啟',
    3: '定位請求超時，請稍後再試',
  };
  return msgs[err.code] || ('定位失敗：' + err.message);
}

// Load Folium HTML via Blob URL to avoid cross-origin issues
function injectMap(mapHtml) {
  const container = document.getElementById('mapContainer');
  container.innerHTML = '';
  const blob  = new Blob([mapHtml], { type: 'text/html' });
  const url   = URL.createObjectURL(blob);
  const frame = document.createElement('iframe');
  frame.src = url;
  frame.style.cssText = 'width:100%;height:100%;border:none;display:block;';
  frame.onload = () => URL.revokeObjectURL(url);
  container.appendChild(frame);
}

async function generateRoute() {
  const budget = +document.getElementById('budgetSlider').value;
  const radius = +document.getElementById('radiusSlider').value;

  if (!validateBudget(budget)) return;

  showState('loading');
  setLoadingText('📍 正在獲取定位...');
  setLoadingIcon('fa-location-crosshairs');

  let position;
  try {
    position = await getPosition();
  } catch (err) {
    showToast(geoErrorMsg(err), 'error');
    showState('input');
    return;
  }

  setLoadingText('🌌 演算法尋找星圖中...');
  setLoadingIcon('fa-star');

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
        departure_time:       document.getElementById('departureTime').value || null,
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

    // Backend already provides the Chinese name; local map is a fallback
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
  }
}

function resetApp() {
  routeData = null;
  document.getElementById('mapContainer').innerHTML = '';
  showState('input');
}

// Build a dark gradient overlay div for IG export card
function buildStatsOverlay(displayName, price) {
  const el = document.createElement('div');
  el.id = 'statsOverlay';
  el.style.cssText = `
    position:absolute;inset:0;z-index:9999;
    display:flex;flex-direction:column;justify-content:flex-end;
    background:linear-gradient(to bottom,rgba(5,5,15,0.15) 0%,rgba(5,5,15,0.9) 60%,rgba(5,5,15,0.97) 100%);
    padding:0 28px 36px;font-family:'Space Grotesk',sans-serif;
  `;
  el.innerHTML = `
    <div style="text-align:center;">
      <div style="display:flex;align-items:center;justify-content:center;gap:10px;margin-bottom:10px;">
        <div style="flex:1;height:1px;background:linear-gradient(to right,transparent,rgba(0,229,255,0.55));"></div>
        <span style="color:rgba(0,229,255,0.65);font-size:11px;letter-spacing:.2em;text-transform:uppercase;">BiteRoute</span>
        <div style="flex:1;height:1px;background:linear-gradient(to left,transparent,rgba(0,229,255,0.55));"></div>
      </div>
      <div style="color:rgba(255,255,255,0.4);font-size:12px;letter-spacing:.15em;margin-bottom:6px;">解鎖星座</div>
      <div style="color:#fff;font-size:32px;font-weight:700;letter-spacing:-.02em;line-height:1.1;margin-bottom:22px;">${displayName}</div>
      <div style="display:inline-flex;align-items:center;gap:6px;background:rgba(0,229,255,0.1);
                  border:1px solid rgba(0,229,255,0.25);border-radius:12px;padding:10px 24px;margin-bottom:24px;">
        <span style="color:rgba(255,255,255,0.45);font-size:12px;letter-spacing:.1em;">TOTAL</span>
        <span style="color:#00e5ff;font-size:26px;font-weight:700;text-shadow:0 0 18px rgba(0,229,255,0.8);">
          $ ${(+price).toLocaleString()}
        </span>
      </div>
      <div style="color:rgba(255,255,255,0.18);font-size:10px;letter-spacing:.18em;">biteroute.app</div>
    </div>
  `;
  return el;
}

// Center-crop canvas to strict 4:5 aspect ratio
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

// Apply per-pixel random noise for film grain effect
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

  // Short delay so overlay renders before capture
  await new Promise(r => setTimeout(r, 320));

  try {
    // html2canvas skips iframes (Folium tiles); overlay provides the visual content
    const canvas = await html2canvas(mapContainer, {
      allowTaint:             true,
      useCORS:                true,
      scale:                  2,
      backgroundColor:        '#05050f',
      logging:                false,
      foreignObjectRendering: false,
      ignoreElements:         el => el.tagName === 'IFRAME',
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

// Wire up all UI interactions after DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const budgetSlider = document.getElementById('budgetSlider');
  const radiusSlider = document.getElementById('radiusSlider');

  // Initialize slider fill gradients on first paint
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

  // Theme selection — highlight active button
  document.querySelectorAll('.theme-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.theme-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      selectedTheme = btn.dataset.theme;
    });
  });

  document.getElementById('btnGenerate').addEventListener('click', generateRoute);
  document.getElementById('btnShare').addEventListener('click', shareToIG);
  document.getElementById('btnReset').addEventListener('click', resetApp);
});
