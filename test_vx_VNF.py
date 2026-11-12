import twitfix
from vx_testdata import *

def getVNFFromLink(link):
    return twitfix.getTweetData(link)

## VNF conversion test ##
def test_textTweetVNF():
    vnf = getVNFFromLink(testTextTweet)
    compareDict(testTextTweet_compare,vnf)

def test_videoTweetVNF():
    vnf = getVNFFromLink(testVideoTweet)
    
    compareDict(testVideoTweet_compare,vnf)

def test_mediaTweetVNF():
    vnf = getVNFFromLink(testMediaTweet)
    compareDict(testMediaTweet_compare,vnf)

def test_multimediaTweetVNF():
    vnf = getVNFFromLink(testMultiMediaTweet)
    compareDict(testMultiMediaTweet_compare,vnf)

def test_pollTweetVNF():
    vnf = getVNFFromLink(testPollTweet)
    compareDict(testPollTweet_compare,vnf)

def test_20images():
    vnf = getVNFFromLink(test20Images)
    assert len(vnf["mediaURLs"]) == 20
    assert len(vnf["media_extended"]) == 20