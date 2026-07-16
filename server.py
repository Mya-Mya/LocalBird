from argparse import ArgumentParser
from flask import Flask, jsonify, send_file, abort, render_template, request
from metarepository import MetaRepository
from imagerepository import ImageRepository
import json
import postimporter

app = Flask(__name__)

meta_repo = MetaRepository()
image_repo = ImageRepository()


def get_post_data(postid: str | int):
    data = meta_repo.get(int(postid))
    if not data:
        return None
    return {
        "postid": str(data[0]),
        "username": data[1],
        "userid": data[2],
        "textcontent": data[3],
        "timestamp": data[4],
    }


@app.route("/")
def index():
    # Read Arguments
    limit = request.args.get("limit", 50, type=int)
    page = request.args.get("page", 1, type=int)
    offset = (page - 1) * limit
    # Get Data
    postids = meta_repo.list(limit=limit, offset=offset)
    posts = []
    for pid in postids:
        post = get_post_data(pid)
        if post:
            img_count = image_repo.count_images(post["userid"], pid)
            post["images"] = list(range(img_count))
            posts.append(post)
    return render_template("index.html", posts=posts, page=page, limit=limit)


@app.route("/image/full/<int:postid>/<int:index>", methods=["GET"])
def get_full_image(postid: str, index: int):
    data = get_post_data(postid)
    if not data:
        abort(404)

    img_path = image_repo.get_full_image_path(data["userid"], postid, index)
    if not img_path:
        abort(404)
    return send_file(img_path, mimetype="image/png")


@app.route("/image/thumbnail/<int:postid>/<int:index>")
def get_thumbnail_image(postid: str, index: int):
    data = get_post_data(postid)
    if not data:
        abort(404)

    try:
        thumbnail_path = image_repo.get_or_create_thumbnail_path(
            data["userid"], postid, index
        )
        if not thumbnail_path:
            abort(404)
        return send_file(thumbnail_path, mimetype="image/png")
    except Exception as e:
        app.logger.error(f"Thumbnail error: {e}")
        abort(500)


@app.route("/post-xpostinfo", methods=["POST"])
def post_xpostinfo():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    try:
        # JSONを読み込み
        content = file.read().decode("utf-8")
        xpostinfo = json.loads(content)
        postimporter.process_single_json(xpostinfo, meta_repo)
        return (
            jsonify({"message": f"Successfully imported post {xpostinfo['postid']}"}),
            200,
        )

    except Exception as e:
        app.logger.error(f"Import failed: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # サーバーの起動
    parser = ArgumentParser("LocalBird Server")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    app.run(host="0.0.0.0", debug=False, port=int(args.port))
