from pathlib import Path
from argparse import ArgumentParser
import json
from xml.sax.saxutils import unescape
import re
import requests
from bs4 import BeautifulSoup
from postimporter import Post
from repository import Meta

IMAGE_URL_PATTERN = re.compile(r"https://pbs.twimg.com/media/.*")


def extract_id(x_soup: BeautifulSoup, url: str) -> str | None:
    # Page-based search

    # <meta itemprop="identifier" content="{{id}}" />
    id_element = x_soup.find(name="meta", attrs={"itemprop": "identifier"})
    if id_element and id_element.has_attr("content"):
        id = str(id_element.attrs["content"])
        return id

    # <meta itemprop="url" content=".../status/{{id}}" />
    id_element = x_soup.find(name="meta", attrs={"itemprop": "url"})
    if id_element and id_element.has_attr("content"):
        content = str(id_element.attrs["content"])
        mat = re.search(r"/status/(\d+)", content)
        if mat:
            id = str(mat.group(1))
            return id

    # <article data-tweet-id="{{id}}">
    id_element = x_soup.find(name="article", attrs={"data-tweet-id": True})
    if id_element:
        id = str(id_element.attrs["data-tweet-id"])
        return id

    # <meta content=".../status/{{id}}" />
    id_element = x_soup.find(name="meta", attrs={"property": "og:url"})
    if id_element and id_element.has_attr("content"):
        content = str(id_element.attrs["content"])
        mat = re.search(r"/status/(\d+)", content)
        if mat:
            id = str(mat.group(1))
            return id

    # <meta property="al:ios:url" content="...id={{id}}" />
    id_element = x_soup.find(name="meta", attrs={"property": "al:ios:url"})
    if id_element and id_element.has_attr("content"):
        content = str(id_element.attrs["content"])
        mat = re.search(r"id=(\d+)", content)
        if mat:
            id = str(mat.group(1))
            return id

    # <meta property="al:android:url" content="...id={{id}}" />
    id_element = x_soup.find(name="meta", attrs={"property": "al:android:url"})
    if id_element and id_element.has_attr("content"):
        content = str(id_element.attrs["content"])
        mat = re.search(r"id=(\d+)", content)
        if mat:
            id = str(mat.group(1))
            return id

    # URL-based search
    mat = re.search(r"https://x\.com/[^/]+/status/(\d+)", url)
    if mat:
        id = str(mat.group(1))
        return id

    return None


def extract_post_from_x_page(url: str) -> Post:
    response = requests.get(url)
    if not response.ok:
        raise ValueError(f"Response is not OK: Status Code = {response.status_code}")
    soup = BeautifulSoup(response.content, "html.parser")

    post = Post()

    # ID
    post.meta.id = extract_id(soup, url)

    # Author Name
    author_name_element = soup.find(name="meta", attrs={"itemprop": "name"})
    if author_name_element and author_name_element.has_attr("content"):
        post.meta.author_name = str(author_name_element.attrs["content"])

    # Author ID
    author_id_element = soup.find(name="meta", attrs={"name": "twitter:creator"})
    if author_id_element and author_id_element.has_attr("content"):
        post.meta.author_id = str(author_id_element.attrs["content"])[1:]

    # Text
    text_element = soup.find(name="meta", attrs={"name": "twitter:description"})
    if text_element and text_element.has_attr("content"):
        post.meta.text = str(text_element.attrs["content"])

    # Created At
    created_at_element = soup.find(
        name="meta", attrs={"property": "article:published_time"}
    )
    if created_at_element and created_at_element.has_attr("content"):
        post.meta.created_at = str(created_at_element.attrs["content"])

    # Image Sources
    image_elements = soup.find_all(name="img", attrs={"src": IMAGE_URL_PATTERN})
    image_srcs = []
    for image_element in image_elements:
        src = str(image_element.attrs["src"])
        unescaped_src = unescape(src)
        if unescaped_src not in image_srcs:
            image_srcs.append(unescaped_src)
    post.image_srcs = image_srcs
    if not post.image_srcs:
        raise ValueError("The post has no images")

    return post


if __name__ == "__main__":
    parser = ArgumentParser(
        prog="LocalBird", description="Extracts Post data from X page and creates JSON"
    )
    parser.add_argument("url", type=str, help="The X page url")
    parser.add_argument("destination", type=Path, help="Directory to save the JSON")
    args = parser.parse_args()

    try:
        post = extract_post_from_x_page(args.url)
    except Exception as e:
        print("Error")
        print(e)
        exit(-1)
    destination = Path(args.destination)
    destination.mkdir(parents=True, exist_ok=True)

    post_json = json.dumps(post.to_dict(), ensure_ascii=False)
    (destination / f"{post.meta.id}.json").write_text(post_json)
