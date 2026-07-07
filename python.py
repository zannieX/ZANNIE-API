from flask import Flask, request, jsonify
import time
import os

app = Flask(__name__)

# In-memory storage (use Redis/MongoDB in production)
BLOCKLIST = {}
RATE_LIMITS = {}

# Rate limiting config
MAX_ATTEMPTS = 3
TIME_WINDOW = 300  # 5 minutes

def is_rate_limited(phone):
    now = time.time()
    if phone not in RATE_LIMITS:
        RATE_LIMITS[phone] = []
    
    # Clean old entries
    RATE_LIMITS[phone] = [t for t in RATE_LIMITS[phone] if now - t < TIME_WINDOW]
    
    if len(RATE_LIMITS[phone]) >= MAX_ATTEMPTS:
        return True
    
    RATE_LIMITS[phone].append(now)
    return False

def add_to_blocklist(phone):
    BLOCKLIST[phone] = time.time() + 86400  # 24-hour ban

def is_blocked(phone):
    if phone not in BLOCKLIST:
        return False
    
    if time.time() > BLOCKLIST[phone]:
        del BLOCKLIST[phone]
        return False
    
    return True

def remove_from_blocklist(phone):
    if phone in BLOCKLIST:
        del BLOCKLIST[phone]

@app.route('/api/ban', methods=['POST'])
def ban():
    data = request.json
    phone = data.get('phone')
    
    if not phone:
        return jsonify({"error": "Phone number required"}), 400
    
    if is_blocked(phone):
        return jsonify({"message": "Already blocked"}), 400
    
    add_to_blocklist(phone)
    return jsonify({"message": f"Blocked {phone}"})

@app.route('/api/unban', methods=['POST'])
def unban():
    data = request.json
    phone = data.get('phone')
    
    if not phone:
        return jsonify({"error": "Phone number required"}), 400
    
    if not is_blocked(phone):
        return jsonify({"message": "Not blocked"}), 400
    
    remove_from_blocklist(phone)
    return jsonify({"message": f"Unblocked {phone}"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)