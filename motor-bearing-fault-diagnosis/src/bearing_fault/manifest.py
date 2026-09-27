"""Official CWRU recording manifest used in the benchmark."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Recording:
    file_id: int
    label: str
    load_hp: int
    rpm: int

    @property
    def url(self) -> str:
        return f"https://engineering.case.edu/sites/default/files/{self.file_id}.mat"


RECORDINGS = [
    Recording(97, "normal", 0, 1797),
    Recording(98, "normal", 1, 1772),
    Recording(99, "normal", 2, 1750),
    Recording(100, "normal", 3, 1730),
    Recording(105, "inner_race", 0, 1797),
    Recording(106, "inner_race", 1, 1772),
    Recording(107, "inner_race", 2, 1750),
    Recording(108, "inner_race", 3, 1730),
    Recording(118, "ball", 0, 1797),
    Recording(119, "ball", 1, 1772),
    Recording(120, "ball", 2, 1750),
    Recording(121, "ball", 3, 1730),
    Recording(130, "outer_race", 0, 1797),
    Recording(131, "outer_race", 1, 1772),
    Recording(132, "outer_race", 2, 1750),
    Recording(133, "outer_race", 3, 1730),
]

LABELS = ["normal", "inner_race", "ball", "outer_race"]
SAMPLE_RATE_HZ = 12_000
