from dataclasses import dataclass
from datetime import datetime, date

from typing import Any, List, Optional

from sythonlab_kiu_rest_sdk.flights.v1.enums import RequestMethod, FlightResultKind, PassengerType


@dataclass
class FlightRequestMetadata:
    """Dataclass for flight request metadata."""

    status: int
    request_id: str
    method: RequestMethod
    url: str
    headers: Any
    request: Any
    response: Any
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    kind: Optional[FlightResultKind] = None


@dataclass
class FlightAvailabilityItinerary:
    departing_iata_code: str
    arrival_iata_code: str
    date: date
    return_date: Optional[date] = None


@dataclass
class FlightAvailabilityPassenger:
    kind: PassengerType
    qty: int


@dataclass
class FlightQuoteSegment:
    """A flight to quote: origin_destination is its leg (1 outbound, 2 return), segment_number its order overall."""

    origin_destination: int
    segment_number: int
    carrier_code: str
    flight_number: str
    departing_iata_code: str
    arrival_iata_code: str
    departure: datetime
    arrival: datetime
    rbds: List[str]
    stop_over: int = 0


@dataclass
class BookingPassenger:
    """A passenger to book: reference_order relates them to the contact information (1, 2...)."""

    reference_order: int
    name: str
    surname: str
    gender: str
    foid_type: str
    foid_id: str
    kind: PassengerType


@dataclass
class BookingSegment:
    """A flight to book, in the order of the itinerary."""

    order: int
    carrier: str
    flight_number: str
    departing_iata_code: str
    arrival_iata_code: str
    departure: datetime
    rbd: str
    number_in_party: int


@dataclass
class BookingPhone:
    city_location_code: str
    phone_detail: str
    passenger_reference_order: int = 1
    contact_type: str = "H"
