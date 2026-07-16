from pathlib import Path
from PIL import Image
from gc import collect


class ImageRepository:
    def __init__(
        self,
        image_dir: Path = Path("./Images"),
        thumbnail_dir: Path = Path("./Thumbnails"),
    ) -> None:
        self.image_dir = image_dir
        self.thumbnail_dir = thumbnail_dir

    def _get_image_path(self, userid: int | str, postid: int | str, index: int) -> Path:
        """元画像のファイルパスを内部的に解決する"""
        return self.image_dir / str(userid) / f"{postid}.{index}.png"

    def _get_thumbnail_path(
        self, userid: int | str, postid: int | str, index: int
    ) -> Path:
        """サムネイルのファイルパスを内部的に解決する"""
        return self.thumbnail_dir / str(userid) / f"{postid}.{index}.png"

    def count_images(self, userid: int | str, postid: int | str) -> int:
        """指定された投稿に紐づく画像の枚数をカウントする"""
        user_dir = self.image_dir / str(userid)
        if not user_dir.exists():
            return 0
        return len(list(user_dir.glob(f"{postid}.*.png")))

    def get_full_image_path(
        self, userid: int | str, postid: int | str, index: int
    ) -> Path | None:
        """フルサイズ画像のパスを取得する（存在しない場合はNone）"""
        path = self._get_image_path(userid, postid, index)
        return path if path.exists() else None

    def get_or_create_thumbnail_path(
        self, userid: int | str, postid: int | str, index: int
    ) -> Path | None:
        """
        サムネイル画像のパスを取得する。
        キャッシュが存在しない場合は自動で生成してからパスを返す。
        元画像自体が存在しない場合は None を返す。
        """
        thumb_path = self._get_thumbnail_path(userid, postid, index)
        if thumb_path.exists():
            return thumb_path

        original_path = self._get_image_path(userid, postid, index)
        if not original_path.exists():
            return None

        # サムネイルをオンデマンドで生成して保存
        try:
            thumb_path.parent.mkdir(parents=True, exist_ok=True)
            with Image.open(original_path) as img:
                img.thumbnail((200, 200))
                img.save(thumb_path, "PNG", optimize=True)
            collect()
            return thumb_path
        except Exception as e:
            raise RuntimeError(f"Failed to generate thumbnail: {e}")

