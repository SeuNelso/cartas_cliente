from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def home():
    print("🔍 Health check request received!")
    return "Hello World!"

@app.route('/health')
def health():
    print("🔍 Health endpoint called!")
    return "OK"

@app.route('/ping')
def ping():
    print("🔍 Ping endpoint called!")
    return "pong"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True) 