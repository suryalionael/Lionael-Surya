// FloodCast Jakarta — Demo Dashboard
// Connects to Azure Function API if configured, otherwise uses local JSON.

const CONFIG = {
  // Azure Function URL — set this to your deployed function endpoint
  apiBaseUrl: window.localStorage.getItem("floodcast_api") || "",
  predictionsFile: "data/predictions.json",
};

const RISK_COLORS = {
  Aman: "#34d399",
  Waspada: "#fbbf24",
  Siaga: "#fb923c",
  Awas: "#ef4444",
};

let state = {
  horizon: 24,
  selectedKelurahan: null,
  selectedAudience: "warga",
  predictions: null,
  map: null,
  markers: [],
};

// =========================================================
// Data loading
// =========================================================

async function loadPredictions() {
  // Try Azure Function first
  if (CONFIG.apiBaseUrl) {
    try {
      const res = await fetch(`${CONFIG.apiBaseUrl}/api/predict?all=true&horizon=${state.horizon}`);
      if (res.ok) {
        const data = await res.json();
        document.getElementById("apiStatus").className = "api-status online";
        document.getElementById("apiStatus").textContent = "API LIVE";
        return data;
      }
    } catch (e) {
      console.warn("API not reachable, falling back to local data", e);
    }
  }

  // Fallback to local JSON
  const res = await fetch(CONFIG.predictionsFile);
  return await res.json();
}

async function fetchAdvisory(kelurahan, audience) {
  const pred = state.predictions.kelurahan.find(k => k.name === kelurahan);
  if (!pred) return "Data tidak tersedia.";

  const horizonKey = `${state.horizon}h`;
  const probData = pred.predictions[horizonKey];

  const payload = {
    kelurahan: pred.name,
    probability: probData.probability,
    horizon_hours: state.horizon,
    risk_level: probData.risk_level,
    top_factors: pred.top_factors,
    audience,
  };

  if (CONFIG.apiBaseUrl) {
    try {
      const res = await fetch(`${CONFIG.apiBaseUrl}/api/advisory`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        const data = await res.json();
        return data.message;
      }
    } catch (e) {
      console.warn("Advisory API failed, using fallback", e);
    }
  }

  return generateFallbackAdvisory(pred, audience, probData);
}

function generateFallbackAdvisory(kelurahan, audience, probData) {
  const prob = probData.probability * 100;
  const risk = probData.risk_level;
  const horizon = state.horizon;
  const name = kelurahan.name;

  if (audience === "warga") {
    if (risk === "Awas" || risk === "Siaga") {
      return `Wilayah ${name} berisiko TINGGI banjir (${prob.toFixed(0)}%) dalam ${horizon} jam ke depan. Segera pindahkan kendaraan ke tempat tinggi, siapkan tas darurat berisi dokumen penting dan obat-obatan, dan pantau ketinggian air pintu air Manggarai. Jika air mulai naik di sekitar rumah, segera evakuasi ke titik aman terdekat.`;
    } else if (risk === "Waspada") {
      return `Wilayah ${name} dalam status WASPADA banjir (${prob.toFixed(0)}%) dalam ${horizon} jam ke depan. Pantau perkembangan cuaca dan ketinggian air Katulangan, siapkan rencana evakuasi keluarga, dan simpan barang berharga di tempat yang lebih tinggi.`;
    } else {
      return `Wilayah ${name} dalam status AMAN (${prob.toFixed(0)}% risiko) untuk ${horizon} jam ke depan. Tetap pantau update cuaca berkala.`;
    }
  } else if (audience === "bpbd") {
    return `PRIORITAS ${risk.toUpperCase()}: ${name} (${kelurahan.kecamatan}), probabilitas banjir ${prob.toFixed(0)}% dalam ${horizon} jam. Estimasi populasi terdampak: ${kelurahan.population.toLocaleString("id-ID")} jiwa. Rekomendasi: pre-positioning 2 perahu karet di pos siaga terdekat, koordinasi dengan kelurahan untuk identifikasi lansia/disabilitas yang perlu evakuasi dini, siapkan posko logistik dengan kapasitas ${Math.round(kelurahan.population * 0.05)} jiwa. Window aksi: ${Math.max(2, horizon - 4)} jam ke depan.`;
  } else {
    const topFactor = kelurahan.top_factors[0];
    return `Analisis ${name}: probabilitas banjir ${prob.toFixed(0)}% horizon ${horizon}h didorong terutama oleh ${topFactor.feature.replace(/_/g, " ")} (kontribusi ${(topFactor.importance * 100).toFixed(0)}%). Pola ini konsisten dengan kelurahan elevasi rendah (${kelurahan.elevation_m}m) di koridor Ciliwung dengan tutupan kedap air tinggi. Implikasi: prioritas program RTH dan normalisasi drainase di wilayah ini untuk mitigasi struktural jangka panjang.`;
  }
}

// =========================================================
// Map rendering (Leaflet.js — no API key required)
// =========================================================

function initMap() {
  state.map = L.map("map", { zoomControl: true }).setView([-6.2500, 106.8550], 12);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 18,
  }).addTo(state.map);

  renderMap();
}

function renderMap() {
  if (!state.predictions || !state.map) return;

  // Remove existing markers
  state.markers.forEach(m => m.remove());
  state.markers = [];

  state.predictions.kelurahan.forEach(k => {
    const horizonKey = `${state.horizon}h`;
    const pred = k.predictions[horizonKey];
    const color = RISK_COLORS[pred.risk_level];
    // Radius scales with probability: 10px (Aman) → 30px (Awas)
    const radius = 10 + pred.probability * 20;

    const marker = L.circleMarker([k.lat, k.lon], {
      radius,
      fillColor: color,
      color: "#ffffff",
      weight: 2,
      opacity: 1,
      fillOpacity: 0.85,
    }).addTo(state.map);

    marker.bindTooltip(
      `<strong>${k.name}</strong><br>${(pred.probability * 100).toFixed(0)}% — ${pred.risk_level}`,
      { direction: "top", sticky: false }
    );
    marker.on("click", () => selectKelurahan(k.name));
    state.markers.push(marker);
  });
}

// =========================================================
// UI rendering
// =========================================================

function renderSidebar() {
  const horizonKey = `${state.horizon}h`;
  const sorted = [...state.predictions.kelurahan].sort(
    (a, b) => b.predictions[horizonKey].probability - a.predictions[horizonKey].probability
  );

  // Stats
  const awasCount = sorted.filter(k =>
    ["Siaga", "Awas"].includes(k.predictions[horizonKey].risk_level)
  ).length;
  const totalAffected = sorted
    .filter(k => ["Siaga", "Awas"].includes(k.predictions[horizonKey].risk_level))
    .reduce((sum, k) => sum + k.population, 0);

  document.getElementById("statAwas").textContent = awasCount;
  document.getElementById("statTerdampak").textContent = totalAffected.toLocaleString("id-ID");

  // List
  const listEl = document.getElementById("kelurahanList");
  listEl.innerHTML = "";
  sorted.forEach(k => {
    const pred = k.predictions[horizonKey];
    const card = document.createElement("div");
    card.className = "kelurahan-card";
    if (k.name === state.selectedKelurahan) card.classList.add("selected");
    card.innerHTML = `
      <div class="top-row">
        <span class="name">${k.name}</span>
        <span class="prob" style="color: ${RISK_COLORS[pred.risk_level]};">
          ${(pred.probability * 100).toFixed(0)}%
        </span>
      </div>
      <div class="meta">
        <span class="risk-pill" style="background: ${RISK_COLORS[pred.risk_level]};">
          ${pred.risk_level}
        </span>
        ${k.kecamatan} • ${k.population.toLocaleString("id-ID")} jiwa
      </div>
    `;
    card.addEventListener("click", () => selectKelurahan(k.name));
    listEl.appendChild(card);
  });
}

async function selectKelurahan(name) {
  state.selectedKelurahan = name;
  const k = state.predictions.kelurahan.find(x => x.name === name);
  if (!k) return;

  const horizonKey = `${state.horizon}h`;
  const pred = k.predictions[horizonKey];
  const color = RISK_COLORS[pred.risk_level];

  // Pan map to selected kelurahan
  if (state.map) {
    state.map.setView([k.lat, k.lon], 14);
  }

  // Detail panel
  document.getElementById("detailPanel").classList.add("visible");
  document.getElementById("detailName").textContent = k.name;
  document.getElementById("detailKecamatan").textContent =
    `${k.kecamatan} • Elevasi ${k.elevation_m}m • ${k.population.toLocaleString("id-ID")} jiwa`;
  document.getElementById("detailProb").textContent = `${(pred.probability * 100).toFixed(0)}%`;
  document.getElementById("detailProb").style.color = color;

  const pill = document.getElementById("detailRisk");
  pill.textContent = pred.risk_level;
  pill.style.background = color;

  document.getElementById("detailProbBar").style.width = `${pred.probability * 100}%`;
  document.getElementById("detailProbBar").style.background = color;

  // Factors
  const factorsEl = document.getElementById("detailFactors");
  factorsEl.innerHTML = "";
  k.top_factors.forEach(f => {
    const div = document.createElement("div");
    div.className = "factor-item";
    const arrow = f.direction === "up" ? "↑" : "↓";
    const arrowColor = f.direction === "up" ? "var(--awas)" : "var(--aman)";
    div.innerHTML = `
      <span class="factor-name">${f.feature.replace(/_/g, " ")} <span style="color: ${arrowColor};">${arrow}</span></span>
      <span>${typeof f.value === "number" ? f.value.toFixed(1) : (f.importance * 100).toFixed(0) + "%"}</span>
    `;
    factorsEl.appendChild(div);
  });

  // Advisory
  await renderAdvisory();

  // Re-render sidebar to update selection highlight
  renderSidebar();
}

async function renderAdvisory() {
  if (!state.selectedKelurahan) return;
  const adv = document.getElementById("detailAdvisory");
  adv.innerHTML = '<span class="advisory-loading">Generating advisory...</span>';
  const message = await fetchAdvisory(state.selectedKelurahan, state.selectedAudience);
  adv.textContent = message;
}

// =========================================================
// Event handlers
// =========================================================

function setupEventHandlers() {
  document.querySelectorAll(".horizon-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".horizon-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      state.horizon = parseInt(btn.dataset.horizon);
      renderMap();
      renderSidebar();
      if (state.selectedKelurahan) selectKelurahan(state.selectedKelurahan);
    });
  });

  document.querySelectorAll(".audience-tab").forEach(btn => {
    btn.addEventListener("click", async () => {
      document.querySelectorAll(".audience-tab").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      state.selectedAudience = btn.dataset.audience;
      await renderAdvisory();
    });
  });

  document.getElementById("closeBtn").addEventListener("click", () => {
    document.getElementById("detailPanel").classList.remove("visible");
    state.selectedKelurahan = null;
    renderSidebar();
  });
}

// =========================================================
// Boot
// =========================================================

async function boot() {
  state.predictions = await loadPredictions();

  // Update API status badge
  if (!CONFIG.apiBaseUrl) {
    document.getElementById("apiStatus").className = "api-status demo";
    document.getElementById("apiStatus").textContent = "DEMO DATA";
  }

  setupEventHandlers();
  renderSidebar();
  initMap();

  // Auto-select highest risk kelurahan
  const horizonKey = `${state.horizon}h`;
  const top = [...state.predictions.kelurahan].sort(
    (a, b) => b.predictions[horizonKey].probability - a.predictions[horizonKey].probability
  )[0];
  if (top) selectKelurahan(top.name);
}

boot();
