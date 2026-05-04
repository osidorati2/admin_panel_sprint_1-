from dataclasses import dataclass
from uuid import UUID
from datetime import datetime


@dataclass
class Genre:
    id: UUID
    name: str
    description: str | None
    created: datetime
    modified: datetime


@dataclass
class Person:
    id: UUID
    full_name: str
    created: datetime
    modified: datetime


@dataclass
class FilmWork:
    id: UUID
    title: str
    description: str | None
    creation_date: datetime | None
    rating: float | None
    type: str
    created: datetime
    modified: datetime
    file_path: str | None
    certificate: str | None