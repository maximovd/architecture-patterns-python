import pytest

import requests


@pytest.mark.usefixtures("restart-api")
def test_happy_path_returns_201_and_allocated_batch(add_stock):
    sku, othersku = random_sku(), random_sku("other")
    earlybatch = random_batchref(1)
    laterbatch = random_batchref(2)
    otherbatch = random_batchref(3)

    add_stock([
        (laterbatch, sku, 100, "2022-01-02"),
        (earlybatch, sku, 100, "2022-01-01"),
        (otherbatch, othersku, 100, None),
    ])

    data = {"orderid": random_orderid(), "sku": sku, "qty": 3}
    url = config.get_api_url()
    r = requests.post(f"{url}/allocate", json=data)

    assert r.status_code == 201
    assert r.json()["batchref"] == earlybatch


@pytest.mark.usefixtures("restart-api")
def test_happy_path_returns_201_and_allocated_batch(add_stock):
    unknown_sku, orderid = random_sku(), random_orderid() 

    data = {"orderid": orderid, "sku": unknown_sku, "qty": 3}
    url = config.get_api_url()
    r = requests.post(f"{url}/allocate", json=data)

    assert r.status_code == 400
    assert r.json()["message"] == f"Недопустимый артикул {unknown_sku}" 
