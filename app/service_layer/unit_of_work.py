import abc

from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine

from app.adapters import repository
from app import config


DEFAULT_SESSION_FACTORY = sessionmaker(bind=create_engine(config.get_postgres_uri()))

class AbstractUnitOfWork(abc.ABC):
    products: repository.AbstractProductRepository

    def __exit__(self, *args) -> None:
        self.rollback()
    
    def __enter__(self):
        ...

    def commit(self):
        self._commit()
        self.collect_new_events()

    def collect_new_events(self):
        for product in self.products.seen:
            while product.events:
                event = product.events.pop(0)
                messagebus.handle(event)
                yield product.events.pop(0)

    @abc.abstractmethod
    def _commit(self):
        raise NotImplemented


    @abc.abstractmethod
    def rollback(self):
        ...


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory=DEFAULT_SESSION_FACTORY):
        self._session_factory = session_factory
    
    def __enter__(self):
        self._session: Session = self._session_factory()
        self._batches = repository.SqlAlchemyRepository(self._session)
        return super().__enter__()
    
    def __exit__(self, *args):
        super().__exit__(*args)
        self._session.close()

    def _commit(self):
        self._session.commit()
    
    def rollback(self):
        self._session.rollback()


