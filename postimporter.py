import json
import logging
from argparse import ArgumentParser
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlunparse, urlparse
import requests

# 既存の MetaRepository クラスをインポート
from metarepository import MetaRepository

# ログの設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

IMAGE_BASE_DIR = Path("./Images")


def upgrade_image_url(url: str) -> str:
    """画像のURLを高画質化(PNG/4096x4096)する"""
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    query_params["format"] = ["png"]
    query_params["name"] = ["4096x4096"]
    new_query = urlencode(query_params, doseq=True)
    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment,
        )
    )


def download_image(url: str, dst: Path, skip_if_exists: bool = True):
    """画像をダウンロードして保存する"""
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


def process_single_json(xpostinfo: dict, repo: MetaRepository) -> bool:
    """1つのXPostInfoを解析し、DB登録と画像ダウンロードを行う"""
    postid = int(xpostinfo["postid"])
    userid = xpostinfo["userid"]
    try:
        # メタデータの保存
        repo.insert(
            postid=postid,
            username=xpostinfo["username"],
            userid=userid,
            textcontent=xpostinfo["text"],
            timestamp=xpostinfo["datetime"],
            overwrite=True,
        )

        # 画像のダウンロード
        dst_parent = IMAGE_BASE_DIR / str(userid)
        for i, imgsrc in enumerate(xpostinfo.get("imgsrcs", [])):
            dst = dst_parent / f"{postid}.{i}.png"
            upgraded_url = upgrade_image_url(imgsrc)
            download_image(upgraded_url, dst)

        logger.info(f"Successfully imported post {postid}")
        return True

    except Exception as e:
        logger.error(f"Failed to import {postid}: {e}")
        return False


def main():
    parser = ArgumentParser(description="XPostInfo.json 一括取り込みツール")
    parser.add_argument(
        "directory",
        type=str,
        help="XPostInfo.json ファイルが複数格納されているディレクトリのパス",
    )
    args = parser.parse_args()

    target_dir = Path(args.directory)
    if not target_dir.is_dir():
        logger.error(f"指定されたパスはディレクトリではありません: {target_dir}")
        return

    # リポジトリの初期化
    repo = MetaRepository()

    # ディレクトリ内の拡張子 .json ファイルを全検索
    json_files = list(target_dir.glob("*.json"))
    if not json_files:
        logger.warning(
            f"ディレクトリ内に JSON ファイルが見つかりませんでした: {target_dir}"
        )
        return

    logger.info(f"{len(json_files)} 個の JSON ファイルの処理を開始します...")

    success_count = 0
    n_json_files = len(json_files)
    for i, json_path in enumerate(json_files):
        print(f"{i:02d}", "/", n_json_files, end="\r")
        xpostinfo = json.loads(json_path.read_text(encoding="utf-8"))
        if process_single_json(xpostinfo, repo):
            success_count += 1
    print()
    logger.info(f"処理完了: 成功 {success_count} / 全体 {len(json_files)}")


if __name__ == "__main__":
    main()
