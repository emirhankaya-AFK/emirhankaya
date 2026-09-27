const preset = document.querySelector("#preset");
const runButton = document.querySelector("#run");

runButton.addEventListener("click", runStudy);
runStudy();

async function runStudy() {
  runButton.disabled = true;
  const response = await fetch(`/presets/${preset.value}`);
  const data = await response.json();
  render(data);
  runButton.disabled = false;
}

function render({ study, result }) {
  const longest = Math.max(...result.relay_results.map(item => item.operating_time_s || 0));
  document.querySelector("#status").textContent = result.all_coordinated ? "Coordinated" : "Review needed";
  document.querySelector("#status").className = result.all_coordinated ? "pass" : "fail";
  document.querySelector("#required").textContent = `${study.required_margin_s.toFixed(2)} s`;
  document.querySelector("#count").textContent = result.relay_results.length;

  document.querySelector("#timeline").innerHTML = result.relay_results.map(relay => {
    const width = relay.operating_time_s ? Math.max(2, relay.operating_time_s / longest * 100) : 0;
    return `<div class="relay"><span>${relay.name} · ${relay.location}</span>
      <div class="track"><div class="bar" style="width:${width}%"></div></div>
      <strong>${relay.operating_time_s === null ? "No trip" : `${relay.operating_time_s.toFixed(3)} s`}</strong></div>`;
  }).join("");

  document.querySelector("#pairs").innerHTML = result.coordination_pairs.map(pair => `
    <tr><td>${pair.downstream} → ${pair.upstream}</td>
    <td>${pair.margin_s === null ? "—" : `${pair.margin_s.toFixed(3)} s`}</td>
    <td class="${pair.coordinated ? "pass" : "fail"}">${pair.coordinated ? "PASS" : "FAIL"}</td>
    <td>${pair.note}</td></tr>`).join("");
}
