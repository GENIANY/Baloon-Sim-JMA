from __future__ import annotations

from pathlib import Path
from typing import Any

import xarray as xr


def open_grib_any(path: Path) -> list[xr.Dataset]:
    """
    Try opening a GRIB2 file with cfgrib.

    cfgrib can split one GRIB file into multiple xarray.Datasets depending on keys.
    We return a list for robustness.
    """
    import cfgrib

    # cfgrib provides open_datasets() (note: xarray does NOT)
    dsets = cfgrib.open_datasets(str(path))
    if not dsets:
        # fallback (rare)
        ds = xr.open_dataset(str(path), engine="cfgrib")
        return [ds]
    return dsets


def summarize_datasets(dsets: list[xr.Dataset]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for i, ds in enumerate(dsets):
        out.append(
            {
                "index": i,
                "sizes": dict(ds.sizes),
                "coords": list(ds.coords),
                "data_vars": list(ds.data_vars),
            }
        )
    return out
