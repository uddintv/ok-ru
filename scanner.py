
import requests
import json
import os
from concurrent.futures import ThreadPoolExecutor

BASE = "https://live2.jorvakstreamcache.com/live/"

channels = [
    BASE + f"channel{i}.m3u8"
    for i in range(1, 20)
]

headers = {
    "User-Agent": "Mozilla/5.0"
}

def check(url):
    try:
        r = requests.get(
            url,
            headers=headers,
            timeout=12
        )

        if r.status_code != 200:
            return None

        text = r.text

        if not text.strip().startswith("#EXTM3U"):
            return None

        lines = [
            x.strip() for x in text.splitlines()
            if x.strip() and not x.startswith("#")
        ]

        if not lines:
            return None

        media_url = url

        # Master playlist
        if "#EXT-X-STREAM-INF" in text:
            for i, line in enumerate(text.splitlines()):
                if line.startswith("#EXT-X-STREAM-INF"):
                    variant = next(
                        (x.strip() for x in text.splitlines()[i+1:]
                         if x.strip() and not x.startswith("#")),
                        None
                    )
                    if not variant:
                        return None

                    media_url = requests.compat.urljoin(url, variant)
                    r = requests.get(
                        media_url,
                        headers=headers,
                        timeout=12
                    )

                    if r.status_code != 200:
                        return None

                    text = r.text

                    if not text.strip().startswith("#EXTM3U"):
                        return None

                    break

        segment = next(
            (x.strip() for x in text.splitlines()
             if x.strip() and not x.startswith("#")),
            None
        )

        if not segment:
            return None

        segment_url = requests.compat.urljoin(
            media_url, segment
        )

        test = requests.get(
            segment_url,
            headers=headers,
            timeout=12,
            stream=True
        )

        try:
            if test.status_code not in (200, 206):
                return None

            first_bytes = next(test.iter_content(2), b"")

            if not first_bytes:
                return None

        finally:
            test.close()

        return url

    except requests.RequestException:
        return None


with ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(check, channels))

live_links = [
    {"index": i, "url": url}
    for i, url in enumerate(
        [x for x in results if x],
        start=1
    )
]

data = {
    "live": live_links
}

with open("live.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("LIVE LINKS:", len(live_links))
