import json
import feedparser
import yt_dlp
import datetime
import os
from unidecode import unidecode

URLBASE = "https://www.youtube.com/watch?v="
RSSBASE = "https://www.youtube.com/feeds/videos.xml?channel_id="


class DataHandler:
    def __init__(self):
        self.data = None
        self.open_data_file()

    def get_dl_path(self) -> str:
        return self.data["path"]

    def get_channel_list(self) -> list:
        c_list = []
        for c in self.data["channels"]:
            c_list.append(
                {
                    "prompt": c["title"],
                    "id": c["id"],
                }
            )
        c_list = sorted(c_list, key=lambda d: d["prompt"].lower())
        return c_list

    def get_video_from_channel_id(self, id: str) -> list:
        v_list = []
        for v in self.data["videos"]:
            if v["channel_id"] == id:
                prompt = self.get_video_prompt_for_channel(
                    title=v["title"],
                    duration=v["duration"],
                )
                v_list.append(
                    {
                        "prompt": prompt,
                        "id": v["id"],
                    }
                )
        return v_list

    def get_channel_title_from_id(self, id: str) -> str:
        title = ""
        for c in self.data["channels"]:
            if c["id"] == id:
                title = c["title"]
                break
        return title

    def get_video_from_pool(self, sort_by_len: bool = False) -> list:
        v_list = []
        v_list_ori = self.data["videos"]
        if sort_by_len:
            v_list_ori = sorted(v_list_ori, key=lambda d: d["duration"])

        for v in v_list_ori:
            if v["pool"]:
                prompt = self.get_video_prompt(
                    channel=self.get_channel_title_from_id(v["channel_id"]),
                    title=v["title"],
                    duration=v["duration"],
                )
                v_list.append(
                    {
                        "prompt": prompt,
                        "id": v["id"],
                    }
                )

        return v_list

    def get_video_prompt(self, channel: str, title: str, duration: int) -> str:
        video_str = []
        video_str.append(channel + " " * (30 - channel.__len__()) + ": ")
        video_str.append(title + " " * (110 - title.__len__()) + ": ")
        video_str.append(str(datetime.timedelta(seconds=duration)))
        return "".join(video_str)

    def get_video_prompt_for_channel(self, title: str, duration: int) -> str:
        video_str = []
        video_str.append(title + " " * (110 - title.__len__()) + ": ")
        video_str.append(str(datetime.timedelta(seconds=duration)))
        return "".join(video_str)

    def get_video_ids(self) -> list[str]:
        v_list = []
        for v in self.data["videos"]:
            v_list.append(v["id"])
        return v_list

    def get_new_videos_to_pool(self):
        v_id_list = self.get_video_ids()
        ydl_opts = {"quiet": False}
        ydl = yt_dlp.YoutubeDL(ydl_opts)

        for u in self.data["channels"]:
            newsfeed = feedparser.parse(u["url"])
            for e in newsfeed.entries:
                if e.yt_videoid not in v_id_list:
                    try:
                        meta = ydl.sanitize_info(
                            ydl.extract_info(
                                url=e.link,
                                download=False,
                            )
                        )

                        self.data["videos"].append(
                            {
                                "id": e.yt_videoid,
                                "channel_id": e.yt_channelid,
                                "title": unidecode(e.title),
                                "duration": meta["duration"],
                                "pool": True,
                            }
                        )
                    except:
                        print("pb extract info")

        self.save_data_modifications()

    def set_videos_pool(self, video_id_list: list[str], in_pool: bool):
        for v in self.data["videos"]:
            if v["id"] in video_id_list:
                v["pool"] = in_pool

        self.save_data_modifications()

    def download_video_from_list(self, video_id_list: list[str]):
        ydl_opts = {
            "format": "bv+ba/b",
            "outtmpl": self.data["path"] + "/%(title)s.%(ext)s",
            "quiet": True,
            "postprocessors": [
                {"key": "FFmpegVideoConvertor", "preferedformat": "mkv"},
                {"key": "FFmpegMetadata"},
                {"key": "EmbedThumbnail"},
            ],
            "writethumbnail": True,
        }
        ydl = yt_dlp.YoutubeDL(ydl_opts)

        for v in self.data["videos"]:
            if v["id"] in video_id_list:
                url = URLBASE + v["id"]
                try:
                    ydl.download(url)
                except:
                    print("pb yt_dlp download or merging")
        self.set_videos_pool(video_id_list, False)

    def is_new_path_valid(self, new_path: str) -> bool:
        return os.path.exists(new_path)

    def set_new_path_for_dl(self, new_path: str):
        self.data["path"] = new_path
        self.save_data_modifications()

    def is_channel_input_known(self, input: str) -> bool:
        c_list = []
        for c in self.data["channels"]:
            c_list.append(c["id"])
        if input in c_list:
            return True
        else:
            return False

    def is_channel_input_valid(self, input: str) -> bool:
        url = RSSBASE + input
        try:
            newsfeed = feedparser.parse(url)
            if len(newsfeed.entries) > 0:
                return True
            else:
                return False

        except:
            print("pb with feedparser or url !")
            return False

    def add_channel(self, channel_id: str):
        url = RSSBASE + channel_id
        newsfeed = feedparser.parse(url)
        self.data["channels"].append(
            {
                "id": newsfeed.entries[0].yt_channelid,
                "url": url,
                "title": unidecode(newsfeed.entries[0].author),
            }
        )
        self.save_data_modifications()

    def delete_channel(self, channel_id: str):
        for c in self.data["channels"]:
            if c["id"] == channel_id:
                self.data["channels"].remove(c)
                break

        final_v_list = []
        for v in self.data["videos"]:
            if v["channel_id"] != channel_id:
                final_v_list.append(v)

        self.data["videos"] = final_v_list
        self.save_data_modifications()

    def open_data_file(self):
        with open("data.json") as f:
            self.data = json.load(f)

    def save_data_modifications(self):
        with open("data.json", "w") as f:
            json.dump(self.data, f)
