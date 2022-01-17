from typing import List, Optional

from server.seedwork.domain.repositories import Repository

from ..common.types import ID
from .entities import Dataset


class DatasetRepository(Repository):
    async def get_all(self) -> List[Dataset]:
        raise NotImplementedError  # pragma: no cover

    async def get_by_id(self, id: ID) -> Optional[Dataset]:
        raise NotImplementedError  # pragma: no cover

    async def insert(self, entity: Dataset) -> ID:
        raise NotImplementedError  # pragma: no cover

    async def delete(self, id: ID) -> None:
        raise NotImplementedError  # pragma: no cover