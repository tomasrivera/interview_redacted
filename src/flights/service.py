from collections import defaultdict
from typing import Any, DefaultDict, TypedDict

from bson import ObjectId

from src.flights.models import (
    Flight,
    FlightCategories,
    FlightCreate,
    FlightFilter,
    FlightSummary,
    FlightUpdate,
    Passenger,
    PassengerCreate,
    PassengerFilter,
    PassengerUpdate,
)
from src.flights.utils import assert_unique
from src.storage.db import FlightCollectionRepository


class ServiceError(Exception):
    """A custom exception for service errors in the flights module."""


class NotFoundError(ServiceError):
    """A custom exception for not found errors in the flights module."""


class PassengerNotFoundError(NotFoundError):
    """A custom exception for flight passenger not found errors."""


class DuplicatePassengerError(ServiceError):
    """A custom exception for duplicate passenger errors."""


async def flights_list(
    repository: FlightCollectionRepository,
    *,
    filters: FlightFilter | None = None,
) -> list[FlightSummary]:
    filters = filters or FlightFilter()
    filter_dict = {}
    for field, value in filters.model_dump(
        exclude_unset=True,
        exclude={"limit", "offset"},
    ).items():
        alias = FlightFilter.model_fields[field].alias
        filter_dict[alias] = value

    cursor = repository.flights.find(
        filter_dict,
        {"passengers": 0},
        skip=filters.offset,
        limit=filters.limit,
    )
    results = await cursor.to_list()
    return [FlightSummary(**f) for f in results]


async def flights_get(
    repository: FlightCollectionRepository,
    *,
    flight_id: str,
) -> Flight:
    result = await repository.flights.find_one({"_id": ObjectId(flight_id)})
    if result is None:
        raise NotFoundError
    return Flight(**result)


async def flights_create(
    repository: FlightCollectionRepository,
    *,
    flight: FlightCreate,
) -> Flight:
    booked_passengers, overbooked_passengers = _order_passengers(flight.passengers, flight.capacity)
    booked_passengers_data = await _get_create_passengers_data(
        repository=repository,
        flight_id=None,
        passengers=booked_passengers,
    )
    overbooked_passengers_data = await _get_create_passengers_data(
        repository=repository,
        flight_id=None,
        passengers=overbooked_passengers,
    )
    new_flight = await repository.flights.insert_one(
        {
            **flight.model_dump(by_alias=True, exclude={"id", "passengers"}),
            "passengers": booked_passengers_data,
            "overbookedPassengers": overbooked_passengers_data,
        }
    )
    result = await repository.flights.find_one({"_id": new_flight.inserted_id})
    if result is None:
        raise ServiceError
    return Flight(**result)


async def flights_update(
    repository: FlightCollectionRepository,
    *,
    flight_id: str,
    flight: FlightUpdate,
) -> Flight:
    data = flight.model_dump(
        by_alias=True,
        exclude_defaults=True,
        exclude_unset=True,
        exclude={"passengers"},
    )
    update_passengers = "passengers" in flight.model_fields_set
    if update_passengers:
        data["passengers"] = await _get_create_passengers_data(
            repository=repository,
            flight_id=None,
            passengers=flight.passengers,
        )

    result = await repository.flights.find_one_and_update(
        {"_id": ObjectId(flight_id)},
        {"$set": data},
        return_document=True,
    )

    if result is None:
        raise NotFoundError

    return Flight(**result)


async def flights_delete(
    repository: FlightCollectionRepository,
    *,
    flight_id: str,
) -> None:
    result = await repository.flights.delete_one({"_id": ObjectId(flight_id)})

    if result.deleted_count == 1:
        return
    raise NotFoundError


async def flights_add_passengers(
    repository: FlightCollectionRepository,
    *,
    flight_id: str,
    passengers: list[PassengerCreate],
) -> list[Passenger]:
    data = await _get_create_passengers_data(
        repository=repository,
        flight_id=flight_id,
        passengers=passengers,
    )
    result = await repository.flights.update_one(
        {"_id": ObjectId(flight_id)},
        {"$push": {"passengers": {"$each": data}}},
    )

    if result.matched_count == 0:
        raise NotFoundError

    return [Passenger(**p) for p in data]


async def flights_remove_passengers(
    repository: FlightCollectionRepository,
    *,
    flight_id: str,
    passenger_ids: list[int],
) -> None:
    result = await repository.flights.update_one(
        {"_id": ObjectId(flight_id)},
        {"$pull": {"passengers": {"id": {"$in": passenger_ids}}}},
    )

    if result.matched_count == 0:
        raise NotFoundError
    if result.modified_count == 0:
        raise PassengerNotFoundError


async def flights_update_passenger(
    repository: FlightCollectionRepository,
    *,
    flight_id: str,
    passenger_id: int,
    passenger: PassengerUpdate,
) -> Passenger:
    flight = await repository.flights.find_one(
        {"_id": ObjectId(flight_id)},
        {"_id": 1},
    )
    if not flight:
        raise NotFoundError

    data = {
        f"passengers.$.{k}": v
        for k, v in passenger.model_dump(
            by_alias=True,
            exclude_unset=True,
            exclude_defaults=True,
        ).items()
    }
    result = await repository.flights.find_one_and_update(
        {"_id": ObjectId(flight_id), "passengers.id": passenger_id},
        {"$set": data},
        return_document=True,
    )

    updated_passengers = result.get("passengers", []) if result else []
    updated_passenger = next((p for p in updated_passengers if p["id"] == passenger_id), None)
    if updated_passenger is None:
        raise PassengerNotFoundError

    return Passenger(**updated_passenger)


async def flights_get_passenger_by_id(
    repository: FlightCollectionRepository,
    *,
    flight_id: str,
    passenger_id: int,
) -> Passenger:
    result = await repository.flights.find_one(
        {"_id": ObjectId(flight_id), "passengers.id": passenger_id},
        {"passengers.$": 1},
    )

    if result is None or not result.get("passengers", []):
        raise PassengerNotFoundError

    return Passenger(**result["passengers"][0])


async def flights_get_passengers(
    repository: FlightCollectionRepository,
    *,
    flight_id: str,
    filters: PassengerFilter | None = None,
) -> list[Passenger]:
    passenger_filter = {}
    for field, value in filters.model_dump(exclude_unset=True).items():
        alias = PassengerFilter.model_fields[field].alias
        passenger_filter[alias] = value

    pipeline: list[dict[str, Any]] = [
        {"$match": {"_id": ObjectId(flight_id)}},
        {
            "$project": {
                "passengers": {
                    "$filter": {
                        "input": "$passengers",
                        "as": "p",
                        "cond": {"$and": [{"$eq": [f"$$p.{k}", v]} for k, v in passenger_filter.items()]}
                        if passenger_filter
                        else True,
                    }
                }
            }
        },
    ]

    cursor = await repository.flights.aggregate(pipeline)
    result = await cursor.to_list(length=1)
    if not result:
        raise NotFoundError

    passengers = result[0].get("passengers", [])
    return [Passenger(**p) for p in passengers]


async def _get_create_passengers_data(
    repository: FlightCollectionRepository,
    *,
    flight_id: str | None,
    passengers: list[PassengerCreate],
) -> list[dict]:
    data = [{**passenger.model_dump(by_alias=True)} for passenger in passengers]

    flight = await repository.flights.find_one(
        {"_id": ObjectId(flight_id)},
        {"passengers": 1},
    )
    if flight is None and flight_id is not None:
        raise NotFoundError
    existing_passengers = flight.get("passengers", []) if flight is not None else []
    try:
        assert_unique(existing_passengers, data, "id")
    except ValueError as e:
        raise DuplicatePassengerError from e

    return data


def _order_passengers(
    passengers: list[PassengerCreate],
    capacity: int,
) -> tuple[list[PassengerCreate], list[PassengerCreate]]:
    category_weights = {
        FlightCategories.BLACK: 10,
        FlightCategories.PLATINUM: 7,
        FlightCategories.GOLD: 5,
        FlightCategories.NORMAL: 2,
    }
    connection_weight = 3
    checked_baggage_weight = 2
    age_weight = 1
    class GroupedPassengers(TypedDict):
        total: int
        passengers: list[PassengerCreate]

    groups:  defaultdict[str, GroupedPassengers] = defaultdict()
    for p in passengers:
        groups.setdefault(p.reservation_id, {"passengers": [], "total": 0})
        groups[p.reservation_id]["passengers"].append(p)
        groups[p.reservation_id]["total"] += (
            category_weights[p.flight_category]
            + (connection_weight if p.has_connections else 0)
            + (checked_baggage_weight if p.has_checked_baggage else 0)
            + (age_weight * p.age)
        )

    booked: list[PassengerCreate] = []
    overbooked: list[PassengerCreate] = []
    ordered_groups = sorted(
        groups.values(),
        key=lambda g: (
            -g["total"] / len(g["passengers"]),
            -len(g["passengers"]),
        ),
    )

    for group in ordered_groups:
        if len(booked) + len(group["passengers"]) <= capacity:
            booked.extend(group["passengers"])
        else:
            overbooked.extend(group["passengers"])

    return booked, overbooked
