from dataclasses import dataclass, asdict, fields
from pathlib import Path
from PIL.PngImagePlugin import PngInfo
from PIL import Image


@dataclass
class Meta:
    id: str | None = None
    author_name: str | None = None
    author_id: str | None = None
    text: str | None = None
    created_at: str | None = None

    @staticmethod
    def from_dict(d: dict):
        return Meta(**d)

    def to_dict(self):
        return asdict(self)

    def to_pnginfo(self):
        pi = PngInfo()
        for key, value in self.to_dict().items():
            pi.add_itxt(key, value if value is not None else "")
        return pi


def save_image_with_meta(image: Image.Image, file: Path, meta: Meta):
    assert file.name.lower().endswith(
        ".png"
    ), f"The extension must be .png, but is {file.name}."
    pnginfo = meta.to_pnginfo()
    image.save(file, format="PNG", pnginfo=pnginfo)


class AnnotatedImage:
    def __init__(self, file: Path) -> None:
        self.file = file
        self.image = Image.open(file)
        info = self.image.info
        self.meta = Meta.from_dict(info)

    def save_meta(self, meta: Meta):
        save_image_with_meta(self.image, self.file, meta)

    def __str__(self) -> str:
        return str(self.meta)


class Repository:
    def __init__(
        self,
        annotated_images_dir: Path = Path("./Images"),
        annotated_thumbnails_dir: Path = Path("./Thumbnails"),
    ) -> None:
        self.annotated_images_dir = annotated_images_dir
        self.annotate_thumbnails_dir = annotated_thumbnails_dir

    @staticmethod
    def is_safe_filename(filename: str):
        if "/" in filename:
            return False
        return True

    @staticmethod
    def ensure_safe_filename(filename: str):
        if not Repository.is_safe_filename(filename):
            raise ValueError(f"The filename {filename} is invalid")

    def get_image_path(self, filename: str):
        Repository.ensure_safe_filename(filename)
        return self.annotated_images_dir / filename

    def get_thumbnail_path(self, filename: str):
        Repository.ensure_safe_filename(filename)
        return self.annotate_thumbnails_dir / filename

    def add_images(self, images: list[Image.Image], meta: Meta) -> list[str]:
        filenames = []
        for image_index, image in enumerate(images):
            filename = f"{meta.id}.{image_index}.png"
            save_image_with_meta(image, self.annotated_images_dir / filename, meta)
            filenames.append(filename)
        return filenames

    def create_thumbnail(self, filename: str):
        orig = AnnotatedImage(self.get_image_path(filename))
        orig.image.thumbnail((200, 200))
        save_image_with_meta(orig.image, self.get_thumbnail_path(filename), orig.meta)

    def get_image(self, filename: str) -> AnnotatedImage:
        image_path = self.get_image_path(filename)
        if not image_path.exists():
            raise ValueError(f"The filename {filename} does not exist")
        return AnnotatedImage(image_path)

    def prepare_thumbnail(self, filename: str):
        thumbnail_path = self.get_thumbnail_path(filename)
        if not thumbnail_path.exists():
            self.create_thumbnail(filename)
        return thumbnail_path

    def get_thumbnail(self, filename: str) -> AnnotatedImage:
        thumbnail_path = self.prepare_thumbnail(filename)
        return AnnotatedImage(thumbnail_path)

    def list(self, limit: int = 50, offset: int = 0) -> list[str]:
        if not self.annotated_images_dir.exists():
            return []
        files = sorted(self.annotated_images_dir.glob("*.png"), reverse=True)
        target_files = files[offset : offset + limit]
        return [file.name for file in target_files]

    def list_by_postid(self, id: str) -> list[str]:
        if not self.annotated_images_dir.exists():
            return []
        files = sorted(self.annotated_images_dir.glob(f"{id}.*.png"))
        return [file.name for file in files]

    def delete(self, filename: str) -> bool:
        success = True
        paths = [
            self.get_image_path(filename),
            self.get_thumbnail_path(filename),
        ]
        for path in paths:
            if path.exists() and path.is_file():
                try:
                    path.unlink()
                except OSError:
                    success = False
        return success
