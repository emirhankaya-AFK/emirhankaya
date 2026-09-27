import pandas as pd

from turbofan_rul.data import SENSORS
from turbofan_rul.features import build_features, last_cycle_rows


def test_features_do_not_mix_engines():
    rows = []
    for engine_id, base in [(1, 0.0), (2, 100.0)]:
        for cycle in range(1, 4):
            row = {
                "engine_id": engine_id,
                "cycle": cycle,
                "setting_1": 0,
                "setting_2": 0,
                "setting_3": 0,
            }
            row.update({sensor: base + cycle for sensor in SENSORS})
            rows.append(row)
    frame = pd.DataFrame(rows)
    features = build_features(frame, windows=(2,))
    assert features.loc[3, "sensor_2_mean_2"] == 101
    assert last_cycle_rows(frame).cycle.tolist() == [3, 3]
