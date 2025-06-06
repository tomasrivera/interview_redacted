import enum
from typing import Annotated

from pydantic import BaseModel as PydanticBaseModel
from pydantic import BeforeValidator, ConfigDict, Field
from pydantic.alias_generators import to_camel


class FlightCategories(enum.StrEnum):
    BLACK = "Black"
    PLATINUM = "Platinum"
    GOLD = "Gold"
    NORMAL = "Normal"


PyObjectId = Annotated[str, BeforeValidator(str)]


class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class FlightBase(BaseModel):
    flight_code: str = Field(...)
    capacity: int = Field(..., ge=1)


class FlightSummary(FlightBase):
    id: PyObjectId = Field(alias="_id")


class Flight(FlightBase):
    id: PyObjectId | None = Field(alias="_id", default=None)
    passengers: list["Passenger"] = Field(default_factory=list)
    overbooked_passengers: list["Passenger"] = Field(default_factory=list)


class FlightCreate(FlightBase):
    passengers: list["PassengerCreate"] = Field(default_factory=list)


class FlightUpdate(FlightBase):
    flight_code: str = Field(...)
    passengers: list["PassengerCreate"] = Field(default_factory=list)


class PassengerBase(BaseModel):
    id: int = Field(...)
    name: str = Field(...)
    has_connections: bool = Field(...)
    age: int = Field(..., ge=0)
    flight_category: FlightCategories = Field(default=FlightCategories.NORMAL)
    reservation_id: str = Field(...)
    has_checked_baggage: bool = Field(...)


class Passenger(PassengerBase): ...


class PassengerCreate(PassengerBase): ...


class PassengerUpdate(BaseModel):
    name: str | None = Field(default=None)
    has_connections: bool | None = Field(default=None)
    age: int | None = Field(default=None, ge=0)
    flight_category: FlightCategories | None = Field(default=None)
    reservation_id: str | None = Field(default=None)
    has_checked_baggage: bool | None = Field(default=None)


class Pagination(BaseModel):
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class FlightFilter(Pagination):
    flight_code: str | None = Field(default=None)


class PassengerFilter(BaseModel):
    name: str | None = Field(default=None)
    has_connections: bool | None = Field(default=None)
    age: int | None = Field(default=None, ge=0)
    flight_category: FlightCategories | None = Field(default=None)
    reservation_id: str | None = Field(default=None)
    has_checked_baggage: bool | None = Field(default=None)
