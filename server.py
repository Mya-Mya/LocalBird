from typing import Optional
from flask import Flask, render_template, make_response, jsonify, Response, send_file
from pathlib import Path
from json import loads
from localbirddatas import LocalBirdDatas

app = Flask(import_name=__file__, static_url_path="/localbird")


@app.get("/")
def get_():
    return send_file("./front.html")


LBDATA_DIR = Path("./Data")
repository = LocalBirdDatas(LBDATA_DIR)


@app.post("/users")
def run_post_users():
    return jsonify(repository.list_userid())


@app.post("/<string:userid>")
def run_post_user(userid: str):
    userindex = repository.get_userindex(userid)
    if userindex is None:
        return make_response(f"User with id {userid} not found.", 404)
    return jsonify(userindex)


@app.route("/<string:userid>/<string:postid>/<int:mediaidx>", methods=["GET", "POST"])
def get_user_tweet_media(userid: str, postid: str, mediaidx: int):
    fp = repository.get_mediafp(userid, postid, mediaidx)
    if not fp.exists():
        return make_response(f"Media with id {userid} not found.", 404)
    return send_file(fp, mimetype="image/png")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3838, debug=False)
