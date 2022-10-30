import abc
import re
from typing import Any

from sqlalchemy.orm import Session

from app import model

class AbstractRepository(abc.ABC):
    
    @abc.abstractmethod
    def add(self, batch: model.Batch) -> None:
        ...
    
    @abc.abstractmethod
    def get(slef, reference: str) -> model.Batch:
        ...


class SqlAlchemyRepository(AbstractRepository):
    """Repository fro SqlAlchmey support."""
    def __init__(self, session: Session) -> None: 
        self._session = session
        super().__init__()
    
    def add(self, batch: model.Batch) -> None:
        self._session.add(batch)
    
    def get(self, reference: str) -> list[model.Batch]:
        return self._session.query(model.Batch).filter_by(reference=reference).all()
    
    def list(self) -> list[model.Batch]:
        return self._session.query(model.Batch).all()


class FakeRepository(AbstractRepository):
    """Repository for Tests."""
    def __init__(self, batches: list[model.Batch]) -> None:
        self._batches = set(batches)
        super().__init__()
    
    def add(self, batch: model.Batch) -> None:
        self._batches.add(batch)
    
    def get(self, reference: str) -> model.Batch:
        return next(b for b in self._batches if b.reference == reference)
    
    def list(self) -> list[model.Batch]:
        return list(self._batches)
        