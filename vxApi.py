import html
from datetime import datetime
from flask import json
from configHandler import config
from utils import stripEndTCO

def getApiUserResponse(user):
    userResult = user["data"]["user"]["result"]
    return {
        "id": int(userResult["rest_id"]),
        "screen_name": userResult["core"]["screen_name"],
        "name": userResult["core"]["name"],
        "profile_image_url": userResult['avatar']["image_url"],
        "description": userResult["legacy"]["description"],
        "location": userResult["location"]["location"],
        "followers_count": userResult["legacy"]["followers_count"],
        "following_count": userResult["legacy"]["friends_count"],
        "tweet_count": userResult["legacy"]["statuses_count"],
        "created_at": userResult["core"]["created_at"],
        "protected": userResult["privacy"]["protected"],
        "fetched_on": int(datetime.now().timestamp()),
    }

def getBestMediaUrl(mediaList):
    # find the highest bitrate
    best_bitrate = -1
    besturl=""
    for j in mediaList:
        if j['content_type'] == "video/mp4" and '/hevc/' not in j["url"] and j['bitrate'] > best_bitrate:
            besturl = j["url"]
            best_bitrate = j['bitrate']
    if "?tag=" in besturl:
        besturl = besturl[:besturl.index("?tag=")]
    return besturl

def getExtendedVideoOrGifInfo(mediaEntry):
    videoInfo = mediaEntry["video_info"]
    info = {
        "url": getBestMediaUrl(videoInfo["variants"]),
        "type": "gif" if mediaEntry.get("type", "") == "animated_gif" else "video",
        "size": {
            "width": mediaEntry['original_info']["width"],
            "height": mediaEntry['original_info']["height"]
        },
        "duration_millis": videoInfo.get("duration_millis", 0),
        "thumbnail_url": mediaEntry.get("media_url_https", None),
        "altText": mediaEntry.get("ext_alt_text", None),
        "id_str": mediaEntry.get("id_str", None)
    }
    return info

def getExtendedImageInfo(mediaEntry):
    info = {
        "url": mediaEntry.get("media_url_https", None),
        "type": "image",
        "size": {
            "width": mediaEntry["original_info"]["width"],
            "height": mediaEntry["original_info"]["height"]
        },
        "thumbnail_url": mediaEntry.get("media_url_https", None),
        "altText": mediaEntry.get("ext_alt_text", None),
        "id_str": mediaEntry.get("id_str", None)
    }
    return info
    
def getApiResponse(tweet,include_txt=False,include_rtf=False):
    tweetL = tweet["legacy"]
    if "user_result" in tweet["core"]:
        user = tweet["core"]["user_result"]["result"]
    elif "user_results" in tweet["core"]:
        user = tweet["core"]["user_results"]["result"]
    userL = user["legacy"]
    media=[]
    media_extended=[]
    hashtags=[]
    communityNote=None
    oldTweetVersion = False
    tweetArticle=None
    lang=None

    if "screen_name" not in userL:
        userL["screen_name"] = user["core"]["screen_name"]
    if "name" not in userL:
        userL["name"] = user["core"]["name"]
    if "profile_image_url_https" not in userL:
        userL["profile_image_url_https"] = user["avatar"]["image_url"]

    #editedTweet=False
    try:
        if "birdwatch_pivot" in tweet:
            if 'summary' in tweet["birdwatch_pivot"]["note"]:
                communityNote=tweet["birdwatch_pivot"]["note"]["summary"]["text"]
            elif 'subtitle' in tweet["birdwatch_pivot"] and 'text' in tweet["birdwatch_pivot"]["subtitle"]:
                communityNote=tweet["birdwatch_pivot"]["subtitle"]["text"]
    except:
        pass
    
    try:
        if "edit_control" in tweet and "edit_tweet_ids" in tweet["edit_control"]:
            #if len(tweet["edit_control"]['initial_tweet_id']) > 1:
            #    editedTweet = True
            lastEditID = tweet["edit_control"]["edit_tweet_ids"][-1]
            if lastEditID != tweet["rest_id"]:
                oldTweetVersion = True
    except:
        pass


    if "extended_entities" in tweetL:
        if "media" in tweetL["extended_entities"]:
            tmedia=tweetL["extended_entities"]["media"]
            for i in tmedia:
                extendedInfo={}
                if "video_info" in i:
                    extendedInfo = getExtendedVideoOrGifInfo(i)
                    media.append(extendedInfo["url"])
                    media_extended.append(extendedInfo)
                else:
                    extendedInfo = getExtendedImageInfo(i)
                    media_extended.append(extendedInfo)
                    media.append(extendedInfo["url"])

        if "hashtags" in tweetL["entities"]:
            for i in tweetL["entities"]["hashtags"]:
                hashtags.append(i["text"])
    elif "card" in tweet or "tweet_card" in tweet:
        cardData = tweet["card" if "card" in tweet else "tweet_card"]
        bindingValues = None
        if 'binding_values' in cardData:
            bindingValues = cardData['binding_values']
        elif 'legacy' in cardData and 'binding_values' in cardData['legacy']:
            bindingValues = cardData['legacy']['binding_values']
        if bindingValues != None:
            if 'name' in cardData and cardData['name'] == "player":
                width = None
                height = None
                vidUrl = None
                for i in bindingValues:
                    if i['key'] == 'player_stream_url':
                        vidUrl = i['value']['string_value']
                    elif i['key'] == 'player_width':
                        width = int(i['value']['string_value'])
                    elif i['key'] == 'player_height':
                        height = int(i['value']['string_value'])
                if vidUrl != None and width != None and height != None:
                    media.append(vidUrl)
                    media_extended.append({"url":vidUrl,"type":"video","size":{"width":width,"height":height}})
            else:
                for i in bindingValues:
                    if i['key'] == 'unified_card' and 'value' in i and 'string_value' in i['value']:
                        cardData = json.loads(i['value']['string_value'])
                        media_key = cardData['component_objects']['media_1']['data']['id']
                        media_entry = cardData['media_entities'][media_key]
                        extendedInfo = getExtendedVideoOrGifInfo(media_entry)
                        media.append(extendedInfo['url'])
                        media_extended.append(extendedInfo)
                        break
                    elif i['key'] == 'photo_image_full_size_large' and 'value' in i and 'image_value' in i['value']:
                        imgData = i['value']['image_value']
                        imgurl = imgData['url']
                        media.append(imgurl)
                        media_extended.append({"url":imgurl,"type":"image","size":{"width":imgData['width'],"height":imgData['height']}})
                        break
    if "article" in tweet:
        try:
            result = tweet["article"]["article_results"]["result"]
            apiArticle = {
                "title": result["title"],
                "preview_text": result["preview_text"],
                "image": None
            }
            if "cover_media" in result and "media_info" in result["cover_media"]:
                apiArticle["image"] = result["cover_media"]["media_info"]["original_img_url"]
            tweetArticle = apiArticle
        except:
            pass

    #include_txt = request.args.get("include_txt", "false")
    #include_rtf = request.args.get("include_rtf", "false") # for certain types of archival software (i.e Hydrus)

    if include_txt == True or include_txt == "true" or (include_txt == "ifnomedia" and len(media)==0):
        txturl = config['config']['url']+"/"+userL["screen_name"]+"/status/"+tweet["rest_id"]+".txt"
        media.append(txturl)
        media_extended.append({"url":txturl,"type":"txt"})
    if include_rtf == True or include_rtf == "true" or (include_rtf == "ifnomedia" and len(media)==0): 
        rtfurl = config['config']['url']+"/"+userL["screen_name"]+"/status/"+tweet["rest_id"]+".rtf"
        media.append(rtfurl)
        media_extended.append({"url":rtfurl,"type":"rtf"})

    qrtURL = None
    if 'quoted_status_id_str' in tweetL:
        qrtURL = "https://twitter.com/i/status/" + tweetL['quoted_status_id_str']

    retweetURL = None
    if 'retweeted_status_result' in tweetL:
        retweetURL = "https://twitter.com/i/status/" + tweetL['retweeted_status_result']['result']['rest_id']

    if 'possibly_sensitive' not in tweetL:
        tweetL['possibly_sensitive'] = False

    twText = html.unescape(tweetL["full_text"])

    if 'note_tweet' in tweet and tweet['note_tweet'] != None and 'note_tweet_results' in tweet['note_tweet']:
        noteTweet = tweet['note_tweet']['note_tweet_results']['result']
        if 'text' in noteTweet:
            twText = noteTweet['text']

    if 'entities' in tweetL and 'urls' in tweetL['entities']:
        for eurl in tweetL['entities']['urls']:
            if 'expanded_url' not in eurl:
                continue
            if "/status/" in eurl["expanded_url"] and eurl["expanded_url"].startswith("https://twitter.com/"):
                twText = twText.replace(eurl["url"], "")
            else:
                twText = twText.replace(eurl["url"],eurl["expanded_url"])
    twText = stripEndTCO(twText)

    # check if all extended media are the same type
    sameMedia = False
    if len(media_extended) > 1:
        sameMedia = True
        for i in media_extended:
            if i["type"] != media_extended[0]["type"]:
                sameMedia = False
                break
    else:
        sameMedia = True

    combinedMediaUrl = None
    if len(media_extended) > 0 and sameMedia and media_extended[0]["type"] == "image" and len(media) > 1:
        host=config['config']['url']
        combinedMediaUrl = f'{host}/rendercombined.jpg?imgs='
        for i in media:
            combinedMediaUrl += i + ","
        combinedMediaUrl = combinedMediaUrl[:-1]

    pollData = None
    card = None
    if 'card' in tweet and 'legacy' in tweet['card'] and tweet['card']['legacy']['name'].startswith("poll"):
        card = tweet['card']['legacy']
    elif 'card' in tweet and 'binding_values' in tweet['card']:
        card = tweet['card']

    if card != None:
        cardName = card['name']
        pollData={} # format: {"options":["name":"Option 1 Name","votes":5,"percent":50]}
        pollData["options"] = []
        totalVotes = 0
        bindingValues = card['binding_values']
        pollValues = {}
        for i in bindingValues:
            key = i["key"]
            value = i["value"]
            etype = value["type"]
            if etype == "STRING":
                pollValues[key] = value["string_value"]
            elif etype == "BOOLEAN":
                pollValues[key] = value["boolean_value"]
        for i in range(1,5):
            if f"choice{i}_label" in pollValues:
                option = {}
                option["name"] = pollValues[f"choice{i}_label"]
                option["votes"] = int(pollValues[f"choice{i}_count"])
                totalVotes += option["votes"]
                pollData["options"].append(option)
        for i in pollData["options"]:
            i["percent"] = round((i["votes"]/totalVotes)*100,2) if totalVotes > 0 else 0
        
    if 'lang' in tweetL:
        lang = tweetL['lang']

    replyingTo = None
    if 'in_reply_to_screen_name' in tweetL and tweetL['in_reply_to_screen_name'] != None:
        replyingTo = tweetL['in_reply_to_screen_name']

    replyingToID = None
    if 'in_reply_to_status_id_str' in tweetL and tweetL['in_reply_to_status_id_str'] != None:
        replyingToID = tweetL['in_reply_to_status_id_str']

    apiObject = {
        "text": twText,
        "likes": tweetL["favorite_count"],
        "retweets": tweetL["retweet_count"],
        "replies": tweetL["reply_count"],
        "date": tweetL["created_at"],
        "user_screen_name": html.unescape(userL["screen_name"]),
        "user_name": userL["name"],
        "user_profile_image_url": userL["profile_image_url_https"],
        "tweetURL": "https://twitter.com/"+userL["screen_name"]+"/status/"+tweet["rest_id"],
        "tweetID": tweet["rest_id"],
        "conversationID": tweetL["conversation_id_str"],
        "mediaURLs": media,
        "media_extended": media_extended,
        "possibly_sensitive": tweetL["possibly_sensitive"],
        "hashtags": hashtags,
        "qrtURL": qrtURL,
        "communityNote": communityNote,
        "allSameType": sameMedia,
        "hasMedia": len(media) > 0,
        "combinedMediaUrl": combinedMediaUrl,
        "pollData": pollData,
        "article": tweetArticle,
        "lang": lang,
        "replyingTo": replyingTo,
        "replyingToID": replyingToID,
        "fetched_on": int(datetime.now().timestamp()),
        "retweetURL":retweetURL,
    }
    try:
        apiObject["date_epoch"] = int(datetime.strptime(tweetL["created_at"], "%a %b %d %H:%M:%S %z %Y").timestamp())
    except:
        pass

    return apiObject
