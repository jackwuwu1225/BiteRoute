// frontend/badges.js

const BADGE_STORAGE_KEY = "biteroute_unlocked_badges";
const CURRENT_ROUTE_KEY = "biteroute_current_route";

/*
  Badge id 必須對應後端 core/constants.py 的 SHAPE_MATRICES key：
  cassiopeia, aries, triangulum, cepheus, corvus,
  corona_borealis, scutum, norma, circinus, libra, big_dipper
*/
const CONSTELLATION_BADGES = [
  {
    id: "cassiopeia",
    name: "仙后座",
    emoji: "👸",
    description: "完成鋸齒狀星圖路線，解鎖優雅又鮮明的仙后座。",
    type: "constellation"
  },
  {
    id: "aries",
    name: "牡羊座",
    emoji: "🐏",
    description: "完成充滿行動感的星圖路線，解鎖牡羊座徽章。",
    type: "constellation"
  },
  {
    id: "triangulum",
    name: "三角座",
    emoji: "🔺",
    description: "完成三站式星圖路線，解鎖簡潔俐落的三角座。",
    type: "constellation"
  },
  {
    id: "cepheus",
    name: "仙王座",
    emoji: "👑",
    description: "完成穩定且具王冠感的星圖路線，解鎖仙王座。",
    type: "constellation"
  },
  {
    id: "corvus",
    name: "烏鴉座",
    emoji: "🐦‍⬛",
    description: "完成神秘感十足的城市探索，解鎖烏鴉座徽章。",
    type: "constellation"
  },
  {
    id: "corona_borealis",
    name: "北冕座",
    emoji: "💫",
    description: "完成弧形星冠路線，解鎖具有儀式感的北冕座。",
    type: "constellation"
  },
  {
    id: "scutum",
    name: "盾牌座",
    emoji: "🛡️",
    description: "完成穩健型星圖路線，解鎖守護感十足的盾牌座。",
    type: "constellation"
  },
  {
    id: "norma",
    name: "矩尺座",
    emoji: "📐",
    description: "完成俐落幾何路線，解鎖具有秩序感的矩尺座。",
    type: "constellation"
  },
  {
    id: "circinus",
    name: "圓規座",
    emoji: "🧭",
    description: "完成對稱感星圖路線，解鎖探索感十足的圓規座。",
    type: "constellation"
  },
  {
    id: "libra",
    name: "天秤座",
    emoji: "⚖️",
    description: "完成兼顧預算、距離與評分的平衡路線，解鎖天秤座。",
    type: "constellation"
  },
  {
    id: "big_dipper",
    name: "北斗七星",
    emoji: "🌟",
    description: "完成經典七星路線，解鎖最具代表性的北斗七星徽章。",
    type: "constellation"
  }
];

const REWARD_BADGES = [
  {
    id: "star_collector_5",
    name: "星圖收藏家",
    emoji: "🏅",
    description: "蒐集滿 5 個不同星座徽章後自動解鎖。",
    type: "reward",
    requiredCount: 5
  },
  {
    id: "galaxy_master",
    name: "銀河探索者",
    emoji: "🌌",
    description: "蒐集所有星座徽章後自動解鎖。",
    type: "reward",
    requiredCount: CONSTELLATION_BADGES.length
  }
];

const ALL_BADGES = [...CONSTELLATION_BADGES, ...REWARD_BADGES];

function normalizeBadgeId(value) {
  if (!value) return "";

  const raw = String(value).trim();

  const aliasMap = {
    "仙后座": "cassiopeia",
    "牡羊座": "aries",
    "白羊座": "aries",
    "三角座": "triangulum",
    "仙王座": "cepheus",
    "烏鴉座": "corvus",
    "北冕座": "corona_borealis",
    "盾牌座": "scutum",
    "矩尺座": "norma",
    "圓規座": "circinus",
    "天秤座": "libra",
    "北斗七星": "big_dipper",

    "Cassiopeia": "cassiopeia",
    "Aries": "aries",
    "Triangulum": "triangulum",
    "Cepheus": "cepheus",
    "Corvus": "corvus",
    "Corona Borealis": "corona_borealis",
    "Corona_Borealis": "corona_borealis",
    "Scutum": "scutum",
    "Norma": "norma",
    "Circinus": "circinus",
    "Libra": "libra",
    "Big Dipper": "big_dipper",
    "Big_Dipper": "big_dipper",

    "cassiopeia": "cassiopeia",
    "aries": "aries",
    "triangulum": "triangulum",
    "cepheus": "cepheus",
    "corvus": "corvus",
    "corona_borealis": "corona_borealis",
    "scutum": "scutum",
    "norma": "norma",
    "circinus": "circinus",
    "libra": "libra",
    "big_dipper": "big_dipper"
  };

  if (aliasMap[raw]) {
    return aliasMap[raw];
  }

  return raw
    .toLowerCase()
    .replace(/\s+/g, "_")
    .replace(/-/g, "_");
}

function getUnlockedBadges() {
  try {
    return JSON.parse(localStorage.getItem(BADGE_STORAGE_KEY)) || [];
  } catch (error) {
    console.warn("讀取徽章資料失敗，已重置。", error);
    return [];
  }
}

function saveUnlockedBadges(unlockedBadges) {
  localStorage.setItem(BADGE_STORAGE_KEY, JSON.stringify(unlockedBadges));
}

function getBadgeById(badgeId) {
  return ALL_BADGES.find((badge) => badge.id === badgeId);
}

function getUnlockedConstellationCount(unlockedBadges) {
  const constellationIds = CONSTELLATION_BADGES.map((badge) => badge.id);

  return unlockedBadges.filter((badgeId) =>
    constellationIds.includes(badgeId)
  ).length;
}

function checkAutoRewardUnlock(unlockedBadges) {
  let updatedBadges = [...unlockedBadges];
  const constellationCount = getUnlockedConstellationCount(updatedBadges);

  REWARD_BADGES.forEach((rewardBadge) => {
    const canUnlock = constellationCount >= rewardBadge.requiredCount;
    const alreadyUnlocked = updatedBadges.includes(rewardBadge.id);

    if (canUnlock && !alreadyUnlocked) {
      updatedBadges.push(rewardBadge.id);
      showBadgeToast(`🎁 自動解鎖回饋徽章：「${rewardBadge.name}」`);
    }
  });

  return updatedBadges;
}

function unlockBadge(badgeId, options = {}) {
  const normalizedId = normalizeBadgeId(badgeId);
  const badge = getBadgeById(normalizedId);

  if (!badge) {
    console.warn("找不到對應的徽章：", badgeId);
    showBadgeToast("目前星座尚未建立對應徽章。");
    return false;
  }

  let unlockedBadges = getUnlockedBadges();

  if (unlockedBadges.includes(normalizedId)) {
    if (!options.silent) {
      showBadgeToast(`你已經解鎖過「${badge.name}」徽章。`);
    }
    renderBadgeGallery();
    return false;
  }

  unlockedBadges.push(normalizedId);
  showBadgeToast(`🏅 解鎖新徽章：「${badge.name}」`);

  unlockedBadges = checkAutoRewardUnlock(unlockedBadges);
  saveUnlockedBadges(unlockedBadges);
  renderBadgeGallery();

  return true;
}

function setCurrentRouteFromResponse(routeData) {
  if (!routeData || routeData.status !== "success") {
    return;
  }

  const constellationId = normalizeBadgeId(
    routeData.constellation_matched ||
    routeData.constellation ||
    routeData.shape
  );

  const constellationName =
    routeData.matched_shape_name ||
    routeData.constellation_name ||
    routeData.constellation ||
    routeData.shape ||
    "未知星圖";

  const routeInfo = {
    constellationId,
    constellationName,
    totalPrice: routeData.total_price || routeData.totalPrice || 0
  };

  localStorage.setItem(CURRENT_ROUTE_KEY, JSON.stringify(routeInfo));
  renderBadgeGallery();
}

function getCurrentRoute() {
  try {
    return JSON.parse(localStorage.getItem(CURRENT_ROUTE_KEY));
  } catch (error) {
    return null;
  }
}

function completeCurrentRoute() {
  const currentRoute = getCurrentRoute();

  if (!currentRoute || !currentRoute.constellationId) {
    showBadgeToast("目前沒有可完成的星圖路線，請先生成路線。");
    return;
  }

  unlockBadge(currentRoute.constellationId);
}

function resetBadgesForDemo() {
  const confirmed = confirm("確定要清除所有徽章紀錄嗎？這個動作主要用於 demo 測試。");

  if (!confirmed) return;

  localStorage.removeItem(BADGE_STORAGE_KEY);
  localStorage.removeItem(CURRENT_ROUTE_KEY);
  renderBadgeGallery();
  showBadgeToast("已清除徽章紀錄。");
}

function renderBadgeGallery() {
  const container = document.getElementById("badge-gallery-content");

  if (!container) {
    console.warn("找不到 #badge-gallery-content，請確認 index.html 是否有加入徽章畫面容器。");
    return;
  }

  const unlockedBadges = getUnlockedBadges();
  const unlockedSet = new Set(unlockedBadges);
  const unlockedConstellationCount = getUnlockedConstellationCount(unlockedBadges);
  const currentRoute = getCurrentRoute();

  const constellationBadgeCards = CONSTELLATION_BADGES.map((badge) => {
    const isUnlocked = unlockedSet.has(badge.id);

    return `
      <div class="br-badge-card ${isUnlocked ? "is-unlocked" : "is-locked"}">
        <div class="br-badge-icon">${isUnlocked ? badge.emoji : "🔒"}</div>
        <div class="br-badge-name">${badge.name}</div>
        <div class="br-badge-desc">${isUnlocked ? badge.description : "尚未解鎖"}</div>
      </div>
    `;
  }).join("");

  const rewardBadgeCards = REWARD_BADGES.map((badge) => {
    const isUnlocked = unlockedSet.has(badge.id);

    return `
      <div class="br-badge-card reward ${isUnlocked ? "is-unlocked" : "is-locked"}">
        <div class="br-badge-icon">${isUnlocked ? badge.emoji : "🔒"}</div>
        <div class="br-badge-name">${badge.name}</div>
        <div class="br-badge-desc">
          ${isUnlocked ? badge.description : `蒐集 ${badge.requiredCount} 個星座徽章後解鎖`}
        </div>
      </div>
    `;
  }).join("");

  const progressPercent = Math.round(
    (unlockedConstellationCount / CONSTELLATION_BADGES.length) * 100
  );

  const currentRouteHtml = currentRoute
    ? `
      <div class="br-current-route readonly">
        <div>
          <span class="br-current-label">目前生成的星圖</span>
          <strong>${currentRoute.constellationName}</strong>
          <p>完成原本路線打卡流程後，將自動解鎖對應徽章。</p>
        </div>
        <button id="br-complete-star-route-btn" class="br-complete-star-route-btn">
            完成星圖
        </button>
      </div>
    `
    : `
      <div class="br-current-route empty">
        <div>
          <span class="br-current-label">目前生成的星圖</span>
          <strong>尚未生成路線</strong>
          <p>生成路線後，這裡會顯示目前可解鎖的星座。</p>
        </div>
      </div>
    `;

  container.innerHTML = `
    <div class="br-gallery-card">
      <div class="br-gallery-header">
        <div>
          <h2>🌌 Badge Gallery</h2>
          <p>完成不同星圖路線，蒐集專屬星座徽章。</p>
        </div>
        <button id="br-reset-badges-btn" class="br-secondary-btn">重置</button>
      </div>

      <div class="br-progress-box">
        <div class="br-progress-text">
          <span>星座徽章進度</span>
          <strong>${unlockedConstellationCount} / ${CONSTELLATION_BADGES.length}</strong>
        </div>
        <div class="br-progress-track">
          <div class="br-progress-fill" style="width: ${progressPercent}%"></div>
        </div>
        <p class="br-progress-hint">蒐集滿 5 個不同星座徽章，會自動解鎖「星圖收藏家」。</p>
      </div>

      ${currentRouteHtml}

      <h3>星座徽章</h3>
      <div class="br-badge-grid">
        ${constellationBadgeCards}
      </div>

      <h3>回饋徽章</h3>
      <div class="br-badge-grid">
        ${rewardBadgeCards}
      </div>
    </div>
  `;

  const resetBtn = document.getElementById("br-reset-badges-btn");
  if (resetBtn) {
    resetBtn.addEventListener("click", resetBadgesForDemo);
  }

  const completeStarRouteBtn = document.getElementById("br-complete-star-route-btn");
  if (completeStarRouteBtn) {
    completeStarRouteBtn.addEventListener("click", completeCurrentRoute);
  }
}

function showBadgeToast(message) {
  let toast = document.getElementById("br-badge-toast");

  if (!toast) {
    toast = document.createElement("div");
    toast.id = "br-badge-toast";
    document.body.appendChild(toast);
  }

  toast.textContent = message;
  toast.classList.add("show");

  setTimeout(() => {
    toast.classList.remove("show");
  }, 2600);
}

//畫面切換函式
function showBadgeScreen() {
  const mainScreen = document.getElementById("main-screen");
  const badgeScreen = document.getElementById("badge-screen");

  if (mainScreen) {
    mainScreen.classList.add("screen-hidden");
  }

  if (badgeScreen) {
    badgeScreen.classList.remove("screen-hidden");
  }

  renderBadgeGallery();
}

function showMainScreen() {
  const mainScreen = document.getElementById("main-screen");
  const badgeScreen = document.getElementById("badge-screen");

  if (badgeScreen) {
    badgeScreen.classList.add("screen-hidden");
  }

  if (mainScreen) {
    mainScreen.classList.remove("screen-hidden");
  }
}
function initBadgeSystem() {
  renderBadgeGallery();

  const showBadgesBtn = document.getElementById("show-badges-btn");
  const backToMainBtn = document.getElementById("back-to-main-btn");

  if (showBadgesBtn) {
    showBadgesBtn.addEventListener("click", () => {
      showBadgeScreen();
    });
  }

  if (backToMainBtn) {
    backToMainBtn.addEventListener("click", () => {
      showMainScreen();
    });
  }
}

window.BiteRouteBadges = {
  init: initBadgeSystem,
  renderBadgeGallery,
  unlockBadge,
  completeCurrentRoute,
  setCurrentRouteFromResponse,
  getUnlockedBadges,
  resetBadgesForDemo,
  showBadgeScreen,
  showMainScreen
};

document.addEventListener("DOMContentLoaded", initBadgeSystem);