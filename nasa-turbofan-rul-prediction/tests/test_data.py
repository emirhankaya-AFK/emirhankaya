import pandas as pd

from turbofan_rul.data import add_training_rul


def test_capped_rul_is_computed_inside_each_engine():
    frame = pd.DataFrame({"engine_id": [1, 1, 1, 2, 2], "cycle": [1, 2, 3, 1, 2]})
    assert add_training_rul(frame, cap=1)["rul"].tolist() == [1, 1, 0, 1, 0]
