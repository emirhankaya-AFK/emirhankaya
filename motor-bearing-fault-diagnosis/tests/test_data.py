import numpy as np
import pytest

from bearing_fault.data import split_windows
from bearing_fault.manifest import RECORDINGS


def test_manifest_has_every_class_at_every_load():
    combinations = {(item.label, item.load_hp) for item in RECORDINGS}
    assert len(combinations) == 16


def test_non_overlapping_windows_do_not_share_samples():
    signal = np.arange(12)
    windows = split_windows(signal, window_size=4, stride=4)
    assert windows.tolist() == [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]]


def test_invalid_window_is_rejected():
    with pytest.raises(ValueError):
        split_windows(np.arange(3), window_size=4)
