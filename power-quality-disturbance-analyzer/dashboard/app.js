const presetMap = {
  sag: "voltage_sag",
  swell: "voltage_swell",
  interruption: "interruption",
  harmonics: "harmonic_distortion",
  unbalance: "phase_unbalance",
  clean: "nominal",
};

const colors = ["#ef4444", "#eab308", "#38bdf8"];

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("btn-run").addEventListener("click", runAnalysis);
  runAnalysis();
});

async function runAnalysis() {
  const button = document.getElementById("btn-run");
  const selected = document.getElementById("preset-select").value;
  const disturbance = presetMap[selected] || "nominal";
  button.disabled = true;
  button.textContent = "Analyzing DSP Pipeline...";

  try {
    const response = await fetch(`/demo/${disturbance}/waveform`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    renderDashboard(await response.json());
  } catch (error) {
    document.getElementById("events-table-body").innerHTML =
      `<tr><td colspan="7">Analysis failed: ${error.message}</td></tr>`;
  } finally {
    button.disabled = false;
    button.textContent = "Run DSP Analysis";
  }
}

function renderDashboard(data) {
  const result = data.result;
  const phases = [result.phase_a, result.phase_b, result.phase_c];
  document.getElementById("kpi-events").textContent = result.detections.length;
  document.getElementById("kpi-thd").textContent = `${Math.max(...phases.map(p => p.thd_percent)).toFixed(2)}%`;
  document.getElementById("kpi-vuf").textContent = `${result.voltage_unbalance_percent.toFixed(2)}%`;
  document.getElementById("kpi-v1").textContent = `${(phases.reduce((sum, p) => sum + p.rms_v, 0) / 3).toFixed(1)} V`;

  Plotly.react("plot-waveform", ["voltage_a", "voltage_b", "voltage_c"].map((key, index) => ({
    x: data.time_s, y: data[key], name: `Phase ${"ABC"[index]}`, type: "scatter",
    mode: "lines", line: { color: colors[index], width: 1.2 },
  })), plotLayout("Instantaneous voltage", "Voltage (V)"), { responsive: true });

  Plotly.react("plot-rms", [{
    x: ["Phase A", "Phase B", "Phase C"], y: phases.map(p => p.rms_pu), type: "bar",
    marker: { color: colors },
  }], plotLayout("RMS per unit", "RMS (pu)"), { responsive: true });

  Plotly.react("plot-harmonics", [{
    x: ["Phase A", "Phase B", "Phase C"], y: phases.map(p => p.thd_percent), type: "bar",
    marker: { color: colors },
  }], plotLayout("Total harmonic distortion", "THD (%)"), { responsive: true });

  Plotly.react("plot-sequences", [{
    x: ["Voltage unbalance"], y: [result.voltage_unbalance_percent], type: "bar",
    marker: { color: "#818cf8" },
  }], plotLayout("Negative / positive sequence", "VUF (%)"), { responsive: true });

  const rows = result.detections.length ? result.detections : [{
    disturbance: "nominal", severity: "normal", evidence: "All metrics are within configured thresholds",
  }];
  document.getElementById("events-table-body").innerHTML = rows.map(event => `
    <tr><td><span class="event-badge">${event.disturbance}</span></td>
    <td>All</td><td>0.000s</td><td>${data.time_s.at(-1).toFixed(3)}s</td>
    <td>${(data.time_s.at(-1) * 1000).toFixed(1)} ms</td><td>${event.severity}</td>
    <td>${event.evidence}</td></tr>`).join("");
}

function plotLayout(title, yTitle) {
  return {
    title: { text: title, font: { color: "#e2e8f0", size: 14 } },
    paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(15,23,42,.6)",
    font: { color: "#94a3b8" }, margin: { l: 55, r: 20, t: 45, b: 45 },
    xaxis: { gridcolor: "#334155" }, yaxis: { title: yTitle, gridcolor: "#334155" },
  };
}
