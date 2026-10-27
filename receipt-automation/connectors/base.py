from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass
class Receipt:
    vendor: str
    date: date
    amount: int
    file_path: Path


class BaseConnector(ABC):
    def __init__(self, page, config: dict):
        self.page = page
        self.config = config

    @abstractmethod
    async def login(self) -> None:
        pass

    @abstractmethod
    async def download_receipts(self, year: int, month: int) -> list[Receipt]:
        pass
