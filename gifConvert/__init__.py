import base64
import os
import subprocess
import tempfile
import urllib.request
import re
import botocore
import boto3
import requests

useBucket=False
bucketname=os.getenv('CF_BUCKET')
s3=None
if bucketname is None:
    useBucket=False
else:
    useBucket=True
    s3 = boto3.client('s3',endpoint_url=os.getenv('CF_ENDPOINT'),aws_access_key_id=os.getenv('CF_KEY'),aws_secret_access_key=os.getenv('CF_KEY_SECRET'))


def extractStatus(url):
    return ""

def get_video_frame_rate(filename):
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            "-show_entries",
            "stream=r_frame_rate",
            filename,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    result_string = result.stdout.decode('utf-8').split()[0].split('/')
    fps = float(result_string[0])/float(result_string[1])
    return fps

def get_video_length_seconds(filename):
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            filename,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    result_string = result.stdout.decode('utf-8').split()[0]
    return float(result_string)

def loop_video_until_length(filename, length):
    # use stream_loop to loop video until it's at least length seconds long
    video_length = get_video_length_seconds(filename)
    if video_length < length:
        loops = int(length/video_length)
        new_filename = tempfile.mkstemp(suffix=".mp4")[1]
        subprocess.call(["ffmpeg","-stream_loop",str(loops),"-i",filename,"-c","copy","-y",new_filename],stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
        
        return new_filename
    else:
        return filename

def redir(url):
    return {
        "statusCode": 307,
        "headers": {
            "Location": url
        }
    }

def lambda_handler(event, context):
    if ("queryStringParameters" not in event):
        return {
            "statusCode": 400,
            "body": "Invalid request!"
        }
    
    url = event["queryStringParameters"].get("url","")
    try:
        if url == "":
            return {
                "statusCode": 400,
                "body": "Invalid request!!"
            }
        if not url.startswith("https://video.twimg.com/tweet_video/"):
            return redir(url)
    
        if useBucket:
            id=re.search(r"https:\/\/video\.twimg\.com\/tweet_video\/(.*?)\..*",url).group(1)
            bfilename = str(id)+".mp4"
            furl=f"https://gifs.vxtwitter.com/{bfilename}" #f"https://{bucketname}.s3.amazonaws.com/{bfilename}"
            print("get req for: "+url)
            try:
                s3.head_object(Bucket=bucketname, Key=bfilename)
                print("found existing already: "+bfilename)
                return redir(furl)
            except botocore.exceptions.ClientError:
                # Not found
                pass
        # download video
        print("downloading: "+url)
        videoLocation = tempfile.mkstemp(suffix=".mp4")[1]
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(videoLocation, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        else:
            print("error downloading video")
            return redir(url)
    
        videoLocationLooped = loop_video_until_length(videoLocation, 30)
        if videoLocationLooped != videoLocation:
            os.remove(videoLocation)
            videoLocation = videoLocationLooped
        else:
            os.remove(videoLocation)
            return redir(url)
        
        if not useBucket:
            with open(videoLocation, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('ascii')
                os.remove(videoLocation)
                return {
                    'statusCode': 200,
                    "headers": 
                    {
                        "Content-Type": "video/mp4"
                    },
                    'body': encoded_string,
                    'isBase64Encoded': True
                }
        else:
            with open(videoLocation, "rb") as image_file:
                s3.upload_fileobj(image_file, bucketname, bfilename)
            os.remove(videoLocation)
            print("converted: "+url+" -> "+furl)
            return redir(furl)
    except Exception as e:
        print("error converting gif: ")
        print(e)
        return redir(url)