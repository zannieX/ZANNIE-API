from flask import Flask, request, jsonify
import os
from redis import Redis

app = Flask(__name__)

# Connect to Redis using an environment variable from Vercel dashboard
# Example URL: rediss://default:password@your-redis-host:port
redis_url = os.environ.get("REDIS_URL")
db = Redis.from_url(redis_url, decode_responses=True) if redis_url else None

# Rate limiting config
MAX_ATTEMPTS = 3
TIME_WINDOW = 300  # 5 minutes

def is_rate_limited(phone):
    if not db: 
        return False
    
    key = f"rate:{phone}"
    # Use Redis pipeline to increment and set expiration safely
    pipe = db.pipeline()
    pipe.incr(key)
    pipe.expire(key, TIME_WINDOW, nx=True)
    current_attempts, _ = pipe.execute()
    
    return int(current_attempts) > MAX_ATTEMPTS

def add_to_blocklist(phone):
    if db:
        # Automatically deletes itself after 24 hours (86400 seconds)
        db.setex(f"block:{phone}", 86400, "banned")

def is_blocked(phone):
    if not db: 
        return False
    return db.exists(f"block:{phone}") > 0

def remove_from_blocklist(phone):
    if db:
        db.delete(f"block:{phone}")

@app.route('/api/ban', methods=['POST'])
def ban():
    data = request.json or {}
    phone = data.get('phone')
    
    if not phone:
        return jsonify({"error": "Phone number required"}), 400
    
    if not db:
        return jsonify({"error": "Database connection missing"}), 500
    
    if is_blocked(phone):
        return jsonify({"message": "Already blocked"}), 400
    
    add_to_blocklist(phone)
    return jsonify({"message": f"Blocked {phone}"})

@app.route('/api/unban', methods=['POST'])
def unban():
    data = request.json or {}
    phone = data.get('phone')
    
    if not phone:
        return jsonify({"error": "Phone number required"}), 400
    
    if not db:
        return jsonify({"error": "Database connection missing"}), 500
    
    if not is_blocked(phone):
        return jsonify({"message": "Not blocked"}), 400
    
    remove_from_blocklist(phone)
    return jsonify({"message": f"Unblocked {phone}"})
