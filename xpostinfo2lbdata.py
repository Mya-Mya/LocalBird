from typing import Tuple
from pathlib import Path
import requests
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import json
from argparse import ArgumentParser
from tqdm import tqdm
from localbirddatas import LocalBirdDatas

DATA_DIR = Path("./Data")

def split_username(username:str)->Tuple[str, str]:
    split = username.splitlines()
    displayname = split[0]
    userid = split[1][1:]
    return displayname, userid

def fetch_img(url: str, saveto: Path, skip_if_exists: bool = True):
    if saveto.exists() and skip_if_exists:
        return
    result = requests.get(url, stream=True)
    result.raise_for_status()
    with open(saveto, "wb") as file:
        for chunk in result.iter_content(1024):
            file.write(chunk)


def upgrade_imgurl(url: str) -> str:
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    query_params["format"] = ["png"]
    query_params["name"] = ["4096x4096"]
    new_query = urlencode(query_params, doseq=True)
    new_url = urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment,
        )
    )
    return new_url

def saveas_lbdata(xpostinfo:dict):
    displayname, _ = split_username(xpostinfo["username"])
    mediafp_list = repository.add_post_to_index(
        userid=xpostinfo["userid"],
        username=displayname,
        postid=xpostinfo["tweetid"],
        text=xpostinfo["tweettext"],
        datetime=xpostinfo["datetime"],
        n_img=len(xpostinfo["imgsrcs"])
    )
    for mediafp, imgsrc in zip(mediafp_list, xpostinfo["imgsrcs"]):
        url = upgrade_imgurl(imgsrc)
        fetch_img(url, saveto=mediafp)

def saveas_lbdata_from_path(xpostinfo_fp:Path):
    with xpostinfo_fp.open("r", encoding="utf-8") as file:
        xpostinfo = json.load(file)
    saveas_lbdata(xpostinfo)

repository:LocalBirdDatas = None
if __name__ == "__main__":
    parser = ArgumentParser(
        description="Prepare LocalBird Tweet Data from xpostinfo JSON file(s)."
    )
    parser.add_argument("datadir", type=Path, help="LocalBird Data Directory", default="./Data")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-d",
        "--directory",
        type=Path,
        help="Directory that contains xpostinfo JSON file with name `xpostinfo.*.json`.",
    )
    group.add_argument(
        "-f", "--file", type=Path, help="xpostinfo JSON file (with free-form name)."
    )
    args = parser.parse_args()

    repository = LocalBirdDatas(datadir=Path(args.datadir))
    if args.directory:
        directory = Path(args.directory)
        fp_list = list(directory.glob("xpostinfo.*.json"))
        if not fp_list:
            print("No xpostinfo JSON files.")
            exit(-1)
        for i, fp in enumerate(fp_list):
            print(i, fp)
        if input("Start Process? [Y/other]") == "Y":
            for fp in tqdm(fp_list):
                saveas_lbdata_from_path(fp)
    if args.file:
        saveas_lbdata_from_path(Path(args.file))
