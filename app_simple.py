from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def root():
    return "OK"

@app.route('/ping')
def ping():
    return "pong"

@app.route('/health')
def health():
    return "healthy"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 