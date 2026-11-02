import os
import json
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(
    prefix="/api",
    tags=["App Updates"]
)

VERSION_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app_version.json")

class AppVersionResponse(BaseModel):
    product_id: str = "sirfbill-printer"
    platform: str = "windows-x64"
    channel: str = "stable"
    version: str = "1.0.1"
    latest_version: str = "1.0.1"
    mandatory: bool = False
    is_mandatory: bool = False
    release_notes: str = ""
    package_url: str = "https://billbackend.naiyo24.com/downloads/SirfBill_Setup_1.0.1.exe"
    download_url: str = "https://billbackend.naiyo24.com/downloads/SirfBill_Setup_1.0.1.exe"
    sha256: str = ""
    signature_url: str = ""

DEFAULT_VERSION_DATA = {
    "product_id": "sirfbill-printer",
    "platform": "windows-x64",
    "channel": "stable",
    "version": "1.0.1",
    "latest_version": "1.0.1",
    "mandatory": False,
    "is_mandatory": False,
    "release_notes": "• Improved custom billing & history sync\n• Auto-naming invoice PDFs\n• Performance improvements",
    "package_url": "https://billbackend.naiyo24.com/downloads/SirfBill_Setup_1.0.1.exe",
    "download_url": "https://billbackend.naiyo24.com/downloads/SirfBill_Setup_1.0.1.exe",
    "sha256": "",
    "signature_url": ""
}

@router.get("/app-version", response_model=AppVersionResponse)
def get_app_version():
    """
    Returns the latest Windows app version information for auto-updater.
    Can be dynamically updated via app_version.json or defaults.
    """
    if os.path.exists(VERSION_CONFIG_PATH):
        try:
            with open(VERSION_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return AppVersionResponse(**data)
        except Exception:
            pass
            
    return AppVersionResponse(**DEFAULT_VERSION_DATA)
