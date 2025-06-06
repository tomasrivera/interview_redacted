from typing import Annotated

from fastapi import Depends
from pymongo import AsyncMongoClient, IndexModel
from pymongo.asynchronous.database import AsyncCollection, AsyncDatabase

from src.settings import settings

client: AsyncMongoClient = AsyncMongoClient(settings.mongo_url)
database = client.get_database(settings.mongo_db_name)


flights_collection = database.get_collection("flights")


def get_database() -> AsyncDatabase:
    return database


class FlightCollectionRepository:
    def __init__(self) -> None:
        self.flights = flights_collection


def get_flights_repository() -> FlightCollectionRepository:
    return FlightCollectionRepository()


FlightsRepository = Annotated[FlightCollectionRepository, Depends(get_flights_repository)]


async def _create_collection_indexes(collection: AsyncCollection, indexes: list[IndexModel]) -> None:
    index_names = []
    if indexes:
        index_names = await collection.create_indexes(indexes)

    list_indexes = await collection.list_indexes()
    all_indexes = {idx["name"]: idx for idx in await list_indexes.to_list(length=None)}
    old_indexes = list(set(all_indexes.keys()).difference(("_id_", *index_names)))
    for index in old_indexes:
        await collection.drop_index(index)


async def create_indexes() -> None:
    await _create_collection_indexes(
        flights_collection,
        [],
    )
