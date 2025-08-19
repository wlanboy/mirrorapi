import sqlite3
import json
from flask import request, jsonify, make_response
from flask_smorest import Blueprint
from swagger import MirrorSaveSchema, MirrorDeleteSchema

mirror_blp = Blueprint(
    "mirror", __name__, url_prefix="/mirror", description="Manages and serves mirrored request/response pairs."
)

DB_PATH = "mirror_data.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_mirror_table():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mirror_pairs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_hash TEXT UNIQUE,
            request_data TEXT,
            response_data TEXT,
            response_status INTEGER
        )
    """)
    conn.commit()
    conn.close()

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

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO mirror_pairs (request_hash, request_data, response_data, response_status) VALUES (?, ?, ?, ?)",
            (request_hash, json.dumps(request_data), json.dumps(response_data), response_status)
        )
        conn.commit()
        return {"message": "Request/Response pair saved."}, 201
    except sqlite3.IntegrityError:
        return {"error": "A pair with this request already exists."}, 409
    finally:
        conn.close()

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

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM mirror_pairs WHERE request_hash = ?", (request_hash,))
    conn.commit()
    rows_deleted = cursor.rowcount
    conn.close()

    if rows_deleted == 0:
        return {"error": "No matching pair found to delete."}, 404
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

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT response_data, response_status FROM mirror_pairs WHERE request_hash = ?", (request_hash,))
    result = cursor.fetchone()
    conn.close()

    if not result:
        return {"error": "No mirrored response found for this request."}, 404
    
    response_data = json.loads(result['response_data'])
    response_status = result['response_status']

    response = make_response(jsonify(response_data), response_status)
    return response