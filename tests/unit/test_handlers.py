import datetime

import pytest

from app.domain import events, model
from app.adapters.repository import FakeRepository
from app.service_layer import messagebus, services, unit_of_work

TODAY = datetime.date.today()
TOMORROW = TODAY + datetime.timedelta(days=1)


class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):
    
    def __init__(self) -> None:
        self.batches = FakeRepository([])
        self.commited = False
        super().__init__()
    
    def commit(self):
        self.commited = True
    
    def rollback(self):
        pass



def test_error_for_invalid_sku():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "AREALSKU", 100, None, repo, session)
    
    with pytest.raises(services.InvalidSku, match="Недопустимый артикул NONEXISTENTSKU"):
        services.allocate("o1", "NONEXISTENTSKU", 10, repo, session)

# TODO: Переписать оставшиеся тесты

def test_commits():
    line = model.OrderLine(order_id="o1", sku="OMNIOUS-MIRROR", quantity=10)
    batch = model.Batch(ref="b1", sku="OMNIOUS-MIRROR", qty=100, eta=None)

    repo = FakeRepository([batch])
    session = FakeSession()

    services.allocate(line, repo, session)

    assert session.commited is True

def test_prefers_warehouse_batches_to_shipment():
    in_stock_batch = model.Batch(ref="in-stock-batch", sku="RETRO-CLOCK", qty=100, eta=None)
    shipment_batch = model.Batch(ref="shipment-batch", sku="RETRO-CLOCK", qty=100, eta=TOMORROW)

    line = model.OrderLine(order_id="oref", sku="RETRO-CLOCK", quantity=10)
    repo = FakeRepository([in_stock_batch, shipment_batch])
    session = FakeSession()

    services.allocate(line, repo, session)

    assert in_stock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100


class TestAddBatch:
    def test_for_new_product(self):
        uow = FakeUnitOfWork()

        messagebus.handle(events.BatchCreated("b1", "CRUNCHY-ARMCHAIR", 100, None), uow)
        
        assert uow.products.get("CRUNCHY-ARMCHAIR") is not None
        assert uow.commited


class TestAllocate:
    def test_returns_allocation(self):
        uow = FakeUnitOfWork()

        messagebus.handle(events.BatchCreated("batch1", "COMPLICATED-LAMP", 100, None), uow)
        result = messagebus.handle(events.AllocationRequired("o1", "COMPLICATED-LAMP", 10, None), uow)

        assert result == "batch1"


class TestChangedBatchQuantity:
    def test_changes_available_quantity(self):
        uow = FakeUnitOfWork()
        messagebus.handle(events.BatchCreated("batch1", "ADORABLE-SETTEL", 100, None), uow)
        [batch] = uow.products.get(sku="ADORABLE-SETTEL").batches

        assert batch.available_quantity == 100

        messagebus.handle(events.BatchQuantityChanged("batch1", 50), uow)

        assert batch.available_quantity == 50

    def test_reallocates_if_nessesary(self):
        uow = FakeUnitOfWork()

        event_history = [
                events.BatchCreated("batch1", "INDIFFERENT-TABLE", 50, None),
                events.BatchCreated("batch2", "INDIFFERENT-TABLE", 50, TODAY),
                events.AllocationRequired("order1", "INDIFFERENT-TABLE", 20),
                events.AllocationRequired("order2", "INDIFFERENT-TABLE", 20),
            ]
        for e in event_history:
            messagebus.handle(e, uow)

        [batch1, batch2] = uwo.products.get(sku="INDIFFERENT-TABLE").batches

        assert batch1.available_quantity == 10
        assert batch2.available_quantity == 50

        messagebus.handle(events.BatchQuantityChanged("batch1", 25), uow)
        
        # Размещение заказов будет отменено, и у нас будет 25 - 30

        assert batch1.available_quantity == 5
        assert batch2.available_quantity == 30
