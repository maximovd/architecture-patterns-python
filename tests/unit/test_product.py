from app.domain import events
from app.domain.model import Batch, OrderLine, Product


def test_records_out_of_stock_event_cannot_allocate():
    batch = Batch(ref="batch1", sku="SMALL-FORK", qty=10, eta=today)
    product = Product(sku="SMALL-FORK", batches=[batch])

    product.allocate(OrderLine(order_id="orderl", sku="SMALL-FORK", quantity=10))

    allocation = product.allocate(OrderLine(order_id="order2", sku="SMALL-FORK", quantity=1))

    assert product.events[-1] == events.OutOfStock(sku="SMALL-FORK")
    assert allocation is None

