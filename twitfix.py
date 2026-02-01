from flask import Flask, render_template, request, redirect, abort, Response, send_from_directory, send_file

from configHandler import config
remoteCombine='combination_method' in config['config'] and config['config']['combination_method'] != "local"

if not remoteCombine:
    import combineImg

from flask_cors import CORS
import os
from io import BytesIO, StringIO
import urllib
import msgs
import twExtract as twExtract
from cache import addVnfToLinkCache,getVnfFromLinkCache
import vxlogging as log
from utils import getTweetIdFromUrl, pathregex, determineMediaToEmbed, determineEmbedTweet, BytesIOWrapper, fixMedia
from vxApi import getApiResponse, getApiUserResponse
from urllib.parse import urlparse 
from PyRTF.Elements import Document
from PyRTF.document.section import Section
from PyRTF.document.paragraph import Paragraph
from copy import deepcopy
import json
import datetime
import activity as activitymg
app = Flask(__name__)
CORS(app)
user_agent=""

staticFiles = { # TODO: Use flask static files instead of this
    "favicon.ico": {"mime": "image/vnd.microsoft.icon","path": "favicon.ico"},
    "apple-touch-icon.png": {"mime": "image/png","path": "apple-touch-icon.png"},
    "openInApp.js": {"mime": "text/javascript","path": "openInApp.js"},
    "preferences": {"mime": "text/html","path": "preferences.html"},
    "style.css": {"mime": "text/css","path": "style.css"},
    "Roboto-Regular.ttf": {"mime": "font/ttf","path": "Roboto-Regular.ttf"},
    "gif.png": {"mime": "image/png","path": "richEmbed/gif.png"},
    "video.png": {"mime": "image/png","path": "richEmbed/video.png"},
    "image.png": {"mime": "image/png","path": "richEmbed/image.png"},
    "text.png": {"mime": "image/png","path": "richEmbed/text.png"},
}

generate_embed_user_agents = [
    "facebookexternalhit/1.1",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.57 Safari/537.36",
    "Mozilla/5.0 (Windows; U; Windows NT 10.0; en-US; Valve Steam Client/default/1596241936; ) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36",
    "Mozilla/5.0 (Windows; U; Windows NT 10.0; en-US; Valve Steam Client/default/0; ) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36", 
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/601.2.4 (KHTML, like Gecko) Version/9.0.1 Safari/601.2.4 facebookexternalhit/1.1 Facebot Twitterbot/1.0", 
    "facebookexternalhit/1.1",
    "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; Valve Steam FriendsUI Tenfoot/0; ) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36", 
    "Slackbot-LinkExpanding 1.0 (+https://api.slack.com/robots)", 
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:38.0) Gecko/20100101 Firefox/38.0", 
    "Mozilla/5.0 (compatible; Discordbot/2.0; +https://discordapp.com)", 
    "TelegramBot (like TwitterBot)", 
    "Mozilla/5.0 (compatible; January/1.0; +https://gitlab.insrt.uk/revolt/january)", 
    "Synapse (bot; +https://github.com/matrix-org/synapse)",
    "Iframely/1.3.1 (+https://iframely.com/docs/about)",
    "test"]

def isValidUserAgent(user_agent):
    return True
    if user_agent in generate_embed_user_agents:
        return True
    elif "WhatsApp/" in user_agent:
        return True
    return False

def message(text):
    rendered = render_template(
        'default.html', 
        message = text, 
        color   = config['config']['color'], 
        appname = config['config']['appname'], 
        repo    = config['config']['repo'], 
        url     = config['config']['url'] )
    return Response(rendered, mimetype='text/html',headers={"Cache-Tag": "message", "Cache-Control": "max-age=1760, public"})

def generateActivityLink(tweetData,media=None,mediatype=None,embedIndex=-1):
    global user_agent
    if 'LegacyEmbed' in user_agent: # TODO: Clean up; This is a hacky fix to make the new activity embed not trigger
        return None
    try:
        embedIndex = embedIndex+1
        return f"{config['config']['url']}/users/{tweetData['user_screen_name']}/statuses/{str(embedIndex)}{tweetData['tweetID']}"
    except Exception as e:
        log.error("Error generating activity link: "+str(e))
        return None

def getAppName(tweetData,appnameSuffix=""):
    appName = config['config']['appname']+appnameSuffix
    if 'Discord' not in user_agent:
        appName = msgs.formatProvider(config['config']['appname']+appnameSuffix,tweetData)
    return appName

def renderImageTweetEmbed(tweetData,image,appnameSuffix="",embedIndex=-1):
    qrt = tweetData['qrt']
    embedDesc = msgs.formatEmbedDesc("Image",tweetData['text'],qrt,tweetData['pollData'])

    if image.startswith("https://pbs.twimg.com") and "?" not in image:
        image = f"{image}?name=orig"
    
    return render_template("image.html",
                    tweet=tweetData,
                    pic=[image],
                    host=config['config']['url'],
                    desc=embedDesc,
                    urlEncodedDesc=urllib.parse.quote(embedDesc),
                    tweetLink=f'https://twitter.com/{tweetData["user_screen_name"]}/status/{tweetData["tweetID"]}',
                    appname=getAppName(tweetData,appnameSuffix),
                    color=config['config']['color'],
                    sicon="image",
                    activityLink=generateActivityLink(tweetData,image,"image/png",embedIndex)
                    )

def renderVideoTweetEmbed(tweetData,mediaInfo,appnameSuffix="",embedIndex=-1):
    qrt = tweetData['qrt']
    embedDesc = msgs.formatEmbedDesc("Video",tweetData['text'],qrt,tweetData['pollData'])

    mediaInfo=fixMedia(mediaInfo)

    appName = config['config']['appname']+appnameSuffix
    if 'Discord' not in user_agent:
        appName = msgs.formatProvider(config['config']['appname']+appnameSuffix,tweetData)

    return render_template("video.html",
                    tweet=tweetData,
                    media=mediaInfo,
                    host=config['config']['url'],
                    desc=embedDesc,
                    urlEncodedDesc=urllib.parse.quote(embedDesc),
                    tweetLink=f'https://twitter.com/{tweetData["user_screen_name"]}/status/{tweetData["tweetID"]}',
                    appname=appName,
                    color=config['config']['color'],
                    sicon="video",
                    activityLink=generateActivityLink(tweetData,mediaInfo['url'],"video/mp4",embedIndex)
                    )

def renderTextTweetEmbed(tweetData,appnameSuffix=""):
    qrt = tweetData['qrt']
    embedDesc = msgs.formatEmbedDesc("Text",tweetData['text'],qrt,tweetData['pollData'])

    return render_template("text.html",
                    tweet=tweetData,
                    host=config['config']['url'],
                    desc=embedDesc,
                    urlEncodedDesc=urllib.parse.quote(embedDesc),
                    tweetLink=f'https://twitter.com/{tweetData["user_screen_name"]}/status/{tweetData["tweetID"]}',
                    appname=getAppName(tweetData,appnameSuffix),
                    color=config['config']['color'],
                    activityLink=generateActivityLink(tweetData),
                    sicon="text"
                    )

def renderArticleTweetEmbed(tweetData,appnameSuffix=""):
    articlePreview=tweetData['article']["title"]+"\n\n"+tweetData['article']["preview_text"]+"…"
    embedDesc = msgs.formatEmbedDesc("Image",articlePreview,None,None)

    return render_template("image.html",
                    tweet=tweetData,
                    pic=[tweetData['article']["image"]],
                    host=config['config']['url'],
                    desc=embedDesc,
                    urlEncodedDesc=urllib.parse.quote(embedDesc),
                    tweetLink=f'https://twitter.com/{tweetData["user_screen_name"]}/status/{tweetData["tweetID"]}',
                    appname=getAppName(tweetData,appnameSuffix),
                    color=config['config']['color'],
                    sicon="image"
                    )

def renderUserEmbed(userData,appnameSuffix=""):
    return render_template("user.html",
                    user=userData,
                    host=config['config']['url'],
                    desc=userData["description"],
                    urlEncodedDesc=urllib.parse.quote(userData["description"]),
                    link=f'https://twitter.com/{userData["screen_name"]}',
                    appname=config['config']['appname'],
                    color=config['config']['color']
                    )

@app.route('/robots.txt')
def robots():
    return "User-agent: *\nDisallow: /"

@app.route('/') # If the useragent is discord, return the embed, if not, redirect to configured repo directly
def default():
    return redirect(config['config']['repo'], 301)

@app.route('/oembed.json') #oEmbed endpoint
def oembedend():
    desc  = request.args.get("desc", None)
    user  = request.args.get("user", None)
    link  = request.args.get("link", None)
    ttype = request.args.get("ttype", None)
    provName = request.args.get("provider",None)
    return  oEmbedGen(desc, user, link, ttype,providerName=provName)

@app.route('/activity.json')
def activity():
    tweetId = request.args.get("id", None)
    publishedDate = request.args.get("published", None)
    likes = request.args.get("likes", None)
    retweets = request.args.get("retweets", None)
    userAttrTo = request.args.get("user", None)
    content = request.args.get("content", None)
    attachments = json.loads(request.args.get("attachments", "[]"))

    ##

    attachmentsRaw = []
    for attachment in attachments:
        attachmentsRaw.append({
            "type": "Document",
            "mediaType": attachment["type"],
            "url": attachment["url"],
            "preview_url": "https://pbs.twimg.com/ext_tw_video_thumb/1906073839441735680/pu/img/2xqg6tlK9mK0mSOR.jpg",
    })

    return {
        "id": "https://x.com/i/status/"+tweetId,
        "type": "Note",
        "summary": None,
        "inReplyTo": None,
        "published": publishedDate,
        "url": "https://x.com/i/status/"+tweetId,
        "attributedTo": userAttrTo,
        "content": content,
        "attachment": attachmentsRaw,
        "likes": {
            "type": "Collection",
            "totalItems": int(likes)
        },
        "shares": {
            "type": "Collection",
            "totalItems": int(retweets)
        },
    }

@app.route('/user.json')
def userJson():

    screen_name = request.args.get("screen_name", None)
    name = request.args.get("name", None)
    pfp = request.args.get("pfp", None)

    return {
        "id": screen_name,
        "type": "Person",
        "preferredUsername": screen_name,
        "name": name,
        "summary": "",
        "url": "https://x.com/"+screen_name,
        "tag": [],
        "attachment": [],
        "icon": {
            "type": "Image",
            "mediaType": "image/jpeg",
            "url": pfp
        },
    }

def getTweetData(twitter_url,include_txt="false",include_rtf="false"):
    cachedVNF = getVnfFromLinkCache(twitter_url)
    if cachedVNF is not None and include_txt == "false" and include_rtf == "false":
        return cachedVNF

    try:
        if config['config']['workaroundTokens'] is not None:
            workaroundTokens = config['config']['workaroundTokens'].split(",")
        else:
            workaroundTokens = None
        rawTweetData = twExtract.extractStatus(twitter_url,workaroundTokens=workaroundTokens)
    except:
        rawTweetData = None
    if rawTweetData == None or 'error' in rawTweetData:
        return None

    if rawTweetData is None:
        return None
    tweetData = getApiResponse(rawTweetData,include_txt,include_rtf)
    if tweetData is None:
        return None
    if include_txt == "false" and include_rtf == "false":
        addVnfToLinkCache(twitter_url,tweetData)
    return tweetData

def getUserData(twitter_url,includeFeed=False):
    if config['config']['workaroundTokens'] is not None:
        workaroundTokens = config['config']['workaroundTokens'].split(",")
    else:
        workaroundTokens = None
    rawUserData = twExtract.extractUser(twitter_url,workaroundTokens=workaroundTokens)
    userData = getApiUserResponse(rawUserData)

    if includeFeed:
        if userData['protected']:
            userData['latest_tweets']=[]
        else:
            feed = twExtract.extractUserFeedFromId(userData['id'],workaroundTokens=workaroundTokens)
            apiFeed = []
            for tweet in feed:
                apiFeed.append(getApiResponse(tweet))
            userData['latest_tweets'] = apiFeed

    return userData

@app.route('/<path:sub_path>') # Default endpoint used by everything
def twitfix(sub_path):
    global user_agent
    user_agent = request.headers.get('User-Agent', None)
    if user_agent is None:
        user_agent = "unknown"

    isApiRequest=request.url.startswith("https://api.vx") or request.url.startswith("http://api.vx")
    if not isApiRequest and (request.url.startswith("https://l.vx") or request.url.startswith("https://old.vx")) and "Discord" in user_agent:
        user_agent = user_agent.replace("Discord","LegacyEmbed") # TODO: Clean up; This is a hacky fix to make the new activity embed not trigger
    if sub_path in staticFiles:
        if 'path' not in staticFiles[sub_path] or staticFiles[sub_path]["path"] == None:
            staticFiles[sub_path]["path"] = sub_path
        return send_from_directory(os.path.join(app.root_path, 'static'), staticFiles[sub_path]["path"], mimetype=staticFiles[sub_path]["mime"])
    if sub_path.startswith("status/"): # support for /status/1234567890 URLs
        sub_path = "i/" + sub_path
    match = pathregex.search(sub_path)
    if match is None:
        # test for .com/username
        if sub_path.count("/") == 0:
            username=sub_path
            extra=None
        else:
            # get first subpath
            username=sub_path.split("/")[0]
            extra = sub_path.split("/")[1]
        if extra in [None,"with_replies","media","likes","highlights","superfollows","media",''] and username != "" and username != None:
            try:
                userData = getUserData(f"https://twitter.com/{username}","with_tweets" in request.args)
            except twExtract.TwExtractError as e:
                if isApiRequest:
                    status=500
                    if 'not found' in e.msg:
                        status=404
                    return Response(json.dumps({"error": e.msg}), status=status,mimetype='application/json')
                return message("Error getting user data: "+str(e.msg))
            if isApiRequest:
                if userData is None:
                    abort(404)
                return userData
            else:
                if userData is None:
                    return message(msgs.failedToScan)
                return renderUserEmbed(userData)
        abort(404)
    twitter_url = f'https://twitter.com/i/status/{getTweetIdFromUrl(sub_path)}'

    include_txt="false"
    include_rtf="false"

    if isApiRequest:
        if "include_txt" in request.args:
            include_txt = request.args.get("include_txt")
        if "include_rtf" in request.args:
            include_rtf = request.args.get("include_rtf")

    tweetData = getTweetData(twitter_url,include_txt,include_rtf)
    if tweetData is None:
        log.error("Tweet Data Get failed for "+twitter_url)
        return message(msgs.failedToScan)
    qrt = None
    if 'qrtURL' in tweetData and tweetData['qrtURL'] is not None:
        qrt = getTweetData(tweetData['qrtURL'])
    tweetData['qrt'] = qrt

    retweet = None
    if 'retweetURL' in tweetData and tweetData['retweetURL'] is not None:
        retweet = getTweetData(tweetData['retweetURL'])
    tweetData['retweet'] = retweet

    tweetData = deepcopy(tweetData)
    log.success("Tweet Data Get success")
    if '?' in request.url:
        requestUrlWithoutQuery = request.url.split("?")[0]
    else:
        requestUrlWithoutQuery = request.url

    directEmbed=False
    if requestUrlWithoutQuery.startswith("https://d.vx") or requestUrlWithoutQuery.endswith(".mp4") or requestUrlWithoutQuery.endswith(".png"):
        directEmbed = True
        # remove the .mp4 from the end of the URL
        if requestUrlWithoutQuery.endswith(".mp4") or requestUrlWithoutQuery.endswith(".png"):
            sub_path = sub_path[:-4]
    elif requestUrlWithoutQuery.endswith(".txt"):
        return Response(tweetData['text'], mimetype='text/plain')
    elif requestUrlWithoutQuery.endswith(".rtf"):
        doc = Document()
        section = Section()
        doc.Sections.append(section)
        p = Paragraph()
        p.append(tweetData['text'])
        section.append(p)
        rtf = StringIO()
        doc.write(rtf)
        rtf.seek(0)
        return send_file(BytesIOWrapper(rtf), mimetype='application/rtf', as_attachment=True, download_name=f'{tweetData["user_screen_name"]}_{tweetData["tweetID"]}.rtf')

    embedIndex = -1
    # if url ends with /1, /2, /3, or /4, we'll use that as the index
    if sub_path[-2:] in ["/1","/2","/3","/4"]:
        embedIndex = int(sub_path[-1])-1
        sub_path = sub_path[:-2]
        
    if isApiRequest: # Directly return the API response if the request is from the API
        return tweetData
    elif directEmbed: # direct embed
        embeddingMedia = tweetData['hasMedia']
        renderMedia = None
        if embeddingMedia:
            renderMedia = determineMediaToEmbed(tweetData,embedIndex,convertGif=False)
        # direct embeds should always prioritize the main tweet, so don't check for qrt
        # determine what type of media we're dealing with
        if not embeddingMedia and qrt is None:
            return renderTextTweetEmbed(tweetData)
        else:
            if renderMedia['type'] == "image":
                return Response(render_template("rawimage.html",media=renderMedia),headers={"Cache-Tag": "embed"})
            elif renderMedia['type'] == "video" or renderMedia['type'] == "gif":
                return Response(render_template("rawvideo.html",media=renderMedia),headers={"Cache-Tag": "embed"})
    else: # full embed
        embedTweetData = determineEmbedTweet(tweetData)
        embeddingMedia = embedTweetData['hasMedia']
        
        if "article" in embedTweetData and embedTweetData["article"] is not None:
            return Response(renderArticleTweetEmbed(tweetData," • See original tweet for full article"),headers={"Cache-Tag": "embed"})
        elif not embeddingMedia:
            return Response(renderTextTweetEmbed(tweetData),headers={"Cache-Tag": "embed"})
        else:
            tryGifConversion = "Discord" in user_agent
            media = determineMediaToEmbed(embedTweetData,embedIndex,convertGif=tryGifConversion)
            suffix=""
            if "suffix" in media:
                suffix = media["suffix"]
            if media['type'] == "image":
                return Response(renderImageTweetEmbed(tweetData,media['url'] , appnameSuffix=suffix,embedIndex=embedIndex),headers={"Cache-Tag": "embed"})
            elif media['type'] == "video":
                return Response(renderVideoTweetEmbed(tweetData,media,appnameSuffix=suffix,embedIndex=embedIndex),headers={"Cache-Tag": "embed"})
            elif media['type'] == "gif":
                if "originalUrl" in media and media["url"] != media["originalUrl"] and tryGifConversion:
                    return Response(renderImageTweetEmbed(tweetData,media['url'] , appnameSuffix=suffix,embedIndex=embedIndex),headers={"Cache-Tag": "embed"})
                else:
                    return Response(renderVideoTweetEmbed(tweetData,media,appnameSuffix=suffix,embedIndex=embedIndex),headers={"Cache-Tag": "embed"})

    return message(msgs.failedToScan)



@app.route('/tvid/<path:vid_path>')
def tvid(vid_path):
    url = f"https://video.twimg.com/{vid_path}.mp4"
    return redirect(url, 302)

@app.route("/rendercombined.jpg")
def rendercombined():
    # get "imgs" from request arguments
    imgs = request.args.get("imgs", "")

    if remoteCombine:
        # Redirecting here instead of setting the embed URL directly to this because if the config combination_method changes in the future, old URLs will still work
        url = config['config']['combination_method'] + "/rendercombined.jpg?imgs=" + imgs
        return redirect(url, 302)

    imgs = imgs.split(",")
    if (len(imgs) == 0 or len(imgs)>4):
        abort(400)
    #check that each image starts with "https://pbs.twimg.com"
    for img in imgs:
        result = urlparse(img)
        if result.hostname != "pbs.twimg.com" or result.scheme != "https":
            abort(400)
    finalImg= combineImg.genImageFromURL(imgs)
    imgIo = BytesIO()
    finalImg = finalImg.convert("RGB")
    finalImg.save(imgIo, 'JPEG',quality=70)
    imgIo.seek(0)
    return send_file(imgIo, mimetype='image/jpeg',max_age=86400)

@app.route("/api/v1/statuses/<string:tweet_id>")
def api_v1_status(tweet_id):
    embedIndex = int(tweet_id[0])-1
    tweet_id = int(tweet_id[1:])
    twitter_url=f"https://twitter.com/i/status/{tweet_id}"
    tweetData = getTweetData(twitter_url)
    if tweetData is None:
        log.error("Tweet Data Get failed for "+twitter_url)
        return message(msgs.failedToScan)
    qrt = None
    if 'qrtURL' in tweetData and tweetData['qrtURL'] is not None:
        qrt = getTweetData(tweetData['qrtURL'])
    tweetData['qrt'] = qrt

    retweet = None
    if 'retweetURL' in tweetData and tweetData['retweetURL'] is not None:
        retweet = getTweetData(tweetData['retweetURL'])
    tweetData['retweet'] = retweet

    if tweetData is None:
        abort(500) # this should cause Discord to fall back to the default embed
    return activitymg.tweetDataToActivity(tweetData,embedIndex)

def oEmbedGen(description, user, video_link, ttype,providerName=None):
    if providerName == None:
        providerName = config['config']['appname']
    out = {
            "type"          : ttype,
            "version"       : "1.0",
            "provider_name" : providerName,
            "provider_url"  : config['config']['repo'],
            "title"         : description,
            "author_name"   : user,
            "author_url"    : video_link
            }

    return out

if __name__ == "__main__":
    app.config['SERVER_NAME']='localhost:80'
    app.run(host='0.0.0.0')
