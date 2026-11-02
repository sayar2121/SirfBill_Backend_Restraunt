import strawberry
from graphql_api.mutations.appointment_mutation import AppointmentMutation
# Import other domain mutations as you build them (e.g., LabBookingMutation, ShopMutation)

@strawberry.type
class Mutation(
    AppointmentMutation,
    # LabBookingMutation,
    # ShopMutation
):
    """
    Root Mutation class aggregating all domain-specific mutations.
    """
    pass
