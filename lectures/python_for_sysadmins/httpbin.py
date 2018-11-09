import json
from flask import Flask, request, Response

app = Flask(__name__)


@app.route('/')
def hello():
    return 'Hello, World!'


@app.route('/get')
def get_endpoint():
    resp = json.dumps({
        'headers': dict(request.headers),
        'params': request.values.to_dict(),
        'data': request.data.decode('utf-8'),
        'json': request.get_json()
    })
    return Response(resp)


@app.route('/post', methods=['POST'])
def post_endpoint():
    resp = json.dumps({
        'headers': dict(request.headers),
        'params': request.values.to_dict(),
        'data': request.data.decode('utf-8'),
        'json': request.get_json()
    })
    return Response(resp)


@app.route('/json', methods=['POST'])
def json_endpoint():
    resp = json.dumps({
        'headers': dict(request.headers),
        'params': request.values.to_dict(),
        'data': request.data.decode('utf-8'),
        'json': request.get_json()
    })
    return Response(resp)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)