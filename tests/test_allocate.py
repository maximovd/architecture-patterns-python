from datetime import date, timedelta
from tkinter import W

import pytest

from app.model import Batch, OrderLine, allocate

tommorrow = date.today() + timedelta(days=1)

class TestBatchesAllocated:
    def test_prefers_current_in_stock_batches_to_shipment(self):
        in_stock_batch = Batch(ref="in-stock-batch", sku="RETRO-CLOCK", qty=100, eta=None)
        shipment_batch = Batch(ref="in-stock-batch", sku="RETRO-CLOCK", qty=100, eta=tommorrow)
        
        line = OrderLine(order_id="order1", sku="RETRO-CLOCK", quantity=20)

        allocate(line, [in_stock_batch, shipment_batch])

        assert in_stock_batch.available_quantity == 80
        assert shipment_batch.available_quantity == 100
        
    def test_prefers_earler_batches(self):
        earliest = Batch(ref="in-stock-batch", sku="RETRO-CLOCK", qty=100, eta=date.today())
        medium = Batch(ref="in-stock-batch", sku="RETRO-CLOCK", qty=100, eta=tommorrow)
        latest = Batch(ref="in-stock-batch", sku="RETRO-CLOCK", qty=100, eta=tommorrow + timedelta(days=1))
        
        line = OrderLine(order_id="order1", sku="RETRO-CLOCK", quantity=20)

        allocate(line, [earliest, medium, latest])

        assert earliest.available_quantity == 80
        assert medium.available_quantity == 100
        assert latest.available_quantity == 100
    
    def test_return_allocated_batch_ref(self):
        in_stock_batch = Batch(ref="in-stock-batch", sku="RETRO-CLOCK", qty=100, eta=None)
        shipment_batch = Batch(ref="in-stock-batch", sku="RETRO-CLOCK", qty=100, eta=tommorrow)
        
        line = OrderLine(order_id="order1", sku="RETRO-CLOCK", quantity=20)

        assert allocate(line, [in_stock_batch, shipment_batch]) == in_stock_batch.reference
