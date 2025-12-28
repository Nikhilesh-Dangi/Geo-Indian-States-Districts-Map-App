function showBanner(msg) {
  let banner = document.getElementById("banner");
  if (!banner) {
    banner = document.createElement("div");
    banner.id = "banner";
    banner.className = "banner";
    document.body.appendChild(banner);
  }
  banner.textContent = msg;
}

if (!window.L) {
  showBanner("Map library failed to load. If you blocked CDN scripts, allow Leaflet or host it locally.");
}

const map = window.L
  ? L.map("map", {
      center: [22.5, 79],
      zoom: 5,
      minZoom: 3,
      worldCopyJump: true,
    })
  : null;

if (map) {
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>',
  }).addTo(map);
}

const layerSelect = document.getElementById("layer-select");
const searchInput = document.getElementById("search");
const downloadSelectedBtn = document.getElementById("download-selected");
const downloadFullBtn = document.getElementById("download-full");
const settingsBtn = document.getElementById("settings-btn");
const modal = document.getElementById("settings-modal");
const closeModalBtn = document.getElementById("close-modal");
const saveToGithubBtn = document.getElementById("save-to-github");

const GH_TOKEN_INPUT = document.getElementById("gh-token");
const GH_OWNER_INPUT = document.getElementById("gh-owner");
const GH_REPO_INPUT = document.getElementById("gh-repo");
const MODAL_STATUS = document.getElementById("modal-status");

let geojsonLayer = null;
let currentData = null;
let currentLayerKey = "states";
let selectedIds = new Set(JSON.parse(localStorage.getItem("selected-ids") || "[]"));

const layerConfig = {
  states: {
    path: "data/states.geojson",
    nameProp: "name",
  },
  districts: {
    path: "data/districts.geojson",
    nameProp: "district",
  },
};

// load persisted selections
function persistSelections() {
  localStorage.setItem("selected-ids", JSON.stringify(Array.from(selectedIds)));
  localStorage.setItem("selected-layer", currentLayerKey);
}

function restoreLayerPreference() {
  const savedLayer = localStorage.getItem("selected-layer");
  if (savedLayer && layerConfig[savedLayer]) {
    currentLayerKey = savedLayer;
    layerSelect.value = savedLayer;
  }
}

restoreLayerPreference();

function styleFeature(feature) {
  const id = feature.id || feature.properties.id || feature.properties.fid;
  const isSelected = selectedIds.has(`${currentLayerKey}:${id}`);
  return {
    color: isSelected ? "#ffb347" : "#6fb9ff",
    weight: isSelected ? 3 : 1,
    fillColor: isSelected ? "rgba(255, 179, 71, 0.4)" : "rgba(126, 224, 255, 0.25)",
    fillOpacity: 0.6,
  };
}

function onEachFeature(feature, layer) {
  const nameProp = layerConfig[currentLayerKey].nameProp;
  const name = feature.properties[nameProp] || feature.properties.name || "Unknown";
  const id = feature.id || feature.properties.id || feature.properties.fid || name;

  layer.bindTooltip(name, { sticky: true });

  layer.on({
    mouseover: () => layer.setStyle({ weight: 3, color: "#fff", fillOpacity: 0.7 }),
    mouseout: () => geojsonLayer.resetStyle(layer),
    click: () => {
      const key = `${currentLayerKey}:${id}`;
      if (selectedIds.has(key)) {
        selectedIds.delete(key);
      } else {
        selectedIds.add(key);
      }
      persistSelections();
      geojsonLayer.resetStyle(layer);
      updateHashFromSelections();
    },
  });
}

async function loadLayer(key) {
  currentLayerKey = key;
  persistSelections();
  if (!map) return;
  if (geojsonLayer) {
    geojsonLayer.remove();
  }
  const cfg = layerConfig[key];
  const candidateUrls = [
    new URL(cfg.path, window.location.href).toString(),
    `./${cfg.path}`,
    key === "states" ? "data/in.json" : "data/output.geojson",
  ];
  let res;
  try {
    let lastErr;
    for (const url of candidateUrls) {
      try {
        res = await fetch(url);
        if (res.ok) {
          currentData = await res.json();
          break;
        } else {
          lastErr = `Fetch failed ${res.status} for ${url}`;
        }
      } catch (e) {
        lastErr = e.message;
      }
    }
    if (!currentData) throw new Error(lastErr || "Unknown fetch error");
  } catch (err) {
    showBanner(`Failed to load dataset. ${err.message}`);
    return;
  }

  geojsonLayer = L.geoJSON(currentData, {
    style: styleFeature,
    onEachFeature,
  }).addTo(map);
  map.fitBounds(geojsonLayer.getBounds(), { padding: [10, 10] });
  applySearchFilter();
  updateHashFromSelections();
}

function applySearchFilter() {
  if (!geojsonLayer) return;
  const term = searchInput.value.trim().toLowerCase();
  geojsonLayer.eachLayer((layer) => {
    const name = layer.feature.properties[layerConfig[currentLayerKey].nameProp] || "";
    const matches = name.toLowerCase().includes(term);
    if (term && !matches) {
      layer.setStyle({ fillOpacity: 0.05, opacity: 0.2 });
    } else {
      geojsonLayer.resetStyle(layer);
    }
  });
}

function downloadBlob(filename, content) {
  const blob = new Blob([content], { type: "application/geo+json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function downloadFull() {
  if (!currentData) {
    showBanner("No dataset loaded yet.");
    return;
  }
  downloadBlob(`${currentLayerKey}.geojson`, JSON.stringify(currentData));
}

function downloadSelected() {
  if (!currentData) {
    showBanner("No dataset loaded yet.");
    return;
  }
  const selectedFeatures = currentData.features.filter((feature) => {
    const id =
      feature.id ||
      feature.properties.id ||
      feature.properties.fid ||
      feature.properties[layerConfig[currentLayerKey].nameProp];
    return selectedIds.has(`${currentLayerKey}:${id}`);
  });
  if (!selectedFeatures.length) {
    showBanner("No selections yet. Click features to select.");
    return;
  }
  const fc = { type: "FeatureCollection", features: selectedFeatures };
  downloadBlob(`${currentLayerKey}-selected.geojson`, JSON.stringify(fc));
}

// Optional GitHub save
async function saveSelectionToGithub() {
  const token = GH_TOKEN_INPUT.value.trim();
  const owner = GH_OWNER_INPUT.value.trim();
  const repo = GH_REPO_INPUT.value.trim();
  if (!token || !owner || !repo) {
    MODAL_STATUS.textContent = "Token, owner, and repo are required.";
    return;
  }

  MODAL_STATUS.textContent = "Preparing commit…";
  const path = "saved/user_selections.json";
  const selections = Array.from(selectedIds);
  const content = btoa(unescape(encodeURIComponent(JSON.stringify({
    layer: currentLayerKey,
    selections,
    updated: new Date().toISOString(),
  }, null, 2))));

  // get current sha (if file exists)
  let sha = undefined;
  try {
    const res = await fetch(`https://api.github.com/repos/${owner}/${repo}/contents/${path}`, {
      headers: { Authorization: `token ${token}` },
    });
    if (res.ok) {
      const data = await res.json();
      sha = data.sha;
    }
  } catch (e) {
    // ignore
  }

  const res = await fetch(`https://api.github.com/repos/${owner}/${repo}/contents/${path}`, {
    method: "PUT",
    headers: {
      Authorization: `token ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message: "Save selections from India Geo Explorer",
      content,
      sha,
    }),
  });

  if (!res.ok) {
    const msg = await res.text();
    MODAL_STATUS.textContent = `Failed: ${res.status} ${msg}`;
  } else {
    MODAL_STATUS.textContent = "Saved to GitHub.";
  }
}

function updateHashFromSelections() {
  const hash = new URLSearchParams();
  hash.set("layer", currentLayerKey);
  if (selectedIds.size) hash.set("sel", Array.from(selectedIds).join(","));
  location.hash = hash.toString();
}

function restoreFromHash() {
  const hash = location.hash.replace(/^#/, "");
  const params = new URLSearchParams(hash);
  const layer = params.get("layer");
  const sel = params.get("sel");
  if (layer && layerConfig[layer]) {
    currentLayerKey = layer;
    layerSelect.value = layer;
  }
  if (sel) {
    selectedIds = new Set(sel.split(","));
  }
}

// Event wiring
layerSelect.addEventListener("change", (e) => loadLayer(e.target.value));
searchInput.addEventListener("input", applySearchFilter);
downloadFullBtn.addEventListener("click", downloadFull);
downloadSelectedBtn.addEventListener("click", downloadSelected);

settingsBtn.addEventListener("click", () => modal.classList.remove("hidden"));
closeModalBtn.addEventListener("click", () => modal.classList.add("hidden"));
modal.addEventListener("click", (e) => {
  if (e.target === modal) modal.classList.add("hidden");
});
saveToGithubBtn.addEventListener("click", saveSelectionToGithub);

restoreFromHash();
loadLayer(currentLayerKey);
