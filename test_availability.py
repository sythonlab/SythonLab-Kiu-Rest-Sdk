import datetime

import sythonlab_kiu_rest_sdk.settings  # noqa: F401 (loads .env and the debug logging for this script)
from sythonlab_kiu_rest_sdk.flights.v1.dataclasses import FlightAvailabilityItinerary, FlightAvailabilityPassenger
from sythonlab_kiu_rest_sdk.flights.v1.enums import PassengerType
from sythonlab_kiu_rest_sdk.flights.v1.sdk import KiuFlightSDK

sdk = KiuFlightSDK(debug=True)

status, data = sdk.get_availability(
    itinerary=[
        FlightAvailabilityItinerary(
            date=datetime.date.today() + datetime.timedelta(days=30),
            departing_iata_code="AEP",
            arrival_iata_code="COR"
        ),
    ],
    passengers=[
        FlightAvailabilityPassenger(kind=PassengerType.ADULT, qty=1),
    ]
)

print(status, data)
