#!/usr/bin/env python3

from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello World!"

@app.route('/health')
def health():
    return "OK"

@app.route('/test')
def test():
    return "Test OK!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True) 