import logging
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Callable, List, Mapping
from uuid import uuid4

import requests

from sythonlab_kiu_rest_sdk.flights.v1.dataclasses import FlightRequestMetadata, FlightAvailabilityItinerary, \
    FlightAvailabilityPassenger, FlightQuoteSegment, BookingPassenger, BookingSegment, BookingPhone
from sythonlab_kiu_rest_sdk.flights.v1.enums import RequestMethod, FlightResultKind, PassengerType

logger = logging.getLogger(__name__)


class KiuFlightSDK:
    debug: bool = False
    url_base: Optional[str] = None
    api_token: str
    username: Optional[str] = None
    device_id: Optional[str] = None
    agent_id: Optional[str] = None
    country_code: Optional[str] = None
    currency: Optional[str] = None

    def __init__(
            self,
            *,
            api_token: Optional[str] = None,
            username: Optional[str] = None,
            device_id: Optional[str] = None,
            agent_id: Optional[str] = None,
            country_code: Optional[str] = None,
            currency: Optional[str] = None,
            url_base: Optional[str] = None,
            debug: Optional[bool] = False,
    ):
        self.url_base = url_base or os.getenv("KIU_API_URL", "https://kiuapi-stage.kiusys.net")
        self.debug = debug if debug is not None else False
        self.api_token = api_token or os.getenv("KIU_API_TOKEN", "")
        self.username = username or os.getenv("KIU_USER", None)
        self.device_id = device_id or os.getenv("KIU_DEVICE_ID", None)
        self.agent_id = agent_id or os.getenv("KIU_AGENT_ID", None)
        self.country_code = country_code or os.getenv("KIU_COUNTRY_CODE", None)
        self.currency = currency or os.getenv("KIU_CURRENCY", None)

    @property
    def headers(self) -> Mapping[str, str]:
        return {
            "KIU-API-Token": self.api_token,
            "Content-Type": "application/json"
        }

    def endpoint(self, kind: FlightResultKind):
        return {
            FlightResultKind.FLIGHT_SEARCH: "/agencies/air/get_availability",
            FlightResultKind.SHOPPING_LITE: "/agencies/smartpricing/shopping_lite",
            FlightResultKind.ITINERARY_QUOTE: "/agencies/smartpricing/itinerary_quote",
            FlightResultKind.CREATE_BOOKING: "/agencies/services/booking/create_booking",
            FlightResultKind.ISSUE_TICKETS: "/agencies/services/booking/issue_tickets",
            FlightResultKind.BOOKING_INFORMATION: "/agencies/air/booking/get_booking_information",
            FlightResultKind.VOID_DOCUMENTS: "/agencies/services/booking/void_documents",
            FlightResultKind.CANCEL_BOOKING: "/agencies/services/booking/cancel_air_segments_itinerary",
        }.get(kind)

    def request(
            self,
            request_id: str,
            *,
            payload: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, Any]] = None,
            method: RequestMethod = RequestMethod.POST,
            on_complete: Optional[Callable] = None,
            kind: Optional[FlightResultKind] = None,
            show_response: bool = False,
            timeout: Optional[int] = 100
    ):
        """Make an HTTP request to the specified URL with the given payload and headers."""

        if not payload:
            payload = {}

        start = datetime.now(timezone.utc)

        headers = {
            **(headers or {}),
            **self.headers,
        }

        url = self.url_base

        if kind:
            url = f"{url}{self.endpoint(kind)}"

        if self.debug:
            logger.debug("-" * 100)
            logger.debug("URL: %s", url)
            logger.debug("Start time: %s", start.strftime("%d/%m/%Y %H:%M:%S"))
            logger.debug("Headers: %s", {**headers, "KIU-API-Token": "***"})
            logger.debug("Payload: %s", payload)

        if method == RequestMethod.POST:
            response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        else:
            raise ValueError("Unsupported request method")

        end = datetime.now(timezone.utc)

        if self.debug:
            logger.debug("-" * 100)
            logger.debug("End time: %s", end.strftime("%d/%m/%Y %H:%M:%S"))
            logger.debug("Duration: %s", end - start)
            logger.debug("Response status: %s", response.status_code)

        status_code = response.status_code

        try:
            data = response.json()
        except requests.exceptions.JSONDecodeError:
            data = response.text

        if show_response:
            logger.debug("Response data: %s", data)

        if on_complete:
            on_complete(metadata=FlightRequestMetadata(
                status=status_code,
                request_id=request_id,
                kind=kind,
                headers=headers,
                request=payload,
                method=method,
                url=url,
                response=response.text,
                start_time=start,
                end_time=end,
                duration=(end - start).total_seconds() if end else None,
            ))

        errors = []

        if errors:
            return 400, errors

        return status_code, data

    @property
    def pos(self):
        return {
            "user": self.username,
            "kiu_device_id": self.device_id,
            "agent_id": self.agent_id,
            "country": self.country_code,
            "preferred_display_currency": self.currency,
        }

    @staticmethod
    def ptc_quantities(passengers: List[FlightAvailabilityPassenger]):
        quantities = {kind: 0 for kind in PassengerType}
        for passenger in passengers:
            quantities[passenger.kind] += passenger.qty

        return {
            PassengerType.ADULT.value: {
                "adult": quantities[PassengerType.ADULT],
                "child": quantities[PassengerType.CHILD],
                "infant": quantities[PassengerType.INFANT],
            }
        }

    def get_availability(
            self,
            itinerary: List[FlightAvailabilityItinerary],
            passengers: List[FlightAvailabilityPassenger],
            *,
            on_complete: Optional[Callable] = None,
            direct_flights_only: Optional[bool] = False,
            show_response: bool = False,
            timeout: Optional[int] = 100
    ):
        payload = {
            "point_of_sale": self.pos,
            "flight_search_criteria": {
                "origin_destinations_list": [
                    {
                        "item_order": str(i + 1),
                        "departure_information": {
                            "location_code": item.departing_iata_code,
                            "date": item.date.strftime("%Y-%m-%d"),
                        },
                        "arrival_information": {
                            "location_code": item.arrival_iata_code
                        },
                        "extra_search_criteria": {
                            "show_summary_rbd": True,
                            "direct_flights_only": direct_flights_only
                        }
                    }
                    for i, item in enumerate(itinerary)
                ]
            }
        }

        return self.request(
            request_id=str(uuid4()),
            payload=payload,
            on_complete=on_complete,
            show_response=show_response,
            timeout=timeout,
            kind=FlightResultKind.FLIGHT_SEARCH
        )

    def shopping_lite(
            self,
            itinerary: List[FlightAvailabilityItinerary],
            passengers: List[FlightAvailabilityPassenger],
            *,
            carrier: Optional[str] = None,
            display_currency: Optional[str] = None,
            echo_token: Optional[str] = None,
            on_complete: Optional[Callable] = None,
            show_response: bool = False,
            timeout: Optional[int] = 100
    ):
        request_id = str(uuid4())

        payload = {
            "date_time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "echo_token": echo_token or request_id,
            "point_of_sale": {key: value for key, value in self.pos.items() if key != "preferred_display_currency"},
            "shopping_parameter": {
                "air_preferences": {
                    "carrier": carrier
                } if carrier else {}
            },
            "shopping_criteria": {
                "display_currency": display_currency or self.currency
            },
            "journey_information": {
                "air_itinerary": {
                    "origin_destinations_list": [
                        {
                            "departure_information": {
                                "location_code": item.departing_iata_code,
                                "date": item.date.strftime("%Y-%m-%d"),
                            },
                            "arrival_information": {
                                "location_code": item.arrival_iata_code
                            },
                            "return_date": item.return_date.strftime("%Y-%m-%d") if item.return_date else ""
                        }
                        for item in itinerary
                    ]
                },
                "traveler_information": {
                    "passenger_type_code_quantity": self.ptc_quantities(passengers)
                }
            }
        }

        return self.request(
            request_id=request_id,
            payload=payload,
            on_complete=on_complete,
            show_response=show_response,
            timeout=timeout,
            kind=FlightResultKind.SHOPPING_LITE
        )

    def itinerary_quote(
            self,
            segments: List[FlightQuoteSegment],
            passengers: List[FlightAvailabilityPassenger],
            *,
            combine_rbd_by_segment: bool = True,
            echo_token: Optional[str] = None,
            on_complete: Optional[Callable] = None,
            show_response: bool = False,
            timeout: Optional[int] = 100
    ):
        request_id = str(uuid4())

        payload = {
            "echo_token": echo_token or request_id,
            "point_of_sale": self.pos,
            "combine_rbd_by_segment": combine_rbd_by_segment,
            "ptc_information": self.ptc_quantities(passengers),
            "flight_segments": [
                {
                    "origin_destination": segment.origin_destination,
                    "stop_over": segment.stop_over,
                    "segment_number": segment.segment_number,
                    "carrier_code": segment.carrier_code,
                    "flight_number": segment.flight_number,
                    "departure_date_time": segment.departure.strftime("%Y-%m-%d %H:%M"),
                    "arrival_date_time": segment.arrival.strftime("%Y-%m-%d %H:%M"),
                    "reservation_booking_designator": segment.rbds,
                    "departure_airport_location_code": segment.departing_iata_code,
                    "arrival_airport_location_code": segment.arrival_iata_code,
                }
                for segment in segments
            ]
        }

        return self.request(
            request_id=request_id,
            payload=payload,
            on_complete=on_complete,
            show_response=show_response,
            timeout=timeout,
            kind=FlightResultKind.ITINERARY_QUOTE
        )

    def create_booking(
            self,
            passengers: List[BookingPassenger],
            segments: List[BookingSegment],
            phones: List[BookingPhone],
            *,
            address: Optional[Dict[str, Any]] = None,
            remarks: Optional[List[str]] = None,
            auto_cancel: bool = True,
            air_price: bool = True,
            echo_token: Optional[str] = None,
            on_complete: Optional[Callable] = None,
            show_response: bool = False,
            timeout: Optional[int] = 100
    ):
        request_id = str(uuid4())

        contact_information = {
            "phone_list": [
                {
                    "city_location_code": phone.city_location_code,
                    "phone_detail": phone.phone_detail,
                    "contact_type": phone.contact_type,
                    "passenger_reference_order_association": phone.passenger_reference_order,
                }
                for phone in phones
            ]
        }
        if address:
            contact_information["address_information"] = {"residence": address}

        payload = {
            "date_time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "echo_token": echo_token or request_id,
            "point_of_sale": self.pos,
            "passenger_information": [
                {
                    "passenger_reference_order": passenger.reference_order,
                    "surname": passenger.surname,
                    "name": passenger.name,
                    "gender": passenger.gender,
                    "foid_type": passenger.foid_type,
                    "foid_id": passenger.foid_id,
                    "passenger_type_code": passenger.kind.value,
                }
                for passenger in passengers
            ],
            "air_itinerary_information": [
                {
                    "order": segment.order,
                    "departure_information": {
                        "location_code": segment.departing_iata_code,
                        "date": segment.departure.strftime("%Y-%m-%d"),
                        "time": segment.departure.strftime("%H%M"),
                    },
                    "arrival_information": {
                        "location_code": segment.arrival_iata_code
                    },
                    "flight_number": int(segment.flight_number),
                    "reservation_booking_designator_code": segment.rbd,
                    "number_in_party": segment.number_in_party,
                    "carrier": segment.carrier,
                }
                for segment in segments
            ],
            "contact_information": contact_information,
            "time_limits_criteria": {
                "booking_ticket_time_limit": {
                    "auto_cancel": auto_cancel
                }
            },
            "air_price": air_price,
        }
        if remarks:
            payload["remarks_list"] = [
                {"order": index, "remark_type": "I.", "text": text} for index, text in enumerate(remarks, start=1)
            ]

        return self.request(
            request_id=request_id,
            payload=payload,
            on_complete=on_complete,
            show_response=show_response,
            timeout=timeout,
            kind=FlightResultKind.CREATE_BOOKING
        )

    def issue_tickets(
            self,
            record_locator: str,
            record_locator_version: str,
            validating_carrier: str,
            *,
            payment_type: str = "CASH",
            order_reference_key: Optional[str] = None,
            exchange: bool = False,
            reconfirm_action: bool = True,
            echo_token: Optional[str] = None,
            on_complete: Optional[Callable] = None,
            show_response: bool = False,
            timeout: Optional[int] = 100
    ):
        """Issues the tickets of a reservation: record_locator_version is the one of its last change."""
        request_id = str(uuid4())

        payload = {
            "date_time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "echo_token": echo_token or request_id,
            "point_of_sale": self.pos,
            "record_locator_version_information": {
                "record_locator": record_locator,
                "record_locator_version": record_locator_version,
            },
            "order_reference_key": order_reference_key or request_id,
            "validating_carrier": validating_carrier,
            "exchange": exchange,
            "first_form_of_payment": {
                "type": payment_type
            },
            "reconfirm_action": reconfirm_action,
        }

        return self.request(
            request_id=request_id,
            payload=payload,
            on_complete=on_complete,
            show_response=show_response,
            timeout=timeout,
            kind=FlightResultKind.ISSUE_TICKETS
        )

    def get_booking_information(
            self,
            record_locator: str,
            *,
            on_complete: Optional[Callable] = None,
            show_response: bool = False,
            timeout: Optional[int] = 100
    ):
        """The reservation as it is now in KIU: its passengers, flights, prices, tickets and version."""
        return self.request(
            request_id=str(uuid4()),
            payload={
                "point_of_sale": self.pos,
                "record_locator": record_locator,
            },
            on_complete=on_complete,
            show_response=show_response,
            timeout=timeout,
            kind=FlightResultKind.BOOKING_INFORMATION
        )

    def void_documents(
            self,
            record_locator: str,
            record_locator_version: str,
            tickets: List[str],
            *,
            echo_token: Optional[str] = None,
            on_complete: Optional[Callable] = None,
            show_response: bool = False,
            timeout: Optional[int] = 100
    ):
        """Voids tickets of a reservation: record_locator_version is the one of its last change."""
        request_id = str(uuid4())

        return self.request(
            request_id=request_id,
            payload={
                "date_time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "echo_token": echo_token or request_id,
                "point_of_sale": self.pos,
                "record_locator_version_information": {
                    "record_locator": record_locator,
                    "record_locator_version": record_locator_version,
                },
                "void_ticket_list": tickets,
            },
            on_complete=on_complete,
            show_response=show_response,
            timeout=timeout,
            kind=FlightResultKind.VOID_DOCUMENTS
        )

    def cancel_booking(
            self,
            record_locator: str,
            record_locator_version: str,
            *,
            remarks: Optional[List[str]] = None,
            cancel_air_itinerary: bool = True,
            echo_token: Optional[str] = None,
            on_complete: Optional[Callable] = None,
            show_response: bool = False,
            timeout: Optional[int] = 100
    ):
        """Cancels the flights of a reservation: record_locator_version is the one of its last change."""
        request_id = str(uuid4())

        payload = {
            "point_of_sale": self.pos,
            "date_time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "echo_token": echo_token or request_id,
            "record_locator_version_information": {
                "record_locator": record_locator,
                "record_locator_version": record_locator_version,
            },
            "cancel_air_itinerary": cancel_air_itinerary,
        }
        if remarks:
            payload["remarks_list"] = [{"text": text} for text in remarks]

        return self.request(
            request_id=request_id,
            payload=payload,
            on_complete=on_complete,
            show_response=show_response,
            timeout=timeout,
            kind=FlightResultKind.CANCEL_BOOKING
        )
