import datetime

import sythonlab_kiu_rest_sdk.settings  # noqa: F401 (loads .env and the debug logging for this script)
from sythonlab_kiu_rest_sdk.flights.v1.dataclasses import FlightAvailabilityItinerary, FlightAvailabilityPassenger, \
    FlightQuoteSegment
from sythonlab_kiu_rest_sdk.flights.v1.enums import PassengerType
from sythonlab_kiu_rest_sdk.flights.v1.sdk import KiuFlightSDK

sdk = KiuFlightSDK(debug=True)
passengers = [FlightAvailabilityPassenger(kind=PassengerType.ADULT, qty=1)]
departure = datetime.date.today() + datetime.timedelta(days=30)

# The flights to quote come from the availability: the first XX one of each leg with seats in Y
status, availability = sdk.get_availability(
    itinerary=[
        FlightAvailabilityItinerary(date=departure, departing_iata_code="AEP", arrival_iata_code="COR"),
        FlightAvailabilityItinerary(date=departure + datetime.timedelta(days=5), departing_iata_code="COR",
                                    arrival_iata_code="AEP"),
    ],
    passengers=passengers,
)


def first_flight(leg_key):
    for option in availability[leg_key].values():
        flights = [flight for name, flight in option.items() if name.startswith("FL")]
        if len(flights) == 1 and flights[0]["carrier_reference_id"] == "00XX_0" and "Y9" in flights[0]["flight_rbd"]:
            return flights[0]


segments = []
legs = sorted(key for key in availability if key.startswith("OD_"))
for number, leg_key in enumerate(legs, start=1):
    flight = first_flight(leg_key)
    segments.append(FlightQuoteSegment(
        origin_destination=number,
        segment_number=number,
        carrier_code="XX",
        flight_number=flight["flight_number"],
        departing_iata_code=flight["departure_information"]["airport_reference_id"].split("_")[0],
        arrival_iata_code=flight["arrival_information"]["airport_reference_id"].split("_")[0],
        departure=datetime.datetime.strptime(
            f'{flight["departure_information"]["date"]} {flight["departure_information"]["time"]}', "%Y-%m-%d %H:%M:%S"),
        arrival=datetime.datetime.strptime(
            f'{flight["arrival_information"]["date"]} {flight["arrival_information"]["time"]}', "%Y-%m-%d %H:%M:%S"),
        rbds=["Y"],
    ))

status, data = sdk.itinerary_quote(segments=segments, passengers=passengers)

print(status, data)
