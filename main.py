from flask import Flask, request, jsonify
from flask_smorest import Api
import logging
import sys
import signal
import os
from swagger import configure_swagger_ui
from header_api import header_blp
from query_api import query_blp
from mirror_api import mirror_blp, db
from echo_api import echo_blp

logging.basicConfig()
logger = logging.getLogger('waitress')
logger.setLevel(logging.DEBUG)

DATABASE_DIR = "/data"
DATABASE_URL = f"sqlite:///{os.path.join(DATABASE_DIR, 'mirror_data.db')}"
if not os.path.exists(DATABASE_DIR):
    os.makedirs(DATABASE_DIR)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["API_TITLE"] = "Mirror Echo API"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.0.2"
app.config["OPENAPI_URL_PREFIX"] = "/swagger-ui"
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

api = Api(app)
api.register_blueprint(header_blp)
api.register_blueprint(query_blp)
api.register_blueprint(mirror_blp)
api.register_blueprint(echo_blp)

# --- 5. Swagger UI Configuration ---
configure_swagger_ui(app)

db.init_app(app)
with app.app_context():
    db.create_all()

def handle_sigterm(signal, frame):
    print("SIGTERM received. Shutting down gracefully...")
    print("Cleanup complete. Exiting.")
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_sigterm)

@app.route('/')
def info_page():
    return f"""
    <html>
    <body style="background-color:#121212; color:#e0e0e0; font-family:sans-serif;">
    <h3 style="color:#bb86fc;">Application Information</h3>
    <p><strong>OpenAPI URL:</strong> <a href="/swagger-ui" style="color:#BB86FC;">/swagger-ui</a></p>
    </body>
    </html>
    """

@app.route("/health", methods=["GET"])
def health():
    """Liveness Probe: prüft nur ob Flask läuft"""
    return jsonify(status="ok"), 200

@app.route("/ready", methods=["GET"])
def ready():
    """Readiness Probe: prüft zusätzlich DB-Verbindung"""
    try:
        with db.engine.connect() as conn:
            conn.execute("SELECT 1")
        return jsonify(status="ready"), 200
    except Exception as e:
        return jsonify(status="not ready", error=str(e)), 500

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=4500)
    #serve(TransLogger(app, setup_console_handler=True), host='0.0.0.0', port=4500, threads=2, expose_tracebacks=False)