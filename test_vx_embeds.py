import os

import twitfix,twExtract
import cache
from flask.testing import FlaskClient
from vx_testdata import *
client = FlaskClient(twitfix.app)

def test_embed_qrtTweet():
    cache.clearCache()
    # this is an incredibly lazy test, todo: improve it in the future
    resp = client.get(testQRTTweet.replace("https://twitter.com",""),headers={"User-Agent":"test"})
    assert resp.status_code==200
    assert testQRTTweet_compare['text'][:10] in str(resp.data)
    # test qrt-ception
    #resp = client.get(testQrtCeptionTweet.replace("https://twitter.com",""),headers={"User-Agent":"test"}) # get top level tweet
    #assert resp.status_code==200
    #assert "Please retweet this to spread awareness for retweets" in str(resp.data)
    #qtd_tweet=cache.getVnfFromLinkCache("https://twitter.com/EliLanger/status/585253161260216320") # check that the quoted tweet for the top level tweet is cached
    #assert qtd_tweet is not None
    #assert qtd_tweet["qrtURL"] is not None # check that the quoted tweet for the top level tweet has a qrtURL
    #assert cache.getVnfFromLinkCache("https://twitter.com/EliLanger/status/313143446842007553") is None # check that the bottom level tweet has NOT been cached
    #resp = client.get("/EliLanger/status/585253161260216320",headers={"User-Agent":"test"}) # get mid level tweet
    #assert resp.status_code==200
    #assert cache.getVnfFromLinkCache("https://twitter.com/EliLanger/status/313143446842007553") is not None # check that the bottom level tweet has been cached now

def test_embed_qrtVideoTweet():
    cache.clearCache()
    # this is an incredibly lazy test, todo: improve it in the future
    resp = client.get(testQrtVideoTweet.replace("https://twitter.com",""),headers={"User-Agent":"test"})
    assert resp.status_code==200
    #qtd_tweet=cache.getVnfFromLinkCache("https://twitter.com/i/status/1674197531301904388")
    #vurl = qtd_tweet["mediaURLs"][0]
    #assert f"twitter:player:stream\" content=\"{vurl}" in str(resp.data)

def test_embed_FromScratch():
    cache.clearCache()
    client.get(testTextTweet.replace("https://twitter.com",""),headers={"User-Agent":"test"})
    client.get(testVideoTweet.replace("https://twitter.com",""),headers={"User-Agent":"test"})
    client.get(testMediaTweet.replace("https://twitter.com",""),headers={"User-Agent":"test"})
    client.get(testMultiMediaTweet.replace("https://twitter.com",""),headers={"User-Agent":"test"})

def test_embed_User():
    cache.clearCache()
    resp = client.get(testUser.replace("https://twitter.com",""),headers={"User-Agent":"test"})
    assert resp.status_code==200

def test_embed_FromCache():
    cache.clearCache()
    twitfix.getTweetData(testTextTweet)
    twitfix.getTweetData(testVideoTweet)
    twitfix.getTweetData(testMediaTweet)
    twitfix.getTweetData(testMultiMediaTweet)
    #embed time
    resp = client.get(testTextTweet.replace("https://twitter.com",""),headers={"User-Agent":"test"})
    assert resp.status_code==200
    resp = client.get(testVideoTweet.replace("https://twitter.com",""),headers={"User-Agent":"test"})
    assert resp.status_code==200
    resp = client.get(testMediaTweet.replace("https://twitter.com",""),headers={"User-Agent":"test"})
    assert resp.status_code==200
    resp = client.get(testMultiMediaTweet.replace("https://twitter.com",""),headers={"User-Agent":"test"})
    assert resp.status_code==200

def test_embed_Suggestive():
    resp = client.get(testNSFWTweet.replace("https://twitter.com",""),headers={"User-Agent":"test"})
    assert resp.status_code==200
    assert "so i had a bot generate it for me" in str(resp.data)
    assert "FfF_gKwXgAIpnpD" in str(resp.data)

def test_embed_video_direct():
    resp = client.get(testVideoTweet.replace("https://twitter.com","")+".mp4",headers={"User-Agent":"test"})
    assert resp.status_code==200
    assert videoRedirect(testVideoTweet_compare)["mediaURLs"][0] in str(resp.data)

def test_embed_video_direct_subdomain():
    resp = client.get(testVideoTweet.replace("https://twitter.com","https://d.vxtwitter.com"),headers={"User-Agent":"test"})
    assert resp.status_code==200
    assert videoRedirect(testVideoTweet_compare)["mediaURLs"][0] in str(resp.data)

def test_embed_img_direct():
    resp = client.get(testMediaTweet.replace("https://twitter.com","")+".png",headers={"User-Agent":"test"})
    assert resp.status_code==200
    assert videoRedirect(testMediaTweet_compare)["mediaURLs"][0] in str(resp.data)

def test_embed_img_direct_subdomain():
    resp = client.get(testMediaTweet.replace("https://twitter.com","https://d.vxtwitter.com"),headers={"User-Agent":"test"})
    assert resp.status_code==200
    assert videoRedirect(testMediaTweet_compare)["mediaURLs"][0] in str(resp.data)

def test_embed_multi_direct():
    # embed first item
    resp = client.get(testMultiMediaTweet.replace("https://twitter.com","")+"/1.png",headers={"User-Agent":"test"})
    assert resp.status_code==200
    assert testMultiMediaTweet_compare["mediaURLs"][0] in str(resp.data)

    # embed second item
    resp = client.get(testMultiMediaTweet.replace("https://twitter.com","")+"/2.mp4",headers={"User-Agent":"test"})
    assert resp.status_code==200
    assert testMultiMediaTweet_compare["mediaURLs"][1] in str(resp.data)

def test_embed_multi_direct_subdomain():
    # generic embed
    resp = client.get(testMultiMediaTweet.replace("https://twitter.com","https://d.vxtwitter.com"),headers={"User-Agent":"test"})
    assert resp.status_code==200
    assert testMultiMediaTweet_compare["mediaURLs"][0] in str(resp.data)

    # embed first item
    resp = client.get(testMultiMediaTweet.replace("https://twitter.com","https://d.vxtwitter.com")+"/1",headers={"User-Agent":"test"})
    assert resp.status_code==200
    assert testMultiMediaTweet_compare["mediaURLs"][0] in str(resp.data)

    # embed second item
    resp = client.get(testMultiMediaTweet.replace("https://twitter.com","https://d.vxtwitter.com")+"/2",headers={"User-Agent":"test"})
    assert resp.status_code==200
    assert testMultiMediaTweet_compare["mediaURLs"][1] in str(resp.data)

def test_embed_message404():
    resp = client.get("https://twitter.com/jack/status/12345",headers={"User-Agent":"test"})
    assert resp.status_code==200
    assert "Failed to scan your link!" in str(resp.data)

def test_combine():
    twt = twitfix.getTweetData(testMultiMediaTweet)
    img1 = twt["mediaURLs"][0]
    img2 = twt["mediaURLs"][1]
    resp = client.get(f"/rendercombined.jpg?imgs={img1},{img2}",headers={"User-Agent":"test"})
    assert resp.status_code==200
    assert resp.headers["Content-Type"]=="image/jpeg"
    assert len(resp.data)>1000

def test_embed_combined():
    twt = twitfix.getTweetData(testMultiMediaTweet)
    img1 = twt["mediaURLs"][0]
    img2 = twt["mediaURLs"][1]
    resp = client.get(testMultiMediaTweet.replace("https://twitter.com",""),headers={"User-Agent":"test"})
    assert resp.status_code==200
    assert f"/rendercombined.jpg?imgs={img1},{img2}" in str(resp.data)

def test_embed_multimedia_single():
    twt = twitfix.getTweetData(testMultiMediaTweet)
    img1 = twt["mediaURLs"][0]
    img2 = twt["mediaURLs"][1]
    resp = client.get(testMultiMediaTweet.replace("https://twitter.com","")+"/1",headers={"User-Agent":"test"})
    assert resp.status_code==200
    assert img1 in str(resp.data) and img2 not in str(resp.data)
    resp = client.get(testMultiMediaTweet.replace("https://twitter.com","")+"/2",headers={"User-Agent":"test"})
    assert resp.status_code==200
    assert img1 not in str(resp.data) and img2 in str(resp.data)

def test_embed_mixedMedia():
    twt = videoRedirect(twitfix.getTweetData(testMixedMediaTweet))
    img1 = twt["mediaURLs"][0]
    img2 = twt["mediaURLs"][1]
    resp = client.get(testMixedMediaTweet.replace("https://twitter.com",""),headers={"User-Agent":"test"})

    # Check for default behavior with no index
    assert resp.status_code==200
    assert img1 in str(resp.data) and img2 not in str(resp.data)
    assert "Media 1/2" in str(resp.data) # make sure user knows there are multiple media

    resp = client.get(testMixedMediaTweet.replace("https://twitter.com","")+"/1",headers={"User-Agent":"test"})
    assert resp.status_code==200
    assert img1 in str(resp.data) and img2 not in str(resp.data)
    resp = client.get(testMixedMediaTweet.replace("https://twitter.com","")+"/2",headers={"User-Agent":"test"})
    assert resp.status_code==200
    assert img1 not in str(resp.data) and img2 in str(resp.data)

def test_embed_vine_player():
    resp = client.get(testVinePlayerTweet.replace("https://twitter.com",""),headers={"User-Agent":"test"})
    assert resp.status_code==200
    assert "v.cdn.vine.co" in str(resp.data)

def test_embed_poll():
    resp = client.get(testPollTweet.replace("https://twitter.com",""),headers={"User-Agent":"test"})
    assert resp.status_code==200
    assert "Mean one thing" in str(resp.data)
    assert "78.82%" in str(resp.data)

def test_embed_stripLastUrl():
    resp = client.get(testMediaTweet.replace("https://twitter.com",""),headers={"User-Agent":"test"})
    assert resp.status_code==200
    assert "HgLAbiXw2E" not in str(resp.data)

def test_embed_no_username():
    resp = client.get(testMediaTweet.replace("/pdxdylan",""),headers={"User-Agent":"test"})
    assert resp.status_code==200

def test_embed_txt():
    resp = client.get(testTextTweet.replace("https://twitter.com","")+".txt",headers={"User-Agent":"test"})
    assert resp.status_code==200
    assert testTextTweet_compare["text"] in str(resp.data)

def test_embed_rtf():
    resp = client.get(testTextTweet.replace("https://twitter.com","")+".rtf",headers={"User-Agent":"test"})
    assert resp.status_code==200
    assert testTextTweet_compare["text"] in str(resp.data)

def test_embed_action():
    cache.clearCache()
    resp = client.get(testTextTweet.replace("https://twitter.com",""),headers={"User-Agent":"test"})
    assert resp.status_code==200
    assert "application/activity+json" in str(resp.data)
    assert "%F0%9F%92%96" in str(resp.data) # 💖
    resp = client.get(testTextTweet.replace("https://twitter.com",""),headers={"User-Agent":"Mozilla/5.0 (compatible; Discordbot/2.0; +https://discordapp.com)"})
    assert resp.status_code==200
    assert "application/activity+json" in str(resp.data)
    assert "%F0%9F%92%96" not in str(resp.data) # 💖

def test_embed_translated():
    resp = client.get(testTextTweet.replace("https://twitter.com","")+"/jp",headers={"User-Agent":"test"})
    assert resp.status_code==200
    assert "→" in resp.text
    resp = client.get(testTextTweet.replace("https://twitter.com","")+"/ja",headers={"User-Agent":"test"})
    assert resp.status_code==200
    assert "→" in resp.text

def test_embed_translated_subdomain():
    resp = client.get(testTextTweet.replace("https://twitter.com","https://jp.vxtwitter.com"),headers={"User-Agent":"test"})
    assert resp.status_code==200
    assert "→" in resp.text
    resp = client.get(testTextTweet.replace("https://twitter.com","https://ja.vxtwitter.com"),headers={"User-Agent":"test"})
    assert resp.status_code==200
    assert "→" in resp.text