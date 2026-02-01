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

def convert_video_to_gif(filename):
    try:
        new_filename = tempfile.mkstemp(suffix=".gif")[1]
        print("converting gif w gifski")
        p_ffmpeg = subprocess.Popen(["ffmpeg", "-i", filename, "-f", "yuv4mpegpipe", "-"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        p_gifski = subprocess.Popen(["gifski","--quality","70","--lossy-quality","30","-o", new_filename, "-"], stdin=p_ffmpeg.stdout, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

        p_ffmpeg.stdout.close()
        ret_gifski = p_gifski.wait()
        ret_ffmpeg = p_ffmpeg.wait()
        if ret_gifski != 0:
            print("err: gifski exited with code:", ret_gifski)
        if ret_ffmpeg != 0:
            print("err: ffmpeg exited with code:", ret_ffmpeg)
        if os.path.isfile(new_filename) and os.path.getsize(new_filename) > 0:
            return new_filename
        else:
            print("gifski failed to convert gif")
            return filename
    except Exception as e:
        print("error converting gif (convert_video_to_gif):")
        print(e)
        return filename
    
def convert_video_to_avif(filename):
    try:
        fd,new_filename = tempfile.mkstemp(suffix=".avif")
        os.close(fd)
        print("converting gif w ffmpeg to avif")
        subprocess.call(["ffmpeg","-nostdin","-y", "-i", filename,"-pix_fmt","yuv420p","-an","-c:v","libsvtav1","-crf","30","-b:v","0","-threads","4", new_filename], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        if os.path.isfile(new_filename) and os.path.getsize(new_filename) > 0:
            return new_filename
        else:
            print("ffmpeg failed to convert avif")
            return filename
    except Exception as e:
        print("error converting avif (convert_video_to_avif):")
        print(e)
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
            bfilename = str(id)+".avif"
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
    
        videoLocationLooped = convert_video_to_avif(videoLocation)
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
                        "Content-Type": "image/avif",
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