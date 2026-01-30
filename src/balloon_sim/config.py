from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class AppConfig:
    """
    App-wide configuration.

    Notes:
    - High-Resolution GSM (0.5/0.25) is under "Closed" directory and may require registration.
      Tutorial mentions /d/c/ and subscription with "Closed".
    - Open global deterministic GRIB (1.25 deg) is available under /d/o/RJTD/GRIB/
      (see WIS Portal news for file naming).
    """

    data_dir: Path = Path(os.environ.get("BALLOON_SIM_DATA_DIR", "data"))

    # Closed (may require auth)
    jma_hr_gsm_base_url: str = os.environ.get(
        "JMA_HR_GSM_BASE_URL",
        # backward-compat: if you used old name, keep working
        os.environ.get(
            "JMA_GSM_BASE_URL",
            "https://www.wis-jma.go.jp/d/c/RJTD/GRIB/Global_Spectral_Model/Latitude_Longitude/",
        ),
    )

    # Open (no auth needed)
    jma_open_grib_base_url: str = os.environ.get(
        "JMA_OPEN_GRIB_BASE_URL",
        "https://www.wis-jma.go.jp/d/o/RJTD/GRIB/",
    )

    # Optional auth (only for Closed)
    jma_user: str | None = os.environ.get("JMA_WIS_USER")
    jma_password: str | None = os.environ.get("JMA_WIS_PASSWORD")
