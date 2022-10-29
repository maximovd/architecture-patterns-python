from datetime import date
from re import L

import pytest

from app.model import Batch, OrderLine


def make_batch_and_line(
    batch_sku: str,
    batch_qty: int,
    line_sku: str,
    line_qty: int,
    ) -> tuple[Batch, OrderLine]:

    return (
        Batch(ref="batch-001", sku=batch_sku, qty=batch_qty, eta=date.today()),
        OrderLine(sku=line_sku, order_id="test-ref", quantity=line_qty)
    )

class TestBatchAllocating:
    def test_allocating_to_a_batch_reduces_the_available_qty_success(self):
        sku = "SMALL-TABLE"
        batch, order_line = make_batch_and_line(batch_sku=sku, line_sku=sku, batch_qty=12, line_qty=2)

        batch.allocate(line=order_line)

        assert batch.available_quantity == 10
    
    def test_allocations_is_idempotent(self):
        sku = "ANGULAR-DESK"
        batch, line = make_batch_and_line(batch_sku=sku, line_sku=sku, batch_qty=12, line_qty=2)
        batch.allocate(line)
        batch.allocate(line)

        assert batch.available_quantity == 10


class TestBatchCanAllocating:
    # TODO: Переписать на parametrize
    def test_can_allocate_if_available_greater_than_required(self):
        sku = "ELEGANT-LAMP"
        batch, small_line = make_batch_and_line(batch_sku=sku, line_sku=sku, batch_qty=20, line_qty=2)
        
        assert batch.can_allocate(line=small_line)
        
    def test_cannot_allocate_if_available_smaller_than_required(self):
        sku = "ELEGANT-LAMP"
        batch, greater_line = make_batch_and_line(batch_sku=sku, line_sku=sku, batch_qty=2, line_qty=20)
        
        assert batch.can_allocate(line=greater_line) is False
    
    def test_can_allocate_if_available_equal_than_required(self):
        sku = "ELEGANT-LAMP"
        batch, equal_line = make_batch_and_line(batch_sku=sku, line_sku=sku, batch_qty=2, line_qty=2)
        
        assert batch.can_allocate(line=equal_line)
    
    def test_cannot_allocate_if_skus_do_not_match(self):
        batch, diff_sku_line = make_batch_and_line(
            batch_sku="ELEGANT-LAMP", 
            line_sku="ANOTHER-ELEGANT-LAMP",
            batch_qty=20,
            line_qty=2,
            )
        
        assert batch.can_allocate(line=diff_sku_line) is False


class TestBatchDeallocating:
    def test_can_only_deallocate_allocated_lines(self):
        sku = "ELEGANT-LAMP"
        available_qty = 20
        batch, unallocated_line = make_batch_and_line(
            batch_sku=sku,
            line_sku=sku,
            batch_qty=available_qty,
            line_qty=2,
            )

        batch.deallocate(unallocated_line)

        assert batch.available_quantity == 20
        
    