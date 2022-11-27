import abc

from sqlalchemy.orm import Session

from app import model


class AbstractRepository(abc.ABC):
    def __init__(self) -> None:
        self.seen: set[model.Product] = set()
    
    def add(self, product: model.Product) -> None:
        self._add(product) 
    
    def get(self, sku: str) -> model.Product:
        product = self._get(sku)
        if product:
            self.seen.add(product)
        return product

    def get_by_batchref(self, batchref: str) -> model.Product:
        product = self._get_by_batchref(batchref)

        if product:
            self.seen.add(product)

        return product
    
    @abc.abstractmethod
    def _add(self, product: model.Product) -> None:
        ...
    
    @abc.abstractmethod
    def _get(self, sku: str) -> model.Product:
        ...

    @abc.abstractmethod
    def list(self) -> list[model.Batch]:
        ...

    @abc.abstractmethod
    def _get_by_batchref(self, batchref):
        ...


class AbstractProductRepository(abc.ABC):
    
    @abc.abstractmethod
    def add(self, product):
        ...
    
    @abc.abstractmethod
    def get(self, sku) -> model.Product:
        ...



class SqlAlchemyRepository(AbstractRepository):
    """Repository for SqlAlchemy support."""


    def __init__(self, session: Session) -> None:
        super().__init__()
        self._session = session
    
    def _add(self, product: model.Product) -> None:
        self._session.add(product)
    
    def _get(self, sku: str) -> list[model.Product]:
        return self._session.query(model.Product).filter_by(sku=sku).first()
    
    def list(self) -> list[model.Batch]:
        return self._session.query(model.Batch).all()

    def _get_by_batchref(self, batchref):
        return self._session.query(model.Product).join(model.Batch).filter(orm.batches.c.reference == batchref).first()


class FakeRepository(AbstractRepository):
    """
    Repository for Tests.
    TODO: Убрать в tests/helper
    """

    seen: set[model.Product]

    def __init__(self, repo: AbstractRepository) -> None:
        self.seen = set()
        self._repo = repo

    
    def add(self, product: model.Product) -> None:
        self._repo.add(product)
        self.seen.add(product)
    
    def _get(self, sku):
        return next((p for p in self._products if p.sku == sku), None)

    def _get_by_batchref(self, batchref):
        return next((p for p in self._products for b in p.batches if b.reference == batchref), None)
