import test from "node:test";
import assert from "node:assert/strict";

import { applianceEnergy, calculatePlan, csvEscape, tieredCost } from "../src/calculations.js";

test("cihazın aktif ve bekleme tüketimini ayrı hesaplar", () => {
  const result = applianceEnergy({ watts: 100, quantity: 2, hours: 5, plannedHours: 4, days: 30, standbyWatts: 2 });
  assert.equal(result.activeKwh, 30);
  assert.equal(result.standbyKwh, 2.28);
  assert.equal(result.totalKwh, 32.28);
});

test("iki kademeli maliyeti eşikte böler", () => {
  const result = tieredCost(250, { thresholdKwh: 200, lowPrice: 2, highPrice: 3, extraPercent: 10 });
  assert.deepEqual(result, { lowKwh: 200, highKwh: 50, energyCost: 550, extras: 55, totalCost: 605 });
});

test("planlanan kullanım tasarrufu doğru verir", () => {
  const result = calculatePlan(
    [{ name: "Isıtıcı", watts: 1000, quantity: 1, hours: 4, plannedHours: 2, days: 30, standbyWatts: 0 }],
    { thresholdKwh: 100, lowPrice: 2, highPrice: 4, extraPercent: 0 },
  );
  assert.equal(result.currentKwh, 120);
  assert.equal(result.plannedKwh, 60);
  assert.equal(result.currentBill.totalCost, 280);
  assert.equal(result.plannedBill.totalCost, 120);
  assert.equal(result.savingsCost, 160);
});

test("virgül ve tırnak içeren CSV hücresini güvenli yazar", () => {
  assert.equal(csvEscape('TV, 55"'), '"TV, 55"""');
});

test("hesap tablosu formülü gibi başlayan CSV hücresini etkisizleştirir", () => {
  assert.equal(csvEscape("=2+2"), "'=2+2");
});

test("24 saatten uzun günlük kullanımı reddeder", () => {
  assert.throws(() => applianceEnergy({ watts: 10, quantity: 1, hours: 25, days: 1 }), RangeError);
});
