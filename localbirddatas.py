from typing import Optional, List
from pathlib import Path
from functools import cache
import json


class LocalBirdDatas:
    def __init__(self, datadir: Path):
        self.datadir = datadir
    
    @cache
    def get_userdir(self, userid:str)->Path:
        return self.datadir / userid
    
    @cache
    def get_mediafp(self, userid:str, postid:str, idx:int)->Path:
        return self.get_userdir(userid) / f"{postid}.{idx}.png" # 今のところ画像のみ対応
    
    @cache
    def list_userid(self):
        userid_list = []
        for p in self.datadir.iterdir():
            if p.is_dir():
                userid = p.name
                userid_list.append(userid)
        return userid_list
    
    @cache
    def get_userindex(self, userid: str) -> Optional[object]:
        userdir = self.get_userdir(userid)
        if not userdir.exists():
            return None
        userindex_fp = userdir / "index.json"
        if not userindex_fp.exists():
            return None
        user = None
        with userindex_fp.open("r", encoding="utf-8") as file:
            user = json.load(file)
        return user

    def save_userindex(self, userid: str, userindex: object):
        userdir = self.get_userdir(userid)
        userdir.mkdir(exist_ok=True)
        userindex_fp = userdir / "index.json"
        with userindex_fp.open("w", encoding="utf-8") as file:
            json.dump(userindex, file, ensure_ascii=False, indent=1)
    
    @cache
    def get_media(self, userid: str, postid: str, idx: int) -> Optional[Path]:
        userdir = self.datadir / userid
        if not userdir.exists():
            return None
        media_candidates = list(userdir.glob(f"{postid}.{idx}.*"))
        if len(media_candidates) == 0:
            return None
        return media_candidates[0]

    def add_post_to_index(
        self,
        userid: str,
        username: str,
        postid: str,
        text: str,
        datetime: str,
        n_img: int,
    ) -> List[Path]:
        userindex = self.get_userindex(userid)
        if userindex is None:
            userindex = {"profile": {"name": username}, "posts": {}}
        userindex["posts"][postid] = {
            "id": postid,
            "text": text,
            "datetime": datetime,
            "medias": [{"type": "image"}] * n_img,  # 今は画像のみ対応
        }
        self.save_userindex(userid, userindex)
        media_fps = [self.get_mediafp(userid, postid, i) for i in range(n_img)]
        return media_fps
