import datetime
import msgs
from utils import determineEmbedTweet, determineMediaToEmbed
from copy import deepcopy

def tweetDataToActivity(tweetData,embedIndex = -1):
    content=""

    if tweetData['replyingTo'] is not None:
        content += f"<blockquote>↪️ <i>Replying to @{tweetData['replyingTo']}</i></blockquote>"
    content+=f"<p>{tweetData['text']}</p>"

    attachments=[]
    if tweetData['qrt'] is not None:
        content += f"<blockquote><b>QRT: <a href=\"{tweetData['qrtURL']}\">{tweetData['qrt']['user_screen_name']}</a></b><br>{tweetData['qrt']['text']}</blockquote>"
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
    media = None
    if embeddingMedia:
        media = determineMediaToEmbed(embedTweetData,embedIndex)

    if media is not None:
        media = deepcopy(media)
        if media['type'] == "gif":
            if "/convert.avif" in media['url']:
                media['type'] = "image"
            else:
                media['type'] = "gifv"
        if 'thumbnail_url' not in media:
            media['thumbnail_url'] = media['url']
        if media['type'] == "image" and "?" not in media['url']:
            media['url'] += "?name=orig"
        attachments.append({
            "id": "114163769487684704",
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
	"language": "en",
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