from app.domain import events, model
from app.service_layer.unit_of_work import AbstractUnitOfWork


class InvalidSku(Exception):
    pass


def is_invalid_sku(sku: str, batches: list) -> bool:
    return sku in {b.sku for b in batches}


def allocate(event: events.AllocationRequired, uow: AbstractUnitOfWork) -> str:
    """Сервис резервирования товаров в партиях."""

    line = model.OrderLine(order_id=event.orderid, sku=event.sku, quantity=event.qty)

    with uow:
        product = uow.products.get(sku=event.sku)

        if product is None:
            raise InvalidSku(f"Недопустимый артикул {line.sku}")

        batchref = product.allocate(line)
        uow.commit()

    return batchref


def add_batch(event: events.BatchCreated, uow: AbstractUnitOfWork) -> None:
    """Сервис довабление новой партии в поставку."""
    with uow:
        product = uow.products.get(sku=event.sku)

        if product is None:
            product = model.Product(event.sku, batches=[])
            uow.products.add(product)
        
        product.batches.append(model.Batch(ref=event.ref, sku=event.sku, qty=event.qty, eta=event.eta))
        uow.commit()


def send_out_of_stock_notification(event: events.OutOfStock, uow: AbstractUnitOfWork):
    email.send("stock@made.me", f"Артикула {event.sku} нет в наличии")


def change_batch_quantity(event: events.BatchQuantityChanged, uow: AbstractUnitOfWork):
    with uow:
        product = uow.products.get_by_batchref(batchref=event.ref)
        product.change_batch_quantity(ref=event.ref, qty=event.qty)
        uow.commit()

