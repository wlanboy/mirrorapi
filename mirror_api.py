from flask_sqlalchemy import SQLAlchemy
from flask import request, jsonify, make_response
from flask_smorest import Blueprint
from swagger import MirrorSaveSchema, MirrorDeleteSchema
import json

mirror_blp = Blueprint(
    "mirror", __name__, url_prefix="/mirror", description="Manages and serves mirrored request/response pairs."
)

db = SQLAlchemy()

class MirrorPair(db.Model):
    __tablename__ = 'mirror_pairs'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    request_hash = db.Column(db.String, unique=True, nullable=False)
    request_data = db.Column(db.Text, nullable=False)
    response_data = db.Column(db.Text, nullable=False)
    response_status = db.Column(db.Integer, nullable=False)

def hash_request(request_data):
    """Generates a consistent hash from the request body."""
    if request_data is None:
        return "None"
    return json.dumps(request_data, sort_keys=True)

@mirror_blp.route("/save", methods=["POST"])
@mirror_blp.arguments(MirrorSaveSchema)
@mirror_blp.response(201, description="Request/Response pair saved successfully.")
@mirror_blp.response(409, description="A pair with this request already exists.")
def mirror_save(data):
    request_data = data["request"]["request_data"]
    response_data = data["response"]["response_data"]
    response_status = data["response"]["response_status"]
    request_hash = hash_request(request_data)

    try:
        pair = MirrorPair(
            request_hash=request_hash,
            request_data=json.dumps(request_data),
            response_data=json.dumps(response_data),
            response_status=response_status
        )
        db.session.add(pair)
        db.session.commit()
        return {"message": "Request/Response pair saved."}, 201
    except Exception as e:
        db.session.rollback()
        if 'UNIQUE constraint' in str(e):
            return {"error": "A pair with this request already exists."}, 409
        return {"error": str(e)}, 500

@mirror_blp.route("/delete", methods=["POST"])
@mirror_blp.doc(requestBody={"content": {"application/json": {"schema": {}}}})
@mirror_blp.response(200, description="Pair deleted successfully.")
@mirror_blp.response(404, description="Pair not found.")
def mirror_delete():
    try:
        request_data = request.get_json(silent=True)
        if request_data is None:
            return {"error": "Request body cannot be empty."}, 400
    except Exception:
        return {"error": "Invalid JSON in request body."}, 400
    
    # Manuelle Verarbeitung des Request-Bodys
    request_hash = hash_request(request_data)

    pair = MirrorPair.query.filter_by(request_hash=request_hash).first()
    if not pair:
        return {"error": "No matching pair found to delete."}, 404
    db.session.delete(pair)
    db.session.commit()
    return {"message": "Pair deleted successfully."}, 200

@mirror_blp.route("/", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@mirror_blp.doc(requestBody={"content": {"application/json": {"schema": {}}}})
@mirror_blp.response(200, description="Matching response found.", schema={})
@mirror_blp.response(404, description="No matching response found.")
def mirror_lookup():
    try:
        request_data = request.get_json(silent=True)
        if request_data is None:
            request_data = request.get_data(as_text=True)
    except Exception:
        request_data = request.get_data(as_text=True)

    if not request_data:
        request_data = ""

    request_hash = hash_request(request_data)

    pair = MirrorPair.query.filter_by(request_hash=request_hash).first()
    if not pair:
        return {"error": "No mirrored response found for this request."}, 404
    response_data = json.loads(pair.response_data)
    response_status = pair.response_status
    response = make_response(jsonify(response_data), response_status)
    return response