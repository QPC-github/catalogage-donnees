import datetime as dt
import random
from typing import Any, TypeVar

import faker
from faker.providers import BaseProvider
from pydantic import BaseModel
from pydantic_factories import ModelFactory, Use

from server.application.auth.commands import CreateUser
from server.application.datasets.commands import CreateDataset, UpdateDataset
from server.application.tags.commands import CreateTag
from server.domain.common import datetime as dtutil
from server.domain.datasets.entities import DataFormat

T = TypeVar("T", bound=BaseModel)


class DateTimeTZProvider(BaseProvider):
    def date_time_tz(self) -> dt.datetime:
        return self.generator.date_time(dtutil.UTC)


fake = faker.Faker(["fr_FR"])
fake.add_provider(DateTimeTZProvider)


class Factory(ModelFactory[T]):
    __faker__ = fake

    @classmethod
    def get_mock_value(cls, field_type: Any) -> Any:
        if field_type is dt.datetime:
            return fake.date_time_tz()
        return super().get_mock_value(field_type)


class CreateUserFactory(Factory[CreateUser]):
    __model__ = CreateUser


class CreateTagFactory(Factory[CreateTag]):
    __model__ = CreateTag


class CreateDatasetFactory(Factory[CreateDataset]):
    __model__ = CreateDataset

    title = Use(fake.sentence)
    description = Use(fake.text)
    service = Use(fake.company)
    formats = Use(lambda: random.choices(list(DataFormat), k=random.randint(1, 3)))
    technical_source = Use(
        lambda: fake.sentence(nb_words=3) if random.random() < 0.5 else None
    )
    producer_email = Use(fake.ascii_free_email)
    contact_emails = Use(
        lambda: [fake.ascii_free_email() for _ in range(random.randint(1, 3))]
    )
    published_url = Use(lambda: fake.url() if random.random() < 0.5 else None)
    tag_ids = Use(lambda: [])


class UpdateDatasetFactory(Factory[UpdateDataset]):
    __model__ = UpdateDataset

    tag_ids = Use(lambda: [])
