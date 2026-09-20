import datetime
import msgs
from utils import determineEmbedTweet, determineMediaToEmbed, mediaToGifConvert
from copy import deepcopy
import html

def tweetDataToActivity(tweetData,embedIndex = -1):
    content=""

    if tweetData['replyingTo'] is not None:
        content += f"<blockquote>↪️ <i>Replying to @{tweetData['replyingTo']}</i></blockquote>"

    mainText = html.escape(tweetData['text'])
    if tweetData["translation"] is not None:
        content += f"<blockquote>🌐 <i>{tweetData['translation']['source_language'].upper()}→{tweetData['translation']['destination_language'].upper()}</i></blockquote>"
        mainText=html.escape(tweetData['translation']["text"])
        
    content+=f"<p>{mainText}</p>"

    attachments=[]
    if tweetData['qrt'] is not None:
        qrtText = html.escape(tweetData['qrt']['text'])
        if "translation" in tweetData['qrt'] and tweetData['qrt']["translation"] is not None:
            qrtText = html.escape(tweetData['qrt']["translation"]["text"])
        content += f"<blockquote><b>QRT: <a href=\"{tweetData['qrtURL']}\">{tweetData['qrt']['user_screen_name']}</a></b><br>{qrtText}</blockquote>"
    if tweetData['pollData'] is not None:
        content += f"<p>{msgs.genPollDisplay(tweetData['pollData'])}</p>"
        content += "</p>"
    content = content.replace("\n","<br>")
    #if media is not None:
    #    attachments.append({"type":mediatype,"url":media})
    likes = tweetData['likes']
    retweets = tweetData['retweets']

    # convert date epoch to iso format
    date = tweetData['date_epoch']
    date = datetime.datetime.fromtimestamp(date).isoformat() + "Z"

    embedTweetData = determineEmbedTweet(tweetData)
    embeddingMedia = embedTweetData['hasMedia']
    allMedia = embedTweetData["media_extended"]
    #if embeddingMedia:
    #    media = determineMediaToEmbed(embedTweetData,embedIndex)
    gallery_mode = False
    if embedIndex >= 0:
        allMedia = [determineMediaToEmbed(embedTweetData,embedIndex)]
    elif len(allMedia) > 0 and allMedia[0]["type"] == "video":
        allMedia = [allMedia[0]]
    else:
        galleryMedia = []
        for media in allMedia:
            if media["type"] == "image":
                galleryMedia.append(media)
            elif media["type"] == "gif":
                converted = mediaToGifConvert(deepcopy(media))
                if converted["url"] != media["url"] or "/convert.avif?url=" in media["url"]:
                    galleryMedia.append(media)
        if len(galleryMedia) > 0:
            allMedia = galleryMedia
            gallery_mode = True
        elif len(allMedia) > 0:
            allMedia = [determineMediaToEmbed(embedTweetData)]

    for media in allMedia:
        if media is not None:
            media = deepcopy(media)
            if media['type'] == "gif":
                original_url = media['url']
                if  media['type'] == "gif":
                    media = mediaToGifConvert(media)
                if media['url'] == original_url and "/convert.avif?url=" not in media['url']:
                    if gallery_mode:
                        continue
                    media['type'] = "gifv"
                if "/convert.avif" in media['url']:
                    media['type'] = "image"
                elif media['type'] == "gif":
                    media['type'] = "gifv"
            if 'thumbnail_url' not in media:
                media['thumbnail_url'] = media['url']
            if media['type'] == "image" and "?" not in media['url']:
                media['url'] += "?name=orig"
            attachments.append({
                "id": "100000000000000000",
                "type": media['type'],
                "url": media['url'],
                "preview_url": media['thumbnail_url'],
            })

    # https://docs.joinmastodon.org/methods/statuses/
    return {
	"id": tweetData['tweetID'],
	"url": f"https://x.com/{tweetData['user_screen_name']}/status/{tweetData['tweetID']}",
	"uri": f"https://x.com/{tweetData['user_screen_name']}/status/{tweetData['tweetID']}",
	"created_at": date,
	"edited_at": None,
	"reblog": None,
	"in_reply_to_account_id": None,
    "language": tweetData.get("lang", "en"),
	"content": content,
	"spoiler_text": "",
	"visibility": "public",
	"application": {
		"website": None
	},
	"media_attachments": attachments,
	"account": {
		"display_name": tweetData['user_name'],
		"username": tweetData['user_screen_name'],
		"acct": tweetData['user_screen_name'],
		"url": f"https://x.com/{tweetData['user_screen_name']}/status/{tweetData['tweetID']}",
		"uri": f"https://x.com/{tweetData['user_screen_name']}/status/{tweetData['tweetID']}",
		"locked": False,
		"avatar": tweetData['user_profile_image_url'],
		"avatar_static": tweetData['user_profile_image_url'],
		"hide_collections": False,
		"noindex": False,
	},
}