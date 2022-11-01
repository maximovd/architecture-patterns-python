from sqlalchemy.orm import Session

from app.model import OrderLine
from app.repository import AbstractRepository


class InvalidSku(Exception):
    pass


def is_invalid_sku(sku: str, batches: list) -> bool:
    return sku in {b.sku for b in batches}


def allocate(line: OrderLine, repo: AbstractRepository, session: Session) -> str:
    batches = repo.list()
    
    if not is_invalid_sku(line.sku, batches):
        raise InvalidSku(f"Недопустимый артикул {line.sku}")

    batchref = model.allocate(line, batches)
    session.commit()

    return batchref


    
