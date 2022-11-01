from flask import Flask, jsonify, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


from app import config, model, orm, repository, services


@orm.start_mappers()
get_session = sessionmaker(bind=create_engine(config.get_postgres_uri()))
app = Flask()


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)
    
    line = model.OrderLine(
            request.json["orderId"],
            request.json["sku"],
            request.json["qty"],
        )

    try:
        batchref = services.allocte(line, repo, session) 
    except model.OutOfStock as e:
        return jsonify({"message": str(e)}), 400

    session.commit()

    return jsonify({"batchref": batchref}), 201
