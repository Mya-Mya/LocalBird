import io
from pathlib import Path
from argparse import ArgumentParser
from flask import Flask, jsonify, send_file, abort, render_template, request
from PIL import Image
from metarepository import MetaRepository
import json
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from gc import collect
import requests

app = Flask(__name__)
app.json.ensure_ascii = False # 日本語のまま返却するように

repo = MetaRepository()
IMAGE_BASE_DIR = Path("./Images")
THUMBNAIL_BASE_DIR = Path("./Thumbnails")

def get_post_data(postid: str|int):
    data = repo.get(int(postid))
    if not data:
        return None
    return {
        "postid": str(data[0]),
        "username": data[1],
        "userid": data[2],
        "textcontent": data[3],
        "timestamp": data[4]
    }

def get_image_file_path(userid:str, postid:str, index:int):
    """画像ファイルのパスを構築する"""
    return IMAGE_BASE_DIR / str(userid) / f"{postid}.{index}.png"

def count_images(userid:str, postid:int):
    user_dir = IMAGE_BASE_DIR / str(userid)
    if not user_dir.exists():
        return 0
    return len(list(user_dir.glob(f"{postid}.*.png")))

def upgrade_image_url(url: str) -> str:
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    query_params["format"] = ["png"]
    query_params["name"] = ["4096x4096"]
    new_query = urlencode(query_params, doseq=True)
    return urlunparse(
        (parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment)
    )

def download_image(url: str, dst: Path, skip_if_exists: bool = True):
    if dst.exists() and skip_if_exists:
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    temp = dst.with_suffix(dst.suffix + ".temp")

    result = requests.get(url, stream=True)
    result.raise_for_status()
    with open(temp, "wb") as file:
        for chunk in result.iter_content(1024):
            file.write(chunk)
    temp.replace(dst)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/detail/<int:postid>', methods=['GET'])
def get_detail(postid:int):
    data = get_post_data(postid)
    if not data:
        abort(404, description="Post not found")

    data["image_count"] = count_images(data["userid"], postid)
    return jsonify(data)

@app.route('/detail/all', methods=['GET'])
def get_all_details():
    postids = repo.list()
    results = []
    for pid in postids:
        data = get_post_data(pid)
        if data:
            data["image_count"] = count_images(data["userid"], pid)
            results.append(data)
    return jsonify(results)

@app.route('/image/full/<int:postid>/<int:index>', methods=['GET'])
def get_full_image(postid:str, index:int):
    data = get_post_data(postid)
    if not data:
        abort(404)

    img_path = get_image_file_path(data["userid"], postid, index)
    if not img_path.exists():
        abort(404)
    return send_file(img_path, mimetype='image/png')

@app.route('/image/thumbnail/<int:postid>/<int:index>')
def get_thumbnail_image(postid:str, index:int):
    data = get_post_data(postid)
    if not data:
        abort(404)

    userid = data["userid"]
    original_path = IMAGE_BASE_DIR / str(userid) / f"{postid}.{index}.png"
    thumb_path = THUMBNAIL_BASE_DIR / str(userid) / f"{postid}.{index}.png"

    # 1. キャッシュ(サムネイル)が既に存在するか確認
    if thumb_path.exists():
        return send_file(thumb_path, mimetype='image/png')

    # 2. 元画像が存在するか確認
    if not original_path.exists():
        abort(404)

    # 3. サムネイルの生成と保存
    try:
        # 保存先ディレクトリの作成 (Thumbnails/<userid>/)
        thumb_path.parent.mkdir(parents=True, exist_ok=True)

        with Image.open(original_path) as img:
            img.thumbnail((200, 200))
            # 最適化して保存
            img.save(thumb_path, 'PNG', optimize=True)
        collect()
        return send_file(thumb_path, mimetype='image/png')

    except Exception as e:
        app.logger.error(f"Thumbnail creation failed: {e}")
        abort(500)

@app.route('/post-xpostinfo', methods=['POST'])
def post_xpostinfo():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        # JSONを読み込み
        content = file.read().decode('utf-8')
        xpostinfo = json.loads(content)
        print(xpostinfo)

        # メタデータの保存
        repo.insert(
            postid=int(xpostinfo["postid"]),
            username=xpostinfo["username"],
            userid=xpostinfo["userid"],
            textcontent=xpostinfo["text"],
            timestamp=xpostinfo["datetime"],
            overwrite=True # 必要に応じて
        )

        # 画像のダウンロード
        dst_parent = IMAGE_BASE_DIR / str(xpostinfo["userid"])
        for i, imgsrc in enumerate(xpostinfo["imgsrcs"]):
            dst = dst_parent / f"{xpostinfo['postid']}.{i}.png"
            upgraded_url = upgrade_image_url(imgsrc)
            download_image(upgraded_url, dst)

        return jsonify({"message": f"Successfully imported post {xpostinfo['postid']}"}), 200

    except Exception as e:
        app.logger.error(f"Import failed: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # サーバーの起動
    parser = ArgumentParser("LocalBird Server")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    app.run(host="0.0.0.0", debug=False, port=int(args.port))

