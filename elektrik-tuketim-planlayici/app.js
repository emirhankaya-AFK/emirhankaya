import { calculatePlan, csvEscape } from "./src/calculations.js";

const STORAGE_KEY = "elektrik-planlayici-v1";
const defaultState = {
  schemaVersion: 1,
  tariff: { thresholdKwh: 0, lowPrice: 0, highPrice: 0, extraPercent: 0 },
  appliances: [
    { id: crypto.randomUUID(), name: "Buzdolabı", watts: 120, quantity: 1, hours: 8, plannedHours: 8, days: 30, standbyWatts: 0 },
    { id: crypto.randomUUID(), name: "Televizyon", watts: 100, quantity: 1, hours: 5, plannedHours: 3, days: 30, standbyWatts: 1 },
    { id: crypto.randomUUID(), name: "Çamaşır makinesi", watts: 2000, quantity: 1, hours: 1, plannedHours: 0.7, days: 12, standbyWatts: 0.5 },
  ],
};

let state = loadState();
const tableBody = document.querySelector("#appliances");
const rowTemplate = document.querySelector("#rowTemplate");
const tariffKeys = ["thresholdKwh", "lowPrice", "highPrice", "extraPercent"];

tariffKeys.forEach(key => {
  const input = document.querySelector(`#${key}`);
  input.value = state.tariff[key];
  input.addEventListener("input", () => {
    state.tariff[key] = input.value;
    persistAndRender();
  });
});

document.querySelector("#add").addEventListener("click", () => {
  state.appliances.push({ id: crypto.randomUUID(), name: "Yeni cihaz", watts: 100, quantity: 1, hours: 1, plannedHours: 1, days: 30, standbyWatts: 0 });
  renderRows();
  persistAndRender();
});

document.querySelector("#exportJson").addEventListener("click", () => download(
  "elektrik-plani.json",
  JSON.stringify(state, null, 2),
  "application/json",
));

document.querySelector("#importJson").addEventListener("change", async event => {
  const file = event.target.files[0];
  if (!file) return;
  try {
    const imported = JSON.parse(await file.text());
    if (
      imported.schemaVersion !== 1
      || !Array.isArray(imported.appliances)
      || typeof imported.tariff !== "object"
    ) throw new Error();
    state = imported;
    tariffKeys.forEach(key => { document.querySelector(`#${key}`).value = state.tariff[key]; });
    renderRows();
    persistAndRender();
  } catch {
    alert("Bu dosya geçerli bir Elektrik Tüketim Planlayıcı yedeği değil.");
  }
  event.target.value = "";
});

document.querySelector("#exportCsv").addEventListener("click", exportCsv);
document.querySelector("#reset").addEventListener("click", () => {
  if (!confirm("Tüm cihazları ve tarife bilgilerini sıfırlamak istiyor musunuz?")) return;
  localStorage.removeItem(STORAGE_KEY);
  state = structuredClone(defaultState);
  location.reload();
});

function loadState() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
    return saved?.appliances && saved?.tariff ? saved : structuredClone(defaultState);
  } catch {
    return structuredClone(defaultState);
  }
}

function renderRows() {
  tableBody.innerHTML = "";
  state.appliances.forEach(appliance => {
    const row = rowTemplate.content.firstElementChild.cloneNode(true);
    row.querySelectorAll("input").forEach(input => {
      const key = input.dataset.key;
      input.value = appliance[key];
      input.addEventListener("input", () => {
        appliance[key] = key === "name" ? input.value : input.value;
        persistAndRender();
      });
    });
    row.querySelector(".remove").addEventListener("click", () => {
      state.appliances = state.appliances.filter(item => item.id !== appliance.id);
      renderRows();
      persistAndRender();
    });
    tableBody.append(row);
  });
}

function persistAndRender() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  renderSummary();
}

function renderSummary() {
  try {
    const result = calculatePlan(state.appliances, state.tariff);
    document.querySelector("#currentKwh").textContent = `${format(result.currentKwh)} kWh`;
    document.querySelector("#currentCost").textContent = currency(result.currentBill.totalCost);
    document.querySelector("#saving").textContent = currency(result.savingsCost);
    document.querySelector("#savingKwh").textContent = `${format(result.savingsKwh)} kWh daha az`;
    const largest = Math.max(0, ...result.currentRows.map(item => item.totalKwh));
    document.querySelector("#breakdown").innerHTML = result.currentRows.length ? result.currentRows
      .sort((a, b) => b.totalKwh - a.totalKwh)
      .map(item => `<div class="breakdown-row"><strong>${escapeHtml(item.name)}</strong>
        <div class="bar-track"><div class="bar-fill" style="width:${largest ? item.totalKwh / largest * 100 : 0}%"></div></div>
        <span>${format(item.totalKwh)} kWh</span><span class="cost">${currency(item.estimatedCost)}</span></div>`).join("")
      : "<p>Hesaplama için en az bir cihaz ekleyin.</p>";
  } catch (error) {
    document.querySelector("#breakdown").innerHTML = `<p class="error">${escapeHtml(error.message)}</p>`;
  }
}

function exportCsv() {
  try {
    const result = calculatePlan(state.appliances, state.tariff);
    const rows = [["Cihaz", "Aktif kWh", "Bekleme kWh", "Toplam kWh", "Tahmini maliyet TL"]];
    result.currentRows.forEach(item => rows.push([
      item.name, item.activeKwh.toFixed(3), item.standbyKwh.toFixed(3), item.totalKwh.toFixed(3), item.estimatedCost.toFixed(2),
    ]));
    rows.push(["TOPLAM", "", "", result.currentKwh.toFixed(3), result.currentBill.totalCost.toFixed(2)]);
    download("elektrik-tuketim-raporu.csv", `\uFEFF${rows.map(row => row.map(csvEscape).join(";")).join("\n")}`, "text/csv;charset=utf-8");
  } catch (error) {
    alert(error.message);
  }
}

function download(filename, content, type) {
  const link = document.createElement("a");
  link.href = URL.createObjectURL(new Blob([content], { type }));
  link.download = filename;
  link.click();
  URL.revokeObjectURL(link.href);
}

function format(value) { return new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 2 }).format(value); }
function currency(value) { return new Intl.NumberFormat("tr-TR", { style: "currency", currency: "TRY" }).format(value); }
function escapeHtml(value) { const node = document.createElement("span"); node.textContent = value; return node.innerHTML; }

renderRows();
persistAndRender();
if ("serviceWorker" in navigator) navigator.serviceWorker.register("./sw.js");
