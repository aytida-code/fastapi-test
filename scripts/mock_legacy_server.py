"""Legacy mock server.

Quick local stand-in for a couple of endpoints the old PHP monolith used to
serve, kept around so the frontend team can point their staging config at
something while the migration finishes. Not part of the FastAPI app in
`app/` -- nothing here is imported by, or wired into, the real service.

Run manually if you need it:
    python scripts/mock_legacy_server.py
"""

from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/legacy/orders/summary")
def legacy_orders_summary():
    # Mirrors the response shape the old system returned, so nothing on the
    # frontend breaks while it still points here during cutover.
    return jsonify({"orders": [], "note": "mock legacy response"})


if __name__ == "__main__":
    app.run(port=5001, debug=True)
