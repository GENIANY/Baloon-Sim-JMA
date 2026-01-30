from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .run_locator import GsmRun, GridDeg


@dataclass(frozen=True)
class RawStore:
    root: Path

    def raw_dir(self) -> Path:
        return self.root / "raw"

    def raw_dir_hr(self) -> Path:
        return self.raw_dir() / "jma_gsm_hr"

    def raw_dir_open(self) -> Path:
        return self.raw_dir() / "jma_gsm_open"

    # Closed (HR)
    def path_for_upper_air_global_hr(self, grid_deg: GridDeg, run: GsmRun, filename: str) -> Path:
        return self.raw_dir_hr() / f"grid_{grid_deg}" / "global" / run.date_yyyymmdd / run.cycle_dir / filename

    # Open (1.25)
    def path_for_open_gsm_1p25_upper_air(self, run: GsmRun, filename: str) -> Path:
        return self.raw_dir_open() / "gsm_1p25" / "upper_air_global" / run.date_yyyymmdd / run.cycle_dir / filename
