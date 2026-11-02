import strawberry
from graphql_api.queries import DoctorQuery, LabCatalogQuery, UserQuery, AppointmentQuery, LabBookingQuery, StoryQuery, UniversalSearchQuery, BannerQuery, SettingsQuery, ShopQuery
from graphql_api.mutations.base import Mutation
@strawberry.type
class Query(UserQuery, DoctorQuery, LabCatalogQuery, AppointmentQuery, LabBookingQuery, StoryQuery, UniversalSearchQuery, BannerQuery, SettingsQuery, ShopQuery):
    pass

schema = strawberry.Schema(query=Query, mutation=Mutation)
