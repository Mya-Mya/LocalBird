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
    def is_safe_basename(basename: str):
        if "/" in basename:
            return False
        return True

    @staticmethod
    def ensure_safe_basename(basename: str):
        if not Repository.is_safe_basename(basename):
            raise ValueError(f"The filename {basename} is invalid")

    def get_image_path(self, basename: str):
        Repository.ensure_safe_basename(basename)
        return self.annotated_images_dir / (basename + ".png")

    def get_thumbnail_path(self, basename: str):
        Repository.ensure_safe_basename(basename)
        return self.annotate_thumbnails_dir / (basename + ".webp")

    def add_images(self, images: list[Image.Image], meta: Meta) -> list[str]:
        basenames = []
        for image_index, image in enumerate(images):
            basename = f"{meta.id}.{image_index}"
            save_image_with_meta(image, self.get_image_path(basename), meta)
            basenames.append(basename)
        return basenames

    def create_thumbnail(self, basename: str):
        orig = AnnotatedImage(self.get_image_path(basename))
        orig.image.thumbnail((200, 200))
        thumbnail_path = self.get_thumbnail_path(basename)
        orig.image.save(thumbnail_path, format="WebP")
        # save_image_with_meta(orig.image, self.get_thumbnail_path(filename), orig.meta)

    def get_image(self, basename: str) -> AnnotatedImage:
        image_path = self.get_image_path(basename)
        if not image_path.exists():
            raise ValueError(f"The basename {basename} does not exist")
        return AnnotatedImage(image_path)

    def prepare_thumbnail(self, basename: str):
        thumbnail_path = self.get_thumbnail_path(basename)
        if not thumbnail_path.exists():
            self.create_thumbnail(basename)
        return thumbnail_path

    def get_thumbnail(self, basename: str) -> Image.Image:
        thumbnail_path = self.prepare_thumbnail(basename)
        thumbnail = Image.open(thumbnail_path)
        return thumbnail

    def list(self, limit: int = 50, offset: int = 0) -> list[str]:
        if not self.annotated_images_dir.exists():
            return []
        files = sorted(self.annotated_images_dir.glob("*.png"), reverse=True)
        target_files = files[offset : offset + limit]
        return [file.stem for file in target_files]

    def list_by_postid(self, id: str) -> list[str]:
        if not self.annotated_images_dir.exists():
            return []
        files = sorted(self.annotated_images_dir.glob(f"{id}.*.png"))
        return [file.stem for file in files]

    def delete(self, basename: str) -> bool:
        success = True
        paths = [
            self.get_image_path(basename),
            self.get_thumbnail_path(basename),
        ]
        for path in paths:
            if path.exists() and path.is_file():
                try:
                    path.unlink()
                except OSError:
                    success = False
        return success
