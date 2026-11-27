import uuid
import json
import requests
import re
import os
import random
import urllib.parse
import time
from oauthlib import oauth1
import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
import twUtils
import twStats
from methods import *

requestUserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:153.0) Gecko/20100101 Firefox/153.0"

bearerTokens=[bearer,v2bearer,androidBearer]

guestToken=None
guestTokenUses=0
pathregex = r"\w{1,15}\/(status|statuses)\/(\d{2,20})"
userregex = r"^https?:\/\/(?:www\.)?twitter\.com\/(?:#!\/)?@?([^/?#]*)(?:[?#/].*)?$"
userIDregex = r"\/i\/user\/(\d+)"


twitterUrl = "x.com" # doubt this will change but just in case

def cycleBearerTokenGet(url,headers):
    global bearerTokens
    rateLimitRemaining = None
    tweet = None
    for token in bearerTokens:
        headers["Authorization"] = token
        try:
            tweet = requests.get(url, headers=headers)
            try:
                rateLimitRemaining = tweet.headers.get("x-rate-limit-remaining")
            except: # for some reason the header is not always present
                pass
            if tweet.status_code == 429 and rateLimitRemaining is not None and int(rateLimitRemaining) > 0: # special case where the bearer token is rate limited but another one is not
                # try another bearer token
                print(f"Error 429 but {rateLimitRemaining} remaining")
                continue
            else:
                # move successful token to the front if it's not already there
                if token != bearerTokens[0]:
                    bearerTokens.insert(0,bearerTokens.pop(bearerTokens.index(token)))
                return tweet
        except Exception as e:
            continue
    if tweet is not None: # every token was rate limited; return the last response
        return tweet
    raise TwExtractError(400, "Extract error")

def twitterApiGet(url,btoken=None,authToken=None,guestToken=None,userAgent=None,language=None):

    if authToken != None and authToken.startswith("oa|"):
        url = url.replace("https://x.com/i/api/graphql/","https://api.twitter.com/graphql/")
        authToken = authToken[3:]
        key = authToken.split("|")[0]
        secret = authToken.split("|")[1]

        twt = oauth1.Client(client_key='3nVuSoBZnx6U4vzUxf5w',client_secret='Bcs59EFbbsdF6Sl9Ng71smgStWEGwXXKSjYvPVt7qys',resource_owner_key=key,resource_owner_secret=secret)
        hdr = getAuthHeaders(androidBearer,language=language)
        del hdr["Authorization"]
        hdr["X-Twitter-Client"] = "TwitterAndroid"
        if userAgent is not None:
            hdr["User-Agent"] = userAgent

        uri, headers, body = twt.sign(url, headers=hdr,realm="http://api.twitter.com/")

        response = requests.get(url,headers=headers)
    else:
        if btoken is None:
            btoken = v2bearer
            #return cycleBearerTokenGet(url,getAuthHeaders(bearer,authToken=authToken,guestToken=guestToken))
        headers = getAuthHeaders(btoken,authToken=authToken,guestToken=guestToken,language=language)
        response = requests.get(url, headers=headers)

    return response

def getAuthHeaders(btoken,authToken=None,guestToken=None,language=None):

    csrfToken=str(uuid.uuid4()).replace('-', '')
    headers = {"x-twitter-active-user":"yes","x-twitter-client-language":"en","x-csrf-token":csrfToken,"User-Agent":requestUserAgent}
    headers['Authorization'] = btoken

    if authToken is not None:
        headers["Cookie"] = f"auth_token={authToken}; ct0={csrfToken}; "
        headers["x-twitter-auth-type"] = "OAuth2Session"
    if guestToken is not None:
        headers["x-guest-token"] = guestToken

    if language is not None:
        headers["x-twitter-client-language"] = language

    return headers

def getGuestToken():
    global guestToken
    global guestTokenUses
    if guestToken is None:
        r = requests.post(f"https://api.{twitterUrl}/1.1/guest/activate.json", headers={"Authorization":v2bearer,"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:153.0) Gecko/20100101 Firefox/153.0"})
        guestToken = json.loads(r.text)["guest_token"]
        guestTokenUses = 0
    else:
        guestTokenUses+=1
        if guestTokenUses > 40:
            gtTemp = guestToken
            guestToken = None
            guestTokenUses = 0
            return gtTemp
    return guestToken

def extractStatus_token(url,workaroundTokens):
    # get tweet ID
    m = re.search(pathregex, url)
    if m is None:
        raise TwExtractError(400, "Extract error")
    twid = m.group(2)
    if workaroundTokens == None:
        raise TwExtractError(400, "Extract error (no tokens defined)")
    # get tweet
    tokens = workaroundTokens
    random.shuffle(tokens)
    for authToken in tokens:
        try:
            
            tweet = requests.get(f"https://api.{twitterUrl}/1.1/statuses/show/" + twid + ".json?tweet_mode=extended&cards_platform=Web-12&include_cards=1&include_reply_count=1&include_user_entities=0", headers=getAuthHeaders(bearer,authToken=authToken))
            output = tweet.json()
            if "errors" in output:
                # try another token
                continue
        except Exception as e:
            continue
        return output
    raise TwExtractError(400, "Extract error")

def extractStatus_guestToken(url):
    # get tweet ID
    m = re.search(pathregex, url)
    if m is None:
        raise TwExtractError(400, "Extract error (url not valid)")
    twid = m.group(2)
    # get guest token
    guestToken = getGuestToken()
    # get tweet
    tweet = requests.get(f"https://api.{twitterUrl}/1.1/statuses/show/" + twid + ".json?tweet_mode=extended&cards_platform=Web-12&include_cards=1&include_reply_count=1&include_user_entities=0", headers={"Authorization":bearer, "x-guest-token":guestToken})
    output = tweet.json()
    if "errors" in output:
        # pick the first error and create a twExtractError
        error = output["errors"][0]
        raise TwExtractError(error["code"], error["message"])
    return output

def extractStatus_syndication(url,workaroundTokens=None,tlLanguage=None):
    # https://github.com/mikf/gallery-dl/blob/46cae04aa3a113c7b6bbee1bb468669564b14ae8/gallery_dl/extractor/twitter.py#L1784
    m = re.search(pathregex, url)
    if m is None:
        raise TwExtractError(400, "Extract error")
    twid = m.group(2)
    tweet = requests.get("https://cdn.syndication.twimg.com/tweet-result?id=" + twid+"&token="+twUtils.calcSyndicationToken(twid))
    
    
    if tweet.status_code == 404:
        raise TwExtractError(404, "Tweet not found")
    output = tweet.json()
    if "errors" in output:
        # pick the first error and create a twExtractError
        error = output["errors"][0]
        raise TwExtractError(error["code"], error["message"])
    
    # change returned data to match the one from the other methods
    output['full_text'] = output['text']
    output['user']['profile_image_url'] = output['user']['profile_image_url_https']
    output['retweet_count']=0
    if 'mediaDetails' in output:
        output['extended_entities'] = {'media':output['mediaDetails']}
        for media in output['extended_entities']['media']:
            media['media_url'] = media['media_url_https']
    if 'quoted_tweet' in output:
        output['quoted_status'] = output['quoted_tweet']
        quotedID=output['quoted_tweet']['id_str']
        quotedScreenName=output['quoted_tweet']['user']['screen_name']
        output['quoted_status_permalink'] = {'expanded':f"https://{twitterUrl}/{quotedScreenName}/status/{quotedID}"}

    #output['user']['']

    return output

def extractStatus_twExtractProxy(url,workaroundTokens=None):
    proxies = os.getenv("VXTWITTER_PROXIES",None)
    if proxies is None:
        raise TwExtractError(400, "Extract error")
    proxies = proxies.split(',')
    random.shuffle(proxies)
    for proxy in proxies:
        try:
            tweet = requests.get(f"{proxy}?url={urllib.parse.quote(url)}")
            output = tweet.json()
            if "errors" in output:
                # try another token
                continue
        except Exception as e:
            continue
        return output

def _tweet_id(url):
    m = re.search(pathregex, url)
    if m is None:
        raise TwExtractError(400, "Extract error (url not valid)")
    return m.group(2)

def _graphqlUrl(query, idInput):
    vars = dict(query["variables"])
    vars[query["id_key"]] = query["id_value"](idInput)
    requestUrl = f"https://x.com/i/api/graphql/{query['query_id']}/{query['operation']}?variables={urllib.parse.quote(json.dumps(vars))}&features={urllib.parse.quote(query['features'])}"
    if query.get("field_toggles"):
        requestUrl += f"&fieldToggles={urllib.parse.quote(query['field_toggles'])}"
    return requestUrl

def extractStatusGraphql(query, url, workaroundTokens=None, tlLanguage=None):
    name = query["name"]
    twid = _tweet_id(url)

    if query["auth"] != AUTH_NONE and workaroundTokens:
        tokens = random.sample(workaroundTokens, len(workaroundTokens))
    elif query["auth"] == AUTH_REQUIRED:
        raise TwExtractError(400, f"{name}: Extract error (no tokens defined)")
    else:
        tokens = [None]

    requestUrl = _graphqlUrl(query, twid)
    guestToken = getGuestToken() if query["guest_token"] and tokens == [None] else None

    lastError = None
    for authToken in tokens:
        resultstatus = twStats.EXCEPTION
        rateLimitRemaining = None
        start = time.monotonic()
        try:
            response = twitterApiGet(requestUrl, btoken=query["bearer"], authToken=authToken, guestToken=guestToken, userAgent=query["user_agent"], language=tlLanguage)
            rateLimitRemaining = twStats.parse_rate_limit(response.headers.get('x-rate-limit-remaining'))
            print(f"[{name}] Rate limit remaining: {rateLimitRemaining}")
            if response.status_code == 429:
                resultstatus = twStats.RATE_LIMITED
                raise TwExtractError(400, f"{name}: rate limit reached")
            resultstatus = twStats.BAD_RESPONSE # this can happen with a 429
            output = response.json()
            if "errors" in output: # note: ERROR(S) not ERROR
                resultstatus = twStats.API_ERROR
                raise TwExtractError(400, f"{name}: errors in output - {json.dumps(output['errors'])}")
            resultstatus = twStats.PARSE_ERROR
            try:
                tweet = query["parser"](output, twid, **query["parser_args"])
            except TwExtractError:
                resultstatus = twStats.UNAVAILABLE
                raise
            if tweet is None:
                resultstatus = twStats.NOT_FOUND
                print(f"[{name}] Tweet 404")
                return {'error':'Tweet not found (404); May be due to invalid tweet, changes in Twitter\'s API, or a protected account.'}
            resultstatus = twStats.UNAVAILABLE if 'error' in tweet else twStats.OK # note: ERROR not ERROR(S), set in methods.py parser i.e parse_results_list
            # maybe 
            return tweet
        except Exception as e:
            print(f"[{name}] Request failed: {e}")
            lastError = e
            continue
        finally:
            twStats.record(name, resultstatus, (time.monotonic() - start) * 1000, rateLimitRemaining)
    raise TwExtractError(400, f"{name}: all tokens failed. Last error: {lastError}")

def fixTweetData(tweet):
    try:
        if 'user' not in tweet:
            tweet['user'] = tweet['core']['user_results']['result']['legacy']
    except:
        print("fixTweetData error: No user")
        pass

    try:
        if 'extended_entities' not in tweet and 'extended_entities' in tweet['legacy']:
            tweet['extended_entities'] = tweet['legacy']['extended_entities']
    except:
        print("fixTweetData error: extended_entities")
        pass
    return tweet

def extractStatus(url,workaroundTokens=None,tlLanguage=None):
    methods = GET_METHODS if tlLanguage is None else GET_METHODS_TL
    start = time.monotonic()
    for tried, method in enumerate(methods, 1):
        try:
            result = extractStatusGraphql(method, url, workaroundTokens, tlLanguage=tlLanguage)
            if 'legacy' not in result:
                print(f"{method['name']} method failed: Legacy not found for {url}")
                # try another method
                continue
            twStats.record_status(method['name'], True, (time.monotonic() - start) * 1000, tried)
            return fixTweetData(result)
        except Exception as e:
            print(f"{method['name']} method failed: {str(e)} for {url}")
            continue
    twStats.record_status(None, False, (time.monotonic() - start) * 1000, len(methods))
    raise TwExtractError(400, "Extract error")

def _isFinalUserError(e): # this user is p much a dead end 
    return isinstance(e, TwExtractError) and (e.code == 404 or 'suspended' in e.msg or e.msg == 'User not found.')

def _graphqlGet(query, requestUrl, authToken):
    if query.get("transaction_id"):
        headers = getAuthHeaders(query["bearer"], authToken=authToken)
        headers["x-client-transaction-id"] = twUtils.generate_transaction_id("GET", requestUrl.split("x.com", 1)[1].split("?", 1)[0])
        return requests.get(requestUrl, headers=headers)
    return twitterApiGet(requestUrl, btoken=query["bearer"], authToken=authToken, userAgent=query["user_agent"])

def _graphqlWithTokens(query, idInput, workaroundTokens, handle):
    name = query["name"]
    tokens = [t for t in (workaroundTokens or []) if not t.startswith("oa|")] # oauth token not supported atm
    if not tokens:
        raise TwExtractError(400, f"{name}: Extract error (no tokens defined)")
    requestUrl = _graphqlUrl(query, idInput)
    lastError = None
    for authToken in random.sample(tokens, len(tokens)):
        try:
            response = _graphqlGet(query, requestUrl, authToken)
            print(f"[{name}] Rate limit remaining: {response.headers.get('x-rate-limit-remaining')}")
            if response.status_code == 429:
                raise TwExtractError(429, f"{name}: rate limit reached")
            output = response.json()
            if "errors" in output:
                error = output["errors"][0]
                raise TwExtractError(error.get("code", 400), error.get("message", "Unknown error"))
            return handle(output)
        except Exception as e:
            if _isFinalUserError(e):
                raise
            print(f"[{name}] Request failed: {e}")
            lastError = e
    raise TwExtractError(400, f"{name}: all tokens failed. Last error: {lastError}")

def extractUserGraphql(query, userInput, workaroundTokens):
    def handle(output):
        user = query["parser"](output, **query["parser_args"])
        if user is None:
            raise TwExtractError(404, "User not found.")
        if user.get('__typename') == 'UserUnavailable':
            raise TwExtractError(404, user.get('message', 'User unavailable'))
        return {"data": {"user": {"result": user}}}
    return _graphqlWithTokens(query, userInput, workaroundTokens, handle)

def extractUser(url,workaroundTokens):
    m = re.search(userIDregex, url)
    if m is not None:
        methods = GET_USER_METHODS_ID
    else:
        m = re.search(userregex, url)
        if m is None:
            raise TwExtractError(400, "Invalid URL")
        methods = GET_USER_METHODS_SCREEN_NAME
    userInput = m.group(1)
    for method in methods:
        try:
            return extractUserGraphql(method, userInput, workaroundTokens)
        except Exception as e:
            if _isFinalUserError(e):
                raise
            print(f"{method['name']} user method failed: {e}")
    raise TwExtractError(400, "Extract error")

def extractUserFeedFromId(userId,workaroundTokens):
    for method in GET_FEED_METHODS:
        try:
            return _graphqlWithTokens(method, userId, workaroundTokens, lambda output: method["parser"](output, userId, **method["parser_args"]))
        except Exception as e:
            print(f"{method['name']} feed method failed: {e}")
    raise TwExtractError(400, "Extract error")

def lambda_handler(event, context):
    if ("queryStringParameters" not in event):
        return {
            "statusCode": 400,
            "body": "Invalid request."
        }
    url = event["queryStringParameters"].get("url","")
    return {
        'statusCode': 200,
        'body': extractStatus(url,workaroundTokens=os.getenv("VXTWITTER_WORKAROUND_TOKENS",None).split(','))
    }