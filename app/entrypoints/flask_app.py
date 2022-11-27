import datetime

from flask import Flask, jsonify, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


from app import config  # TODO: добавить конфиг файл
from app.service_layer import messagebus, services, unit_of_work
from app.adapters import orm, repository
from app.domain import events, model


@orm.start_mappers()
get_session = sessionmaker(bind=create_engine(config.get_postgres_uri()))
app = Flask()


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    try:
        event = events.AllocationRequired(
                request.json["orderid"],
                request.json["sku"],
                request.json["qty"],
            )
        results = messagebus.handle(event, unit_of_work.SqlAlchemyUnitOfWork())

        batchref = results.pop(0)
    except InvaildSku as e:
        pass  # TODO: Добавить обрбаботку


@app.route("/add_batch", methods=["POST"])
def add_batch():
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)

    eta = request.json("eta")
    if eta is not None:
        eta = datetime.datetime.fromisoformat(eta).date()
    
    services.add_batch(request.json["ref"], request.json["sku"], request.json["qty"], eta, repo, session)
    return "OK", 201

