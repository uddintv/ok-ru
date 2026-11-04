const fs = require('fs');
const path = require('path');

const channels = [
  { id: 1, url: "https://live2.jorvakstreamcache.com/live/channel1.m3u8" },
  { id: 2, url: "https://live2.jorvakstreamcache.com/live/channel2.m3u8" },
  { id: 3, url: "https://live2.jorvakstreamcache.com/live/channel3.m3u8" },
  { id: 4, url: "https://live2.jorvakstreamcache.com/live/channel4.m3u8" },
  { id: 5, url: "https://live2.jorvakstreamcache.com/live/channel5.m3u8" },
  { id: 6, url: "https://live2.jorvakstreamcache.com/live/channel6.m3u8" },
  { id: 7, url: "https://live2.jorvakstreamcache.com/live/channel7.m3u8" },
  { id: 8, url: "https://live2.jorvakstreamcache.com/live/channel8.m3u8" },
  { id: 9, url: "https://live2.jorvakstreamcache.com/live/channel9.m3u8" },
  { id: 10, url: "https://live2.jorvakstreamcache.com/live/channel10.m3u8" },
  { id: 11, url: "https://live2.jorvakstreamcache.com/live/channel11.m3u8" },
  { id: 12, url: "https://live2.jorvakstreamcache.com/live/channel12.m3u8" },
  { id: 13, url: "https://live2.jorvakstreamcache.com/live/channel13.m3u8" },
  { id: 14, url: "https://live2.jorvakstreamcache.com/live/channel14.m3u8" },
  { id: 15, url: "https://live2.jorvakstreamcache.com/live/channel15.m3u8" },
  { id: 16, url: "https://live2.jorvakstreamcache.com/live/channel16.m3u8" },
  { id: 17, url: "https://live2.jorvakstreamcache.com/live/channel17.m3u8" },
  { id: 18, url: "https://live2.jorvakstreamcache.com/live/channel18.m3u8" },
  { id: 19, url: "https://live2.jorvakstreamcache.com/live/channel19.m3u8" }
];

const filePath = path.join(__dirname, 'channels.json');

async function checkChannel(channel) {
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 10000);

    const response = await fetch(channel.url, {
      method: "GET",
      signal: controller.signal
    });
    clearTimeout(timer);

    if (!response.ok) return false;
    const playlist = await response.text();
    if (!playlist.trim().startsWith("#EXTM3U")) return false;

    return true;
  } catch (error) {
    return false;
  }
}

async function runScanner() {
  console.log("চ্যানেল স্ক্যান শুরু হচ্ছে...");
  let newlyFound = [];

  for (let i = 0; i < channels.length; i += 3) {
    const batch = channels.slice(i, i + 3);
    const results = await Promise.all(batch.map(ch => checkChannel(ch)));

    results.forEach((isLive, index) => {
      if (isLive) {
        newlyFound.push(batch[index]);
      }
    });
  }

  // আগের ফাইল থেকে ডেটা পড়া (যদি থাকে)
  let existingLinks = [];
  if (fs.existsSync(filePath)) {
    try {
      const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
      existingLinks = data.links || [];
    } catch (e) {}
  }

  // যদি নতুন স্ক্যানে সচল লিংক পাওয়া যায়, তবে আপডেট হবে। না হলে পুরনো লিংক বহাল থাকবে।
  let finalLinks = newlyFound.length > 0 ? newlyFound : existingLinks;

  const outputData = {
    updated_at: new Date().toISOString(),
    count: finalLinks.length,
    links: finalLinks
  };

  fs.writeFileSync(filePath, JSON.stringify(outputData, null, 2));
  console.log("স্ক্যান সম্পন্ন! channels.json ফাইল আপডেট করা হয়েছে।");
}

runScanner();
