from __future__ import annotations

import base64
import shutil
import urllib.request
import urllib.error
from dataclasses import dataclass
from pathlib import Path


class DownloadError(RuntimeError):
    pass


@dataclass(frozen=True)
class Auth:
    user: str
    password: str


def _make_request(url: str, auth: Auth | None) -> urllib.request.Request:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "balloon-sim-jma/0.0.0 (+https://github.com/GENIANY/Baloon-Sim-JMA)"},
        method="GET",
    )
    if auth is not None:
        token = base64.b64encode(f"{auth.user}:{auth.password}".encode("utf-8")).decode("ascii")
        req.add_header("Authorization", f"Basic {token}")
    return req


def download_to(
    url: str,
    dst: Path,
    auth: Auth | None = None,
    overwrite: bool = False,
    timeout_sec: int = 300,  # bigger default for 100MB+ files
) -> Path:
    dst.parent.mkdir(parents=True, exist_ok=True)

    if dst.exists() and not overwrite and dst.stat().st_size > 0:
        return dst

    req = _make_request(url, auth)

    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            status = getattr(resp, "status", 200)
            if status != 200:
                raise DownloadError(f"HTTP {status} for {url}")

            tmp = dst.with_suffix(dst.suffix + ".part")
            with open(tmp, "wb") as f:
                shutil.copyfileobj(resp, f)
            tmp.replace(dst)
            return dst

    except urllib.error.HTTPError as e:
        raise DownloadError(f"HTTP {e.code} {e.reason}: {url}") from e
    except Exception as e:
        raise DownloadError(f"Failed to download: {url} -> {dst}. Reason: {e}") from e
