
import requests
import json
from concurrent.futures import ThreadPoolExecutor

BASE = "https://live2.jorvakstreamcache.com/live/"

# মোট ৩০টি M3U8 চ্যানেল
channels = [
    {
        "name": f"server {i}",
        "url": f"{BASE}channel{i}.m3u8"
    }
    for i in range(1, 31)
]

headers = {
    "User-Agent": "Mozilla/5.0"
}


def check(channel):

    url = channel["url"]

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
            x.strip()
            for x in text.splitlines()
            if x.strip()
        ]

        media_url = url

        # Master Playlist পরীক্ষা
        if "#EXT-X-STREAM-INF" in text:

            variant = None

            for i, line in enumerate(lines):

                if line.startswith("#EXT-X-STREAM-INF"):

                    variant = next(
                        (
                            x for x in lines[i + 1:]
                            if not x.startswith("#")
                        ),
                        None
                    )

                    break

            if not variant:
                return None

            media_url = requests.compat.urljoin(
                url, variant
            )

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

        # Media Segment খোঁজা
        segment = next(
            (
                x.strip()
                for x in text.splitlines()
                if x.strip() and not x.strip().startswith("#")
            ),
            None
        )

        if not segment:
            return None

        segment_url = requests.compat.urljoin(
            media_url, segment
        )

        # Segment পরীক্ষা
        test = requests.get(
            segment_url,
            headers=headers,
            timeout=12,
            stream=True
        )

        try:

            if test.status_code not in (200, 206):
                return None

            first_bytes = next(
                test.iter_content(2),
                b""
            )

            if not first_bytes:
                return None

        finally:
            test.close()

        print("LIVE:", channel["name"])

        return channel

    except requests.RequestException as e:

        print("ERROR:", channel["name"], str(e))

        return None


# ৫টি Worker দিয়ে স্ক্যান
with ThreadPoolExecutor(max_workers=5) as executor:

    results = list(
        executor.map(check, channels)
    )


# শুধু LIVE চ্যানেল
live_links = [
    result
    for result in results
    if result is not None
]


# API-compatible JSON Array
with open("live.json", "w", encoding="utf-8") as f:

    json.dump(
        live_links,
        f,
        indent=4,
        ensure_ascii=False
    )


print("--------------------------------")
print("TOTAL CHANNELS:", len(channels))
print("LIVE CHANNELS:", len(live_links))
print("OFFLINE CHANNELS:", len(channels) - len(live_links))
print("JSON UPDATED: live.json")
print("--------------------------------")
