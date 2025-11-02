import re
import io
from configHandler import config

pathregex = re.compile("\\w{1,15}\\/(status|statuses)\\/(\\d{2,20})")
endTCOregex = re.compile("(^.*?)[ \n]+https:\/\/t.co\/.*?$",flags=re.DOTALL)

def getTweetIdFromUrl(url):
    match = pathregex.search(url)
    if match is not None:
        return match.group(2)
    else:
        return None
    
def stripEndTCO(text):
    # remove t.co links at the end of a string
    match = endTCOregex.search(text)
    if match is not None:
        return match.group(1)
    else:
        return text
    
# https://stackoverflow.com/a/55977438
class BytesIOWrapper(io.BufferedReader):
    """Wrap a buffered bytes stream over TextIOBase string stream."""

    def __init__(self, text_io_buffer, encoding=None, errors=None, **kwargs):
        super(BytesIOWrapper, self).__init__(text_io_buffer, **kwargs)
        self.encoding = encoding or text_io_buffer.encoding or 'utf-8'
        self.errors = errors or text_io_buffer.errors or 'strict'

    def _encoding_call(self, method_name, *args, **kwargs):
        raw_method = getattr(self.raw, method_name)
        val = raw_method(*args, **kwargs)
        return val.encode(self.encoding, errors=self.errors)

    def read(self, size=-1):
        return self._encoding_call('read', size)

    def read1(self, size=-1):
        return self._encoding_call('read1', size)

    def peek(self, size=-1):
        return self._encoding_call('peek', size)
    
def fixMedia(mediaInfo):
    # This is for the iOS Discord app, which has issues when serving URLs ending in .mp4 (https://github.com/dylanpdx/BetterTwitFix/issues/210)
    if 'video.twimg.com' not in mediaInfo['url'] or 'convert?url=' in mediaInfo['url'] or 'originalUrl' in mediaInfo:
        return mediaInfo
    mediaInfo["originalUrl"] = mediaInfo['url']
    mediaInfo['url'] = mediaInfo['url'].replace("https://video.twimg.com",f"{config['config']['url']}/tvid").replace(".mp4","")
    return mediaInfo

def determineEmbedTweet(tweetData):
    # Determine which tweet, i.e main or QRT, to embed the media from.
    # if there is no QRT, return the main tweet => default behavior
    # if both don't have media, return the main tweet => embedding qrt text will be handled in the embed description
    # if both have media, return the main tweet => priority is given to the main tweet's media
    # if only the QRT has media, return the QRT => show the QRT's media, not the main tweet's
    # if only the main tweet has media, return the main tweet => show the main tweet's media, embedding QRT text will be handled in the embed description
    if tweetData['qrt'] is None:
        return tweetData
    if tweetData['qrt']['hasMedia'] and not tweetData['hasMedia']:
        return tweetData['qrt']
    return tweetData

def determineMediaToEmbed(tweetData,embedIndex = -1,convertGif = True):
    if tweetData['allSameType'] and tweetData['media_extended'][0]['type'] == "image" and embedIndex == -1 and tweetData['combinedMediaUrl'] != None:
        return {"url":tweetData['combinedMediaUrl'],"type":"image"}
    else:
        # this means we have mixed media or video, and we're only going to embed one
        if embedIndex == -1: # if the user didn't specify an index, we'll just use the first one
            embedIndex = 0
        media = tweetData['media_extended'][embedIndex]
        media=fixMedia(media)
        suffix=""
        if len(tweetData["media_extended"]) > 1:
            suffix = f' • Media {embedIndex+1}/{len(tweetData["media_extended"])}'
        else:
            suffix = ''
        media["suffix"] = suffix
        if media['type'] == "image":
            return media
        elif media['type'] == "video" or media['type'] == "gif":
            if media['type'] == "gif" and convertGif:
                if config['config']['gifConvertAPI'] != "" and config['config']['gifConvertAPI'] != "none":
                    vurl=media['originalUrl'] if 'originalUrl' in media else media['url']
                    media['url'] = config['config']['gifConvertAPI'] + "/convert?url=" + vurl
                    suffix += " • GIF"
                    media["suffix"] = suffix
        return media