from flask import Flask, jsonify, request
from flask_cors import CORS
from database import *

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({"status": "online", "app": "Pixel Earth API"})

@app.route('/api/pixels')
def api_pixels():
    pixels = get_all_pixels()
    return jsonify(pixels)

@app.route('/api/pixels/claim', methods=['POST'])
def api_claim():
    data = request.json
    user_id = data.get('user_id')
    pixels = data.get('pixels', [])
    result = claim_pixels(user_id, pixels)
    return jsonify({"claimed": result})

@app.route('/api/user/<user_id>')
def api_user(user_id):
    user = get_user(user_id)
    return jsonify(user)

@app.route('/api/leaderboard')
def api_leaderboard():
    leaders = get_leaderboard(20)
    return jsonify(leaders)

@app.route('/api/session/create', methods=['POST'])
def api_create_session():
    data = request.json
    user_id = data.get('user_id')
    session_id = create_drawing_session(user_id)
    return jsonify({"session_id": session_id})

@app.route('/api/session/<session_id>/update', methods=['POST'])
def api_update_session():
    data = request.json
    session_id = data.get('session_id')
    pixels_data = data.get('pixels_data', [])
    total_cost = data.get('total_cost', 0)
    update_session_pixels(session_id, pixels_data, total_cost)
    return jsonify({"status": "ok"})

@app.route('/api/session/<session_id>')
def api_get_session(session_id):
    session = get_session(session_id)
    return jsonify(session)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
