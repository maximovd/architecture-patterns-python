import typing
from datetime import date
from dataclasses import dataclass

from app.domain import events


@dataclass(frozen=True)
class OrderLine:
    order_id: str
    sku: str
    quantity: int


class OutOfStock(Exception):
    """Out of Stock batch error."""


class Batch:
    def __init__(self, ref: str, qty: int, sku: str, eta: date | None) -> None:
        self.reference = ref
        self.sku = sku
        self.eta = eta
        self._purchased_quantity = qty
        self._allocations: set[OrderLine] = set()
    
    def __eq__(self, other: "Batch") -> bool:
        if not isinstance(other, Batch):
            return False
        return other.reference == self.reference
    
    def __gt__(self, other: "Batch") -> bool:
        if self.eta is None:
            return False
        if other.eta is None:
            return True
        return self.eta > other.eta
    
    def __hash__(self) -> int:
        return hash(self.reference)

    def allocate(self, line: OrderLine) -> None:
        if self.can_allocate(line):
            self._allocations.add(line)
    
    def deallocate(self, line: OrderLine) -> None:
        if line in self._allocations:
            self._allocations.remove(line)

    def deallocate_one(self) -> OrderLine:
        return self._allocations.pop()

    def can_allocate(self, line: OrderLine) -> bool:
        return self.sku == line.sku and self.available_quantity >= line.quantity
    
    @property
    def allocated_quantity(self) -> int:
        return sum(line.quantity for line in self._allocations)

    @property
    def available_quantity(self) -> int:
       return self._purchased_quantity - self.allocated_quantity


def allocate(line: OrderLine, batches: list[Batch]) -> str:
    try:
        batch = next(b for b in sorted(batches) if b.can_allocate(line))
    except StopIteration:
        raise OutOfStock(f"Article {line.sku} out of stock from batch")

    batch.allocate(line) 
    return batch.reference
    


class Product:
    """
    Агрегат для работы с позциями заказа.
     - Главным id продукта является sku
     - Класс содержит ссылку на коллекцию партий `batches`
    """

    def __init__(self, sku: str, batches: list[Batch], version_number: int = 0) -> None:
        self.sku = sku
        self.batches = batches
        self.version_number = version_number
        self.events: list[events.Event] = []

    def allocate(self, line: OrderLine) -> str | None:
        """Резревирование товара в партии."""
        try:
            batch = next(b for b in sorted(self.batches) if b.can_allocate(line))
            batch.allocate(line)
            self.version_number += 1
            return batch.reference
        except StopIteration:
            self.events.append(events.OutOfStock(line.sku))
            return None

    def change_batch_quantity(self, ref: str, qty: int):
        batch = next(b for b in self.batches if b.reference == ref)
        batch._purchased_quantity = qty

        while batch.available_quantity < 0:
            line = batch.deallocate_one()
            self.events.append(events.AllocationRequired(line.order_id, line.sku, line.qty))

