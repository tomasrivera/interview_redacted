from typing import Annotated

from fastapi import APIRouter, Body, HTTPException, Path, Query, status

from src.flights.models import (
    Flight,
    FlightCreate,
    FlightFilter,
    FlightSummary,
    FlightUpdate,
    Passenger,
    PassengerCreate,
    PassengerFilter,
    PassengerUpdate,
)
from src.flights.service import (
    DuplicatePassengerError,
    NotFoundError,
    PassengerNotFoundError,
    flights_add_passengers,
    flights_create,
    flights_delete,
    flights_get,
    flights_get_passenger_by_id,
    flights_get_passengers,
    flights_list,
    flights_remove_passengers,
    flights_update,
    flights_update_passenger,
)
from src.storage.db import FlightsRepository

router = APIRouter()


@router.get("/")
async def list_endpoint(
    repository: FlightsRepository,
    filters: Annotated[FlightFilter, Query(...)],
) -> list[FlightSummary]:
    return await flights_list(
        repository,
        filters=filters,
    )


@router.get("/{flight_id}")
async def get_endpoint(
    repository: FlightsRepository,
    flight_id: Annotated[str, Path(...)],
) -> Flight:
    try:
        return await flights_get(repository, flight_id=flight_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flight {flight_id} not found",
        ) from e


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_endpoint(repository: FlightsRepository, flight: Annotated[FlightCreate, Body(...)]) -> Flight:
    try:
        return await flights_create(repository, flight=flight)
    except DuplicatePassengerError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate passenger found",
        ) from e


@router.put("/{flight_id}")
async def update_endpoint(
    repository: FlightsRepository,
    flight_id: Annotated[str, Path(...)],
    flight: Annotated[FlightUpdate, Body(...)],
) -> Flight:
    try:
        return await flights_update(
            repository,
            flight_id=flight_id,
            flight=flight,
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flight {flight_id} not found",
        ) from e
    except DuplicatePassengerError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate passenger found",
        ) from e


@router.delete("/{flight_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_endpoint(
    repository: FlightsRepository,
    flight_id: Annotated[str, Path(...)],
) -> None:
    try:
        await flights_delete(repository, flight_id=flight_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flight {flight_id} not found",
        ) from e


@router.post("/{flight_id}/passengers", status_code=status.HTTP_201_CREATED)
async def add_passengers_endpoint(
    repository: FlightsRepository,
    flight_id: Annotated[str, Path(...)],
    passengers: Annotated[list[PassengerCreate], Body()],
) -> Passenger:
    try:
        created_passengers = await flights_add_passengers(repository, flight_id=flight_id, passengers=passengers)
        return created_passengers[0]
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flight {flight_id} not found",
        ) from e
    except DuplicatePassengerError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate passenger found",
        ) from e


@router.put("/{flight_id}/passengers/{passenger_id}")
async def update_passenger_endpoint(
    repository: FlightsRepository,
    flight_id: Annotated[str, Path(...)],
    passenger_id: Annotated[int, Path(...)],
    passenger: Annotated[PassengerUpdate, Body(...)],
) -> Passenger:
    try:
        return await flights_update_passenger(
            repository, flight_id=flight_id, passenger_id=passenger_id, passenger=passenger
        )
    except PassengerNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Passenger {passenger_id} not found in flight {flight_id}",
        ) from e
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flight {flight_id} not found",
        ) from e


@router.delete("/{flight_id}/passengers/{passenger_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_passenger_endpoint(
    repository: FlightsRepository,
    flight_id: Annotated[str, Path(...)],
    passenger_id: Annotated[int, Path(...)],
) -> None:
    try:
        await flights_remove_passengers(
            repository,
            flight_id=flight_id,
            passenger_ids=[passenger_id],
        )
    except PassengerNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Passenger {passenger_id} not found in flight {flight_id}",
        ) from e
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flight {flight_id} not found",
        ) from e


@router.get("/{flight_id}/passengers/{passenger_id}")
async def get_passenger_by_id_endpoint(
    repository: FlightsRepository,
    flight_id: Annotated[str, Path(...)],
    passenger_id: Annotated[int, Path(...)],
) -> Passenger:
    try:
        return await flights_get_passenger_by_id(
            repository,
            flight_id=flight_id,
            passenger_id=passenger_id,
        )
    except PassengerNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Passenger {passenger_id} not found in flight {flight_id}",
        ) from e


@router.get(
    "/{flight_id}/passengers",
)
async def get_passengers_endpoint(
    repository: FlightsRepository, flight_id: Annotated[str, Path(...)], filters: Annotated[PassengerFilter, Query(...)]
) -> list[Passenger]:
    try:
        return await flights_get_passengers(
            repository,
            flight_id=flight_id,
            filters=filters,
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flight {flight_id} not found",
        ) from e


@router.get(
    "/{flight_id}/overbooked_passengers",
)
async def get_overbooked_passengers_endpoint(
    repository: FlightsRepository,
    flight_id: Annotated[str, Path(...)],
) -> list[Passenger]:
    try:
        flight = await flights_get(
            repository,
            flight_id=flight_id,
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flight {flight_id} not found",
        ) from e
    return flight.overbooked_passengers
