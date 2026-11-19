# based loosely on:
# https://stackoverflow.com/a/1119769 
# https://mojoauth.com/dev-guides/base62-with-python
# https://github.com/suminb/base62/blob/develop/base62.py
# format: base62(version + zlib(json))

import json
import zlib
import string

MAX_DATA_LEN = 1400
MAX_DECOMPRESSED_LEN = 512 * 1024

ALPHABET = string.digits + string.ascii_uppercase + string.ascii_lowercase

# DO NOT CHANGE THIS!
# data encoded with one dict must be decoded with the same dict, which is why I put a version num at the start
ACTIVITY_V2 = (
    '<blockquote>🌐 <i>→</i></blockquote>'
    '<blockquote>↪️ <i>Replying to @</i></blockquote>'
    '<blockquote><b>QRT: <a href="https://twitter.com/i/status/</a></b><br>'
    'https://pbs.twimg.com/tweet_video_thumb/.jpg'
    'https://video.twimg.com/tweet_video/.mp4'
    'https://pbs.twimg.com/amplify_video_thumb//img/.jpg'
    'https://video.twimg.com/amplify_video//vid/avc1/1280x720/.mp4?tag=1'
    'https://pbs.twimg.com/ext_tw_video_thumb//pu/img/.jpg'
    'https://video.twimg.com/ext_tw_video//pu/vid/avc1/1280x720/.mp4?tag=12'
    '"type":"gifv","type":"video",'
    '{"id":"21","url":"https://x.com/_/status/21",'
    '"uri":"https://x.com/_/status/21","created_at",'
    '"edited_at":null,"reblog":null,"in_reply_to_account_id":null,"language":"en","content":"<p></p><br>",'
    '"spoiler_text":"","visibility":"public","application":{"website":null},'
    '"media_attachments":[{"id":"1","type":"image",'
    '"url":"https://pbs.twimg.com/media/.jpg?name=orig","preview_url":"https://pbs.twimg.com/media/.jpg"}],'
    '"account":{"display_name":"","username":"","acct":"","url":"https://x.com/_/status/21",'
    '"uri":"https://x.com/_/status/21","locked":false,'
    '"avatar":"https://pbs.twimg.com/profile_images/21/_normal.jpg",'
    '"avatar_static":"https://pbs.twimg.com/profile_images/21/_normal.jpg",'
    '"hide_collections":false,"noindex":false}}'
).encode("utf-8")

DICT_VERSIONS = {
    1: None,
    2: ACTIVITY_V2,
}
CURRENT_VERSION = 2

def base62Encode(data): # bytes -> base62 str
    if not data or data[0] == 0:
        raise Exception("invalid start byte")
    n = int.from_bytes(data, "big")
    out = []
    while n:
        if n < 0:
            raise Exception("invalid byte")
        n, r = divmod(n, 62)
        out.append(ALPHABET[r])
    return "".join(reversed(out))

def base62Decode(text): # base62 str -> bytes
    n = 0
    for ch in text:
        n = n * 62 + ALPHABET.index(ch)
    return n.to_bytes((n.bit_length() + 7) // 8, "big")

def getCompressor(zdict):
    if zdict is None:
        return zlib.compressobj(9)
    return zlib.compressobj(9, zlib.DEFLATED, 15, 9, zlib.Z_DEFAULT_STRATEGY, zdict)

def getDecompressor(zdict):
    if zdict is None:
        return zlib.decompressobj()
    return zlib.decompressobj(15, zdict)

def pack(obj, version=CURRENT_VERSION):
    raw = json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8") # flat json
    compressor = getCompressor(DICT_VERSIONS[version])
    compressed = compressor.compress(raw) + compressor.flush()
    return base62Encode(bytes([version]) + compressed)

def unpack(packed):
    if len(packed) > MAX_DATA_LEN:
        return None
    try:
        data = base62Decode(packed)
        if not data or data[0] not in DICT_VERSIONS:
            return None
        decompressor = getDecompressor(DICT_VERSIONS[data[0]])
        raw = decompressor.decompress(data[1:], MAX_DECOMPRESSED_LEN)
        if decompressor.unconsumed_tail or not decompressor.eof:
            return None
        return json.loads(raw)
    except Exception:
        return None
