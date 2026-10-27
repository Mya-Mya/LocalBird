from argparse import ArgumentParser
from pathlib import Path
from repository import *
from postimporter import add_images_by_files

if __name__ == "__main__":
    parser = ArgumentParser(
        prog="LocalBird Manual Importer",
        description="Registers local images with manually written metadata",
    )
    parser.add_argument("images", type=Path, nargs="+", help="Image files (in order)")
    parser.add_argument("--id", required=True, help="The post ID")
    parser.add_argument("--author-name")
    parser.add_argument("--author-id")
    parser.add_argument("--text")
    parser.add_argument("--created-at", help="e.g. 2025-01-01T00:00:00.000Z")
    args = parser.parse_args()

    meta = Meta(
        id=args.id,
        author_name=args.author_name,
        author_id=args.author_id,
        text=args.text,
        created_at=args.created_at,
    )
    repo = Repository()
    repo.annotated_images_dir.mkdir(parents=True, exist_ok=True)
    try:
        basenames = add_images_by_files(repo, meta, args.images)
    except Exception as e:
        print("Error")
        print(e)
        exit(-1)
    for basename in basenames:
        print(basename)
