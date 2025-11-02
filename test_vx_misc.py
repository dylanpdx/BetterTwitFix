import twitfix, cache, twExtract, utils
from vx_testdata import *
from twExtract import twUtils

def test_calcSyndicationToken():
    assert twUtils.calcSyndicationToken("1691389765483200513") == "43lnobuxzql"

def test_stripEndTCO():
    assert utils.stripEndTCO("Hello World https://t.co/abc123") == "Hello World"
    assert utils.stripEndTCO("Hello\nWorld https://t.co/abc123") == "Hello\nWorld"
    assert utils.stripEndTCO("Hello\nWorld\nhttps://t.co/abc123") == "Hello\nWorld"
    assert utils.stripEndTCO("Hello\nWorld\n https://t.co/abc123") == "Hello\nWorld"
    assert utils.stripEndTCO("Hello\nWorld \nhttps://t.co/abc123") == "Hello\nWorld"

def test_addToCache():
    cache.clearCache()
    twitfix.getTweetData(testTextTweet)
    twitfix.getTweetData(testVideoTweet)
    twitfix.getTweetData(testMediaTweet)
    twitfix.getTweetData(testMultiMediaTweet)
    #retrieve
    compareDict(videoRedirect(testTextTweet_compare),videoRedirect(cache.getVnfFromLinkCache(testTextTweet)))
    compareDict(videoRedirect(testVideoTweet_compare),videoRedirect(cache.getVnfFromLinkCache(testVideoTweet)))
    compareDict(videoRedirect(testMediaTweet_compare),videoRedirect(cache.getVnfFromLinkCache(testMediaTweet)))
    compareDict(videoRedirect(testMultiMediaTweet_compare),videoRedirect(cache.getVnfFromLinkCache(testMultiMediaTweet)))
    cache.clearCache()