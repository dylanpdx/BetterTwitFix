from vx_testdata import *
import twitfix,twExtract
from flask.testing import FlaskClient
client = FlaskClient(twitfix.app)

def test_api_get_tweet():
    resp = client.get(testTextTweet.replace("https://twitter.com","https://api.vxtwitter.com")+"?include_txt=true",headers={"User-Agent":"test"})
    jData = resp.get_json()
    assert resp.status_code==200
    assert jData['text'] == 'just setting up my twttr'

def test_api_get_invalid_tweet():
    resp = client.get("https://vxtwitter.com/test/status/None",headers={"User-Agent":"test"})
    jData = resp.get_json()
    assert resp.status_code!=200

def test_api_include_txt():
    resp = client.get(testTextTweet.replace("https://twitter.com","https://api.vxtwitter.com")+"?include_txt=true",headers={"User-Agent":"test"})
    jData = resp.get_json()
    assert resp.status_code==200
    assert any(".txt" in i for i in jData["mediaURLs"])

def test_api_include_rtf():
    resp = client.get(testTextTweet.replace("https://twitter.com","https://api.vxtwitter.com")+"?include_rtf=true",headers={"User-Agent":"test"})
    jData = resp.get_json()
    assert resp.status_code==200
    assert any(".rtf" in i for i in jData["mediaURLs"])

def test_api_include_txt_nomedia():
    resp = client.get(testTextTweet.replace("https://twitter.com","https://api.vxtwitter.com")+"?include_txt=ifnomedia",headers={"User-Agent":"test"})
    jData = resp.get_json()
    assert resp.status_code==200
    assert any(".txt" in i for i in jData["mediaURLs"])

    resp = client.get(testMediaTweet.replace("https://twitter.com","https://api.vxtwitter.com")+"?include_txt=ifnomedia",headers={"User-Agent":"test"})
    jData = resp.get_json()
    assert resp.status_code==200
    assert not any(".txt" in i for i in jData["mediaURLs"])

def test_api_include_rtf_nomedia():
    resp = client.get(testTextTweet.replace("https://twitter.com","https://api.vxtwitter.com")+"?include_rtf=ifnomedia",headers={"User-Agent":"test"})
    jData = resp.get_json()
    assert resp.status_code==200
    assert any(".rtf" in i for i in jData["mediaURLs"])

    resp = client.get(testMediaTweet.replace("https://twitter.com","https://api.vxtwitter.com")+"?include_rtf=ifnomedia",headers={"User-Agent":"test"})
    jData = resp.get_json()
    assert resp.status_code==200
    assert not any(".rtf" in i for i in jData["mediaURLs"])

def test_api_mixedmedia():
    resp = client.get(testMixedMediaTweet.replace("https://twitter.com","https://api.vxtwitter.com")+"?include_txt=true",headers={"User-Agent":"test"})
    assert resp.status_code==200

def test_api_user():
    resp = client.get(testUser.replace("https://twitter.com","https://api.vxtwitter.com"),headers={"User-Agent":"test"})
    jData = resp.get_json()
    assert resp.status_code==200
    assert jData["screen_name"]=="jack"

def test_api_user_suspended():
    resp = client.get(testUserSuspended.replace("https://twitter.com","https://api.vxtwitter.com"),headers={"User-Agent":"test"})
    jData = resp.get_json()
    assert 'suspended' in jData["error"]

def test_api_user_private():
    resp = client.get(testUserPrivate.replace("https://twitter.com","https://api.vxtwitter.com")+"?with_tweets=true",headers={"User-Agent":"test"})
    jData = resp.get_json()
    assert jData['protected'] == True
    assert len(jData["latest_tweets"])==0

def test_api_user_invalid():
    resp = client.get(testUserInvalid.replace("https://twitter.com","https://api.vxtwitter.com")+"?with_tweets=true",headers={"User-Agent":"test"})
    jData = resp.get_json()
    assert resp.status_code==404

def test_api_user_feed():
    resp = client.get(testUser.replace("https://twitter.com","https://api.vxtwitter.com")+"?with_tweets=true",headers={"User-Agent":"test"})
    jData = resp.get_json()
    assert resp.status_code==200
    assert jData["screen_name"]=="jack"
    assert len(jData["latest_tweets"])>0

def test_api_retweet():
    resp = client.get(testRetweetTweet.replace("https://twitter.com","https://api.vxtwitter.com"),headers={"User-Agent":"test"})
    jData = resp.get_json()
    assert jData['retweetURL'] == 'https://twitter.com/i/status/1828569456231993456'
    assert jData['retweet'] != None
    assert jData['retweet']['text'].startswith("If you want to try")