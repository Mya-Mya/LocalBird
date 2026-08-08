from argparse import ArgumentParser
from flask import Flask, jsonify, send_file, abort, render_template, request
import json
from repository import *
import postimporter

app = Flask(__name__)

repo = Repository()


@app.route("/")
def index():
    # Read Arguments
    limit = request.args.get("limit", 50, type=int)
    page = request.args.get("page", 1, type=int)
    offset = (page - 1) * limit
    # Get Data
    filenames = repo.list(limit=limit, offset=offset)
    return render_template("list.html", filenames=filenames, page=page)


@app.get("/detail/<string:filename>")
def get_detail(filename: str):
    ai = repo.get_image(filename)
    meta = ai.meta
    return render_template(
        "detail.html",
        filename=filename,
        id=meta.id,
        author_name=meta.author_name,
        author_id=meta.author_id,
        text=meta.text,
        created_at=meta.created_at,
    )


@app.get("/image/thumbnail/<string:filename>")
def get_thumbnail(filename: str):
    repo.prepare_thumbnail(filename)
    return send_file(repo.get_thumbnail_path(filename))


@app.get("/image/full/<string:filename>")
def get_full(filename: str):
    return send_file(repo.get_image_path(filename))


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


@app.post("/delete/<string:filename>")
def delete_post(filename: str):
    repo.delete(filename)
    return jsonify({"message": f"Deleted image {filename}"}), 200


if __name__ == "__main__":
    # サーバーの起動
    parser = ArgumentParser("LocalBird Server")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    app.run(host="0.0.0.0", debug=False, port=int(args.port))
