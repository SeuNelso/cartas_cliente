from flask import Flask

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
    return "Debug OK!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080) 