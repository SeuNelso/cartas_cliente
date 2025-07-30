from flask import Flask, render_template
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello World! Railway Test"

@app.route('/health')
def health():
    return "OK"

@app.route('/test')
def test():
    return "Test OK!"

@app.route('/debug')
def debug():
    return f"Port: {os.environ.get('PORT', '5000')}"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 