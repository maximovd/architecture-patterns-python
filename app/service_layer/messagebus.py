from typing import Callable, Type
from app.domain import events
from app.service_layer import handlers, unit_of_work


def handle(event: events.Event, uow: unit_of_work.AbstractUnitOfWork):
    results = []
    queue = [event]
    
    while queue:
        for handler in HANDLERS[type(event)]:
            handler(event, uow=uow)
            results.append(handler(event, uow=uow))
            queue.extend(uow.collect_new_events())
    
    # TODO: Возврат results - кривой костыль, мы смешиваем обязанности по чтению и записи.
    return results


def send_out_of_stock_notification(event: events.OutOfStock):
    email.send_mail(
            "stock@made.com",
            f"Артикула {event.sku} нет в наличии.",
        )


HANDLERS: dict[Type[events.Event], list[Callable]] = {
    events.BatchCreated: [handlers.add_batch],
    events.BatchQuantityChanged: [handlers.change_batch_quatntity],
    events.AllocationRequired: [handlers.allocate],
    events.OutOfStock: [send_out_of_stock_notification],

    }
