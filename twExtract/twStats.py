# logging helper for debugging issues
# https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html
# https://github.com/awslabs/aws-embedded-metrics-python
# TODO: this needs to be updated if/when moved to different hosting 

import contextvars
import json
import os
import time

BACKEND = os.getenv("VXTWITTER_STATS", "none").lower()
NAMESPACE = os.getenv("VXTWITTER_STATS_NAMESPACE", "vxTwitter/twExtract")

# this could be an enum tbh
SOURCE_API = "api"
SOURCE_EMBED = "embed"
SOURCE_ACTIVITY = "activity"
SOURCE_UNKNOWN = "unknown"

_source = contextvars.ContextVar("twStatsSource", default=SOURCE_UNKNOWN)

def set_source(source):
    _source.set(source)

OK = "ok"
NOT_FOUND = "not_found"
UNAVAILABLE = "unavailable"
RATE_LIMITED = "ratelimited"
API_ERROR = "api_error"
BAD_RESPONSE = "bad_response"
PARSE_ERROR = "parse_error"
EXCEPTION = "exception"

def _printlog(directives, fields):
    if BACKEND != "emf": # TODO: this needs to be updated if/when moved to different hosting 
        return
    try:
        print(json.dumps(
            {"_aws": 
                {
                    "Timestamp":int(time.time() * 1000),
                    "CloudWatchMetrics": directives
                },**fields
            }, separators=(",", ":")))
    except Exception as e:
        print(f"twStats error: {e}")

def parse_rate_limit(value):
    try:
        return int(value)
    except:
        return None

def record(method, result, duration_ms, rate_limit_remaining=None):
    directives = [
        {
            "Namespace": NAMESPACE,
            "Dimensions": 
            [
                [],
                ["Method"],
                ["Result"]
            ],
            "Metrics": 
            [
                {
                    "Name": "Attempts",
                    "Unit": "Count"
                },
                {
                    "Name": "AttemptSuccess",
                    "Unit": "Count"
                }
            ]
        },
        {
            "Namespace": NAMESPACE,
            "Dimensions": 
            [
                ["Method"]
            ],
            "Metrics":
            [
                {
                    "Name": "AttemptDuration",
                    "Unit": "Milliseconds"
                }
            ]
        },
    ]
    fields = {
        "Method": method,
        "Result": result,
        "Source": _source.get(),
        "Attempts": 1,
        "AttemptSuccess": 1 if result == OK else 0,
        "AttemptDuration": round(duration_ms, 1),
    }
    if rate_limit_remaining is not None:
        directives.append(
            {
                "Namespace": NAMESPACE,
                "Dimensions": 
                [
                    ["Method"]
                ],
                "Metrics":
                [
                    {
                        "Name": "RateLimitRemaining",
                        "Unit": "Count"
                    }
                ]
            }
        )
        fields["RateLimitRemaining"] = rate_limit_remaining
    _printlog(directives, fields)

def record_status(retrieved_by, success, duration_ms, attempts):
    _printlog([
        {
            "Namespace": NAMESPACE,
            "Dimensions":
            [
                [],
                ["RetrievedBy"],
                ["Source"]
            ],
            "Metrics": 
            [
                {
                    "Name": "StatusRequests",
                    "Unit": "Count"
                },
                {
                    "Name": "StatusSuccess",
                    "Unit": "Count"
                }
            ]
        },
        {
            "Namespace": NAMESPACE,
            "Dimensions": [[]],
            "Metrics": 
            [
                {
                    "Name": "StatusDuration",
                    "Unit": "Milliseconds"
                }, 
                {
                    "Name": "StatusMethodsTried",
                    "Unit": "Count"
                }
            ]
        },
    ], {
        "RetrievedBy": retrieved_by or "none",
        "Source": _source.get(),
        "StatusRequests": 1,
        "StatusSuccess": 1 if success else 0,
        "StatusDuration": round(duration_ms, 1),
        "StatusMethodsTried": attempts,
    })
