from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def home():
    image_url = "https://i.scdn.co/image/ab67616d0000b273c56dcd1015c1ffb8c56d2988"
    return render_template("index.html", image_url=image_url)

if __name__ == "__main__":
    app.run(debug=True)