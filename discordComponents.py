import json
from copy import deepcopy
from configHandler import config
from utils import mediaToGifConvert

media_per_post = 10
max_size = 2000

def galleryUrls(mediaExtended): # get urls to add to the gallery
    urls = []
    for media in mediaExtended:
        url = media["url"]
        if media["type"] == "gif":
            url = mediaToGifConvert(deepcopy(media))["url"]
        if url.startswith("https://pbs.twimg.com") and "?" not in url:
            url = f"{url}?name=orig"
        urls.append(url)
    return urls

def buildTweetComponents(tweetData, embedTweetData, desc, tweetLink, page=1):
    urls = galleryUrls(embedTweetData["media_extended"])
    if len(urls) == 0: # how did we get here
        return None
    pageCount = (len(urls) + media_per_post - 1) // media_per_post
    page = min(max(page,1),pageCount) # if someone puts a p# > pages, just use the last one
    shown = urls[(page-1)*media_per_post : page*media_per_post]

    container = {"type":17,"components":[]}
    color = config['config']['color']
    if color:
        try:
            container["accent_color"] = int(color.replace("#","0x").replace("\\",""),16)
        except:
            pass

    header = [
        {"type":10,"content":f"**{tweetData['user_name']} (@{tweetData['user_screen_name']})**"},
    ]
    if (len(desc)>max_size):
        desc = desc[:2000]+"..."
    descComponent = {"type":10,"content":desc}
    footer = [{"type":12,"items":[{"media":{"url":url}} for url in shown]}]
    if pageCount > 1:
        otherPages = ", ".join(f"/p{p}" for p in range(1,pageCount+1) if p != page)
        footer.append({"type":10,"content":f"-# Page {page}/{pageCount} - add {otherPages} to the link to see others"})
    epoch = str(tweetData["date_epoch"])
    footerdisp = config['config']['appname'] + f" - <t:{epoch}:d> <t:{epoch}:t>"
    footer.append({"type":10,"content":f"-# {footerdisp}"})

    descComponents = [descComponent] if desc.strip() else [] # this makes embeds fail, discord can;'t do empty components
    container["components"] = header + descComponents + footer
    resp = {"component":container}

    return resp
