from .user import UserQuery
from .doctor import DoctorQuery
from .lab_catalog import LabCatalogQuery
from .appointment import AppointmentQuery
from .lab_booking import LabBookingQuery
from .story import StoryQuery
from .universal_search import UniversalSearchQuery
from .banner import BannerQuery
from .settings import SettingsQuery
from .shop_query import ShopQuery

__all__ = [
    "UserQuery",
    "DoctorQuery",
    "LabCatalogQuery",
    "AppointmentQuery",
    "LabBookingQuery",
    "StoryQuery",
    "UniversalSearchQuery",
    "BannerQuery",
    "SettingsQuery",
    "ShopQuery"
]
