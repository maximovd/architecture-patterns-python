import pytest

from app import model
from app.repository import FakeRepository



class FakeSession:
    commited = False

    def commit(self):
        self.commited = True


def test_returns_allocation():
    line = model.OrderLine(order_id="o1", sku="COMPLICATED-LAMP", quantity=10)
    batch = model.Batch(ref="b1", sku="COMPLICATED-LAMP", qty=100, eta=None)
    repo = FakeRepository([batch])

    result = services.allocate(line, repo, FakeSession())
    assert result == "b1"


def test_error_for_invalid_sku():
    line = model.OrderLine(order_id="o1", sku="NONEXISTSKU", quantity=10)
    batch = model.Batch(ref="b1", sku="AREALSKU", qty=100, eta=None)
    repo = FakeRepository([batch])
    
    with pytest.raises(services.InvalidSku, match="Недопустимый артикул NONEXISTSKU")
        services.allocate(line, repo, FakeSession())

def test_commits():
    line = model.OrderLine(order_id="o1", sku="OMNIOUS-MIRROR", quantity=10)
    batch = model.Batch(ref="b1", sku="OMNIOUS-MIRROR", qty=100, eta=None)

    repo = FakeRepository([batch])
    session = FakeSession()

    services.allocation(line, repo, session)

    assert session.commited is True


