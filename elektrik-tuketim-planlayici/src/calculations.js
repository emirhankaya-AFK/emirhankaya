export function validateNumber(value, { min = 0, max = Infinity, label = "Değer" } = {}) {
  const number = Number(value);
  if (!Number.isFinite(number) || number < min || number > max) {
    throw new RangeError(`${label} ${min}–${max} aralığında olmalı.`);
  }
  return number;
}

export function applianceEnergy(appliance, planned = false) {
  const watts = validateNumber(appliance.watts, { min: 0, max: 100000, label: "Güç" });
  const quantity = validateNumber(appliance.quantity, { min: 1, max: 1000, label: "Adet" });
  const hours = validateNumber(planned ? appliance.plannedHours : appliance.hours, {
    min: 0,
    max: 24,
    label: "Günlük kullanım",
  });
  const days = validateNumber(appliance.days, { min: 0, max: 31, label: "Aylık gün" });
  const standbyWatts = validateNumber(appliance.standbyWatts || 0, {
    min: 0,
    max: 10000,
    label: "Bekleme gücü",
  });
  const activeKwh = (watts * quantity * hours * days) / 1000;
  const standbyHours = Math.max(0, 24 - hours) * days;
  const standbyKwh = (standbyWatts * quantity * standbyHours) / 1000;
  return {
    activeKwh,
    standbyKwh,
    totalKwh: activeKwh + standbyKwh,
  };
}

export function tieredCost(kwh, tariff) {
  const energy = validateNumber(kwh, { min: 0, max: 1_000_000, label: "Tüketim" });
  const threshold = validateNumber(tariff.thresholdKwh, {
    min: 0,
    max: 1_000_000,
    label: "Kademe sınırı",
  });
  const lowPrice = validateNumber(tariff.lowPrice, { min: 0, max: 1000, label: "Alt kademe" });
  const highPrice = validateNumber(tariff.highPrice, {
    min: 0,
    max: 1000,
    label: "Üst kademe",
  });
  const extraPercent = validateNumber(tariff.extraPercent || 0, {
    min: 0,
    max: 1000,
    label: "Ek oran",
  });
  const lowKwh = Math.min(energy, threshold);
  const highKwh = Math.max(0, energy - threshold);
  const energyCost = lowKwh * lowPrice + highKwh * highPrice;
  const extras = energyCost * (extraPercent / 100);
  return { lowKwh, highKwh, energyCost, extras, totalCost: energyCost + extras };
}

export function calculatePlan(appliances, tariff) {
  const currentRows = appliances.map(item => ({ ...item, ...applianceEnergy(item, false) }));
  const plannedRows = appliances.map(item => ({ ...item, ...applianceEnergy(item, true) }));
  const currentKwh = currentRows.reduce((sum, item) => sum + item.totalKwh, 0);
  const plannedKwh = plannedRows.reduce((sum, item) => sum + item.totalKwh, 0);
  const currentBill = tieredCost(currentKwh, tariff);
  const plannedBill = tieredCost(plannedKwh, tariff);
  const blendedRate = currentKwh > 0 ? currentBill.totalCost / currentKwh : 0;
  return {
    currentRows: currentRows.map(item => ({ ...item, estimatedCost: item.totalKwh * blendedRate })),
    plannedRows,
    currentKwh,
    plannedKwh,
    currentBill,
    plannedBill,
    savingsKwh: Math.max(0, currentKwh - plannedKwh),
    savingsCost: Math.max(0, currentBill.totalCost - plannedBill.totalCost),
  };
}

export function csvEscape(value) {
  let text = String(value ?? "");
  if (/^[=+\-@]/.test(text)) text = `'${text}`;
  return /[";,\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}
