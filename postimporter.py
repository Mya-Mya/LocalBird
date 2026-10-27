import json
from io import BytesIO
from urllib.parse import parse_qs, urlencode, urlunparse, urlparse
import requests
from dataclasses import dataclass, field
from repository import *


@dataclass
class Post:
    meta: Meta = field(default_factory=Meta)
    image_srcs: list[str] = field(default_factory=list)

    @staticmethod
    def from_dict(d: dict):
        return Post(meta=Meta.from_dict(d["meta"]), image_srcs=d["image_srcs"])

    @staticmethod
    def from_json(json_text: str):
        return Post.from_dict(json.loads(json_text))

    def to_dict(self):
        return {"meta": self.meta.to_dict(), "image_srcs": self.image_srcs}


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


def fetch_image(url: str):
    result = requests.get(url)
    image = Image.open(BytesIO(result.content))
    return image


def add_images_by_post(repo: Repository, post: Post) -> list[str]:
    images = []
    for src in post.image_srcs:
        url = upgrade_image_url(src)
        image = fetch_image(url)
        images.append(image)
    filenames = repo.add_images(images, post.meta)
    return filenames


def open_local_image(file) -> Image.Image:
    """パス or ファイルオブジェクトから画像を開き，PNG保存可能な形式にする"""
    image = Image.open(file)
    image.load()
    if image.mode not in ("RGB", "RGBA", "L", "LA", "P"):
        image = image.convert("RGBA")
    return image


def add_images_by_files(repo: Repository, meta: Meta, files: list) -> list[str]:
    """手動で用意した画像ファイルとメタデータを登録する"""
    if not meta.id:
        raise ValueError("The id is required")
    if not files:
        raise ValueError("No images")
    images = [open_local_image(file) for file in files]
    return repo.add_images(images, meta)
