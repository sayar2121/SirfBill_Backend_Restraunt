import os
import json
import time
import urllib.request
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(
    prefix="/api",
    tags=["App Updates"]
)

VERSION_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app_version.json")
GITHUB_REPO = "sayar2121/SirfBill_Restraunt"

# In-memory cache for live GitHub version info (5 min TTL)
_cached_version_data = None
_cached_timestamp = 0
CACHE_TTL_SECONDS = 300


class AppVersionResponse(BaseModel):
    product_id: str = "sirfbill-restaurant"
    platform: str = "windows-x64"
    channel: str = "stable"
    version: str = "1.0.13"
    latest_version: str = "1.0.13"
    mandatory: bool = False
    is_mandatory: bool = False
    release_notes: str = ""
    package_url: str = ""
    download_url: str = ""
    sha256: str = ""
    signature_url: str = ""


def _fetch_live_github_version():
    global _cached_version_data, _cached_timestamp
    now = time.time()
    if _cached_version_data and (now - _cached_timestamp) < CACHE_TTL_SECONDS:
        return _cached_version_data

    # 1. Try reading manifest.json directly from GitHub latest release
    manifest_url = f"https://github.com/{GITHUB_REPO}/releases/latest/download/manifest.json"
    req = urllib.request.Request(manifest_url, headers={"User-Agent": "SirfBill-Backend-Updater"})
    try:
        with urllib.request.urlopen(req, timeout=4) as resp:
            if resp.status == 200:
                raw = resp.read().decode("utf-8")
                m = json.loads(raw)
                ver = (m.get("version") or "").strip()
                if ver:
                    data = {
                        "product_id": "sirfbill-restaurant",
                        "platform": "windows-x64",
                        "channel": "stable",
                        "version": ver,
                        "latest_version": ver,
                        "mandatory": bool(m.get("mandatory", False)),
                        "is_mandatory": bool(m.get("mandatory", False)),
                        "release_notes": m.get("release_notes", f"• SirfBill Restaurant Release v{ver}"),
                        "package_url": m.get("package_url") or f"https://github.com/{GITHUB_REPO}/releases/download/v{ver}/app-update.zip",
                        "download_url": f"https://github.com/{GITHUB_REPO}/releases/download/v{ver}/Sirfbill_Restaurant_Setup.exe",
                        "sha256": m.get("sha256", ""),
                        "signature_url": ""
                    }
                    _cached_version_data = data
                    _cached_timestamp = now
                    return data
    except Exception:
        pass

    # 2. Try GitHub Releases API
    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    req = urllib.request.Request(
        api_url,
        headers={"Accept": "application/vnd.github.v3+json", "User-Agent": "SirfBill-Backend-Updater"}
    )
    try:
        with urllib.request.urlopen(req, timeout=4) as resp:
            if resp.status == 200:
                release = json.loads(resp.read().decode("utf-8"))
                tag = (release.get("tag_name") or "").replace("v", "").strip()
                if tag:
                    assets = release.get("assets", [])
                    pkg_url = ""
                    setup_url = ""
                    for a in assets:
                        name = (a.get("name") or "").lower()
                        if name == "app-update.zip":
                            pkg_url = a.get("browser_download_url", "")
                        elif name.endswith(".exe"):
                            setup_url = a.get("browser_download_url", "")

                    data = {
                        "product_id": "sirfbill-restaurant",
                        "platform": "windows-x64",
                        "channel": "stable",
                        "version": tag,
                        "latest_version": tag,
                        "mandatory": False,
                        "is_mandatory": False,
                        "release_notes": release.get("body") or f"• SirfBill Restaurant Release v{tag}",
                        "package_url": pkg_url or f"https://github.com/{GITHUB_REPO}/releases/download/v{tag}/app-update.zip",
                        "download_url": setup_url or f"https://github.com/{GITHUB_REPO}/releases/download/v{tag}/Sirfbill_Restaurant_Setup.exe",
                        "sha256": "",
                        "signature_url": ""
                    }
                    _cached_version_data = data
                    _cached_timestamp = now
                    return data
    except Exception:
        pass

    return None


@router.get("/app-version", response_model=AppVersionResponse)
def get_app_version():
    """
    Returns latest Windows app version information for auto-updater.
    Priority:
    1. Dynamic live check from GitHub releases (auto-detects new builds without manual server edit)
    2. Local app_version.json file
    3. Safe fallback defaults
    """
    # 1. Live GitHub lookup with caching
    live_data = _fetch_live_github_version()
    if live_data:
        return AppVersionResponse(**live_data)

    # 2. Local app_version.json
    if os.path.exists(VERSION_CONFIG_PATH):
        try:
            with open(VERSION_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return AppVersionResponse(**data)
        except Exception:
            pass

    # 3. Fallback
    return AppVersionResponse(
        product_id="sirfbill-restaurant",
        platform="windows-x64",
        channel="stable",
        version="1.0.13",
        latest_version="1.0.13",
        release_notes="• SirfBill Restaurant Release v1.0.13\n• Performance and auto-update enhancements",
        package_url=f"https://github.com/{GITHUB_REPO}/releases/download/v1.0.13/app-update.zip",
        download_url=f"https://github.com/{GITHUB_REPO}/releases/download/v1.0.13/Sirfbill_Restaurant_Setup.exe"
    )
