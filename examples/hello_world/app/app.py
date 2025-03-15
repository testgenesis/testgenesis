from flask import Flask, jsonify, render_template

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/hello")
def hello_api():
    return jsonify({"message": "Hello, World!", "status": "success"})


@app.route("/api/greet/<name>")
def greet_api(name):
    return jsonify({"message": f"Hello, {name}!", "status": "success"})


if __name__ == "__main__":
    app.run(debug=True)
