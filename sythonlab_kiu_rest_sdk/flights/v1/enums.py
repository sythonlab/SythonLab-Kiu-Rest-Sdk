from enum import Enum


class RequestMethod(Enum):
    """Represents HTTP request methods."""

    POST = "POST"


class FlightResultKind(Enum):
    """Enum for the kind of flight result."""

    FLIGHT_SEARCH = "FLIGHT_SEARCH"
    FLIGHT_PRICING = "FLIGHT_PRICING"
    SHOPPING_LITE = "SHOPPING_LITE"
    ITINERARY_QUOTE = "ITINERARY_QUOTE"
    CREATE_BOOKING = "CREATE_BOOKING"
    ISSUE_TICKETS = "ISSUE_TICKETS"
    BOOKING_INFORMATION = "BOOKING_INFORMATION"
    VOID_DOCUMENTS = "VOID_DOCUMENTS"
    CANCEL_BOOKING = "CANCEL_BOOKING"


class PassengerType(Enum):
    """Represents the passengers types."""

    ADULT = "ADT"
    CHILD = "CNN"
    INFANT = "INF"
