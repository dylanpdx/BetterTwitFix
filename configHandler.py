import json
import os

if ('RUNNING_SERVERLESS' in os.environ and os.environ['RUNNING_SERVERLESS'] == '1'): # pragma: no cover
    config = {
            "config":{
                "link_cache":os.getenv("VXTWITTER_LINK_CACHE","none"),
                "database":os.getenv("VXTWITTER_DATABASE",""),
                "table":os.getenv("VXTWITTER_CACHE_TABLE",""),
                "color":os.getenv("VXTWITTER_COLOR",""), 
                "appname": os.getenv("VXTWITTER_APP_NAME","vxTwitter"), 
                "repo": os.getenv("VXTWITTER_REPO","https://github.com/dylanpdx/BetterTwitFix"), 
                "url": os.getenv("VXTWITTER_URL","https://vxtwitter.com"),
                "combination_method": os.getenv("VXTWITTER_COMBINATION_METHOD","local"), # can either be 'local' or a URL to a server handling requests in the same format
                "gifConvertAPI":os.getenv("VXTWITTER_GIF_CONVERT_API",""),
                "workaroundTokens":os.getenv("VXTWITTER_WORKAROUND_TOKENS",None),
                "deeplKey":os.getenv("DEEPL_API_KEY",None),
            }
        }
else:
    # Read config from config.json. If it does not exist, create new.
    if not os.path.exists("config.json"):
        with open("config.json", "w") as outfile:
            default_config = {
                "config":{
                    "link_cache":"json",
                    "database":"[url to mongo database goes here]",
                    "table":"TwiFix",
                    "color":"#43B581", 
                    "appname": "vxTwitter", 
                    "repo": "https://github.com/dylanpdx/BetterTwitFix", 
                    "url": "https://vxtwitter.com",
                    "combination_method": "local", # can either be 'local' or a URL to a server handling requests in the same format
                    "gifConvertAPI":"",
                    "workaroundTokens":None,
                    "deeplKey":None
                }
            }

            json.dump(default_config, outfile, indent=4, sort_keys=True)

        config = default_config
    else:
        f = open("config.json")
        config = json.load(f)
        f.close()
