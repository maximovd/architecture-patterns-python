import logging
from typing import Callable, Type

from tenacity import Retrying, RetryError
from tenacity.stop import stop_after_attempt
from tenacity.wait import wait_exponential

from app.domain import events, commands
from app.service_layer import handlers, unit_of_work


Message = commands.Command | events.Event
logger = logging.getLogger(__name__)


def handle(message: Message, uow: unit_of_work.AbstractUnitOfWork):
    results = []
    queue = [message]
    
    while queue:

        if isinstance(message, events.Event):
            handle_event(message, queue=queue, uow=uow)

        elif isinstance(message, commands.Command):
            cmd_result = handle_command(message, queue=queue, uow=uow)
            results.append(cmd_result)

        else:
            raise Exception(f"{message} was not an Event or Command")

    return results


def handle_event(event: events.Event, queue: list[Message], uow: unit_of_work.AbstractUnitOfWork):
    for handler in EVENT_HANDLERS[type(event)]:
        try:
            for attempt in Retrying(stop=stop_after_attempt(3), wait=wait_exponential()):

                with attempt:
                    logger.debug(f"handling event {event} with handler {handler}")
                    handler(event, uow=uow)
                    queue.extend(uow.collect_new_events())

        except RetryError as retry_failure:
            logger.exception(f"Не получилось обработать событие {retry_failure.last_attempt.attempt_number} раз, отказ !")
            continue


def handle_command(command: command.Command, queue: list[Message], uow: unit_of_work.AbstractUnitOfWork):
    logger.debug(f"handling command {command}")
    
    try:
        handler = COMMAND_HANDLERS[type(command)]
        result = handler(command, uow=uow)
        queue.extend(uow.collect_new_events())
        return result
    except Exception:
        logger.exception(f"Exception handling command {command}")
        raise


def send_out_of_stock_notification(event: events.OutOfStock):
    email.send_mail(
            "stock@made.com",
            f"Артикула {event.sku} нет в наличии.",
        )


EVENT_HANDLERS: dict[Type[events.Event], list[Callable]] = {
    events.OutOfStock: [send_out_of_stock_notification],
}


COMMAND_HANDLERS: dict[Type[commands.Command], Callable] = {
    commands.Allocate: handlers.allocate,
    commands.CreateBatch: handlers.add_batch,
    commands.ChangeBatchQuantity: handlers.change_batch_quantity,
}

