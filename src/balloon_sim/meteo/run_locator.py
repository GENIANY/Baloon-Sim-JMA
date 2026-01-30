from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal


GridDeg = Literal["0.5", "0.25"]
Region = Literal["global", "ra2"]


_GLOBAL_REGION_BY_GRID: dict[GridDeg, str] = {
    "0.5": "90.0_-90.0_0.0_359.5",
    "0.25": "90.0_-90.0_0.0_359.75",
}

_RA2_REGION: str = "90.0_-5.0_30.0_195.0"


def grid_dir(grid_deg: GridDeg) -> str:
    if grid_deg == "0.5":
        return "0.5_0.5"
    if grid_deg == "0.25":
        return "0.25_0.25"
    raise ValueError(f"Unsupported grid_deg: {grid_deg}")


def region_dir(grid_deg: GridDeg, region: Region) -> str:
    if region == "global":
        return _GLOBAL_REGION_BY_GRID[grid_deg]
    if region == "ra2":
        return _RA2_REGION
    raise ValueError(f"Unsupported region: {region}")


@dataclass(frozen=True)
class GsmRun:
    """Represents a GSM initial time (UTC)."""

    date_yyyymmdd: str  # e.g. "20260130"
    cycle_hh: str       # "00" / "06" / "12" / "18"

    @property
    def cycle_dir(self) -> str:
        # HH0000 format (6 digits, e.g. 000000 / 120000)
        return f"{self.cycle_hh}0000"

    @property
    def run_id(self) -> str:
        return f"{self.date_yyyymmdd}{self.cycle_hh}"

    @property
    def init_stamp(self) -> str:
        # yyyymmdd + hh0000  (8 + 6 = 14 digits)
        return f"{self.date_yyyymmdd}{self.cycle_dir}"

    @staticmethod
    def from_datetime(dt_utc: datetime) -> "GsmRun":
        if dt_utc.tzinfo is None:
            raise ValueError("dt_utc must be timezone-aware (UTC).")
        dt_utc = dt_utc.astimezone(timezone.utc)
        return GsmRun(dt_utc.strftime("%Y%m%d"), dt_utc.strftime("%H"))


def iter_recent_cycles(now_utc: datetime, n: int = 12) -> list[GsmRun]:
    if now_utc.tzinfo is None:
        raise ValueError("now_utc must be timezone-aware (UTC).")
    now_utc = now_utc.astimezone(timezone.utc)
    hh = (now_utc.hour // 6) * 6
    base = now_utc.replace(hour=hh, minute=0, second=0, microsecond=0)

    runs: list[GsmRun] = []
    for i in range(n):
        dt = base - timedelta(hours=6 * i)
        runs.append(GsmRun.from_datetime(dt))
    return runs


def fd_code(forecast_hours: int) -> str:
    if forecast_hours < 0:
        raise ValueError("forecast_hours must be >= 0")
    days = forecast_hours // 24
    hours = forecast_hours % 24
    if days > 99:
        raise ValueError("forecast_hours too large for FDddhh format")
    return f"FD{days:02d}{hours:02d}"


# -----------------------------
# Closed (High-Resolution) URL builder
# -----------------------------
def build_upper_air_global_url(
    base_url: str,
    grid_deg: GridDeg,
    run: GsmRun,
    forecast_hours: int,
) -> str:
    grid = grid_dir(grid_deg)
    region = region_dir(grid_deg, "global")
    layer = "Upper_air_layers"
    fd = fd_code(forecast_hours)

    if grid_deg == "0.5":
        fname = f"GSM_GPV_Rgl_Gll0p5deg_L-pall_{fd}_grib2.bin"
    else:
        fname = f"GSM_GPV_Rgl_Gll0p25deg_L-pall_{fd}_grib2.bin"

    return "/".join([base_url.rstrip("/"), grid, region, layer, run.date_yyyymmdd, run.cycle_dir, fname])


# -----------------------------
# Open (1.25 deg) URL builder
# -----------------------------
def build_open_gsm_1p25_upper_air_url(
    open_grib_base_url: str,
    run: GsmRun,
    fd_range: str = "FD0000-0512",
) -> str:
    """
    Open deterministic global GSM (1.25 deg) upper-air file.

    Directory and filename pattern are described in WIS Portal news (2019-05-09):
      /d/o/RJTD/GRIB/Global_Spectral_Model/Latitude_Longitude/1.25_1.25/
        90.0_-90.0_0.0_358.75/Upper_air_layers/YYYYMMDD/HH0000/
        W_jp-JMA-tokyo,MODEL,JMA+gsm+gpv,C_RJTD_yyyymmddhh0000_GSM_GPV_Rgl_Gll1p25deg_L-all_FD0000-0512_grib2.bin
    """
    subdir = "Global_Spectral_Model/Latitude_Longitude/1.25_1.25/90.0_-90.0_0.0_358.75/Upper_air_layers"
    fname = (
        f"W_jp-JMA-tokyo,MODEL,JMA+gsm+gpv,C_RJTD_{run.init_stamp}_"
        f"GSM_GPV_Rgl_Gll1p25deg_L-all_{fd_range}_grib2.bin"
    )
    return "/".join([open_grib_base_url.rstrip("/"), subdir, run.date_yyyymmdd, run.cycle_dir, fname])
