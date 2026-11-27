class TwExtractError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.msg = message

    def __str__(self):
        return self.msg

bearer="Bearer AAAAAAAAAAAAAAAAAAAAAPYXBAAAAAAACLXUNDekMxqa8h%2F40K4moUkGsoc%3DTYfbDKbT3jJPCEVnMYqilB28NHfOPqkca3qaAxGfsyKCs0wRbw"
v2bearer="Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
androidBearer="Bearer AAAAAAAAAAAAAAAAAAAAAFXzAwAAAAAAMHCxpeSDG1gLNLghVe8d74hl6k4%3DRUMF4xAQLsbeBhTSRrCiQpJtxoGWeyHrDb5te2jpGskWDFW82F"

gt_pattern = r'document\.cookie="gt=([^;]+);'

ANDROID_UA = "TwitterAndroid/11.61.0-release.0 (311610000-r-0) G011A/9 (google;G011A;google;G011A;0;;1;2016)"

AUTH_REQUIRED = "required" # login only
AUTH_OPTIONAL = "optional" # login and logout
AUTH_NONE = "none" # never use tokens

## parse
def _unwrap_visibility(result):
    if result.get('__typename') == 'TweetWithVisibilityResults':
        return result['tweet']
    return result


def parse_results_list(output, twid, results_key='tweet_results'):
    for entry in output['data'][results_key]:
        if 'result' not in entry:
            print("Tweet result not found in entry")
            continue
        result = _unwrap_visibility(entry['result'])
        if result.get('__typename') == 'TweetUnavailable':
            if 'reason' in result:
                return {'error':'Tweet unavailable: '+result['reason']}
            return {'error':'Tweet unavailable'}
        if result.get('rest_id') == twid:
            return result
    return None

def parse_timeline(output, twid, root, type_key='__typename', item_key='content', results_key='tweet_results'):
    instructions = output['data'][root]['instructions']
    entries = next((i['entries'] for i in instructions if i[type_key] == 'TimelineAddEntries'), [])
    for entry in entries:
        content = entry.get('content')
        if content is None:
            print("Tweet content not found in entry")
            continue
        if content.get('__typename') != 'TimelineTimelineItem':
            continue
        item = content.get(item_key, {})
        if item.get('__typename') != 'TimelineTweet':
            continue
        result = item[results_key]['result']
        if result.get('__typename') == 'Tweet' and result.get('rest_id') == twid:
            return result
    return None

def parse_single_result(output, twid, results_key='tweetResult'):
    result = _unwrap_visibility(output['data'][results_key]['result'])
    if result.get('__typename') == 'TweetUnavailable':
        if 'reason' in result:
            raise TwExtractError(400, "Extract error: "+result['reason'])
        raise TwExtractError(400, "Extract error: Tweet unavailable")
    if result.get('rest_id') != twid:
        return None
    if 'card' in result and 'legacy' in result['card']:
        result['card'] = result['card']['legacy']
    return result

# variables: variables sent in request, AND id_key set to result of id_value(twid)
# auth: type of auth to use, see above
# https://github.com/fa0311/TwitterInternalAPIDocument

TWEET_RESULTS_BY_IDS = {
    "name": "TweetResultsByIds",
    "query_id": "2OOZWmw8nAtUHVnXXQhgaA",
    "operation": "TweetResultsByIdsQuery",
    "bearer": v2bearer,
    "user_agent": ANDROID_UA,
    "features": '{"longform_notetweets_inline_media_enabled":true,"super_follow_badge_privacy_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"super_follow_user_api_enabled":true,"super_follow_tweet_api_enabled":true,"android_graphql_skip_api_media_color_palette":true,"creator_subscriptions_tweet_preview_api_enabled":true,"freedom_of_speech_not_reach_fetch_enabled":true,"creator_subscriptions_subscription_count_enabled":true,"tweetypie_unmention_optimization_enabled":true,"longform_notetweets_consumption_enabled":true,"subscriptions_verification_info_enabled":true,"blue_business_profile_image_shape_enabled":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"super_follow_exclusive_tweet_notifications_enabled":true}',
    "auth": AUTH_REQUIRED,
    "guest_token": False,
    "id_key": "rest_ids",
    "id_value": lambda twid: [twid],
    "variables": {"includeTweetImpression":True,"includeHasBirdwatchNotes":False,"includeEditPerspective":False,"rest_ids":[],"includeEditControl":True,"includeCommunityTweetRelationship":True,"includeTweetVisibilityNudge":True},
    "parser": parse_results_list,
    "parser_args": {},
}

CONVERSATION_TIMELINE_V2 = { # Android
    "name": "ConversationTimelineV2",
    "query_id": "Wrspae-uyGj-nWPyUqdUag",
    "operation": "ConversationTimelineV2",
    "bearer": androidBearer,
    "user_agent": ANDROID_UA,
    "features": '{"grok_translations_community_note_translation_is_enabled":false,"super_follow_badge_privacy_enabled":true,"unified_cards_destination_url_params_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"super_follow_user_api_enabled":true,"profile_label_improvements_pcf_label_in_profile_enabled":true,"premium_content_api_read_enabled":false,"grok_translations_community_note_auto_translation_is_enabled":false,"android_graphql_skip_api_media_color_palette":true,"tweetypie_unmention_optimization_enabled":true,"longform_notetweets_consumption_enabled":true,"subscriptions_verification_info_enabled":true,"blue_business_profile_image_shape_enabled":true,"super_follow_exclusive_tweet_notifications_enabled":true,"longform_notetweets_inline_media_enabled":true,"grok_android_analyze_trend_fetch_enabled":false,"unified_cards_ad_metadata_container_dynamic_card_content_query_enabled":true,"super_follow_tweet_api_enabled":true,"articles_api_enabled":true,"android_ad_formats_media_component_render_overlay_enabled":true,"creator_subscriptions_tweet_preview_api_enabled":true,"freedom_of_speech_not_reach_fetch_enabled":true,"grok_translations_timeline_user_bio_auto_translation_is_enabled":false,"grok_translations_post_auto_translation_is_enabled":false,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"immersive_video_status_linkable_timestamps":true,"profile_label_improvements_pcf_label_in_post_enabled":true}',
    "auth": AUTH_REQUIRED,
    "guest_token": False,
    "id_key": "focalTweetId",
    "id_value": int,
    "variables": {"referrer":"home","includeTweetImpression":True,"includeHasBirdwatchNotes":False,"isReaderMode":False,"includeEditPerspective":False,"includeEditControl":True,"focalTweetId":0,"includeCommunityTweetRelationship":True,"includeTweetVisibilityNudge":True},
    "parser": parse_timeline,
    "parser_args": {"root": "timeline_response", "results_key": "tweetResult"},
}

CONVERSATION_TIMELINE = { # iOS
    "name": "ConversationTimeline",
    "query_id": "b-bCN9RelT8k0fCr_s2BFg",
    "operation": "ConversationTimeline",
    "bearer": androidBearer,
    "user_agent": ANDROID_UA,
    "features": '{"grok_translations_community_note_translation_is_enabled":false,"super_follow_badge_privacy_enabled":true,"unified_cards_destination_url_params_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"super_follow_user_api_enabled":true,"profile_label_improvements_pcf_label_in_profile_enabled":true,"premium_content_api_read_enabled":false,"grok_translations_community_note_auto_translation_is_enabled":false,"android_graphql_skip_api_media_color_palette":true,"tweetypie_unmention_optimization_enabled":true,"longform_notetweets_consumption_enabled":true,"subscriptions_verification_info_enabled":true,"blue_business_profile_image_shape_enabled":true,"super_follow_exclusive_tweet_notifications_enabled":true,"longform_notetweets_inline_media_enabled":true,"grok_android_analyze_trend_fetch_enabled":false,"unified_cards_ad_metadata_container_dynamic_card_content_query_enabled":true,"super_follow_tweet_api_enabled":true,"articles_api_enabled":true,"android_ad_formats_media_component_render_overlay_enabled":true,"creator_subscriptions_tweet_preview_api_enabled":true,"freedom_of_speech_not_reach_fetch_enabled":true,"grok_translations_timeline_user_bio_auto_translation_is_enabled":false,"grok_translations_post_auto_translation_is_enabled":false,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"immersive_video_status_linkable_timestamps":true,"profile_label_improvements_pcf_label_in_post_enabled":true}',
    "auth": AUTH_REQUIRED,
    "guest_token": False,
    "id_key": "focal_tweet_id",
    "id_value": int,
    "variables": {"referrer":"home","includeTweetImpression":True,"includeHasBirdwatchNotes":False,"isReaderMode":False,"includeEditPerspective":False,"includeEditControl":True,"focal_tweet_id":0,"includeCommunityTweetRelationship":True,"includeTweetVisibilityNudge":True,"ranking_mode":"Relevance"},
    "parser": parse_timeline,
    "parser_args": {"root": "threaded_conversation_with_injections_v2"},
}

TWEET_DETAIL = { 
    "name": "TweetDetail",
    "query_id": "dQDdKtt882nl-Km98FJGSQ",
    "operation": "TweetDetail",
    "bearer": v2bearer,
    "user_agent": None,
    "features": '{"rweb_video_screen_enabled":false,"rweb_cashtags_enabled":true,"profile_label_improvements_pcf_label_in_post_enabled":true,"responsive_web_profile_redirect_enabled":true,"rweb_tipjar_consumption_enabled":false,"verified_phone_label_enabled":false,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_timeline_navigation_enabled":true,"premium_content_api_read_enabled":false,"communities_web_enable_tweet_community_results_fetch":true,"c9s_tweet_anatomy_moderator_badge_enabled":true,"responsive_web_grok_analyze_button_fetch_trends_enabled":false,"responsive_web_grok_analyze_post_followups_enabled":true,"rweb_cashtags_composer_attachment_enabled":true,"responsive_web_jetfuel_frame":true,"rweb_sports_post_context_enabled":true,"x_elections_post_context_enabled":true,"responsive_web_grok_share_attachment_enabled":true,"responsive_web_grok_annotations_enabled":true,"articles_preview_enabled":true,"responsive_web_edit_tweet_api_enabled":true,"rweb_conversational_replies_downvote_enabled":false,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":true,"content_disclosure_indicator_enabled":true,"content_disclosure_ai_generated_indicator_enabled":true,"responsive_web_grok_show_grok_translated_post":true,"responsive_web_grok_analysis_button_from_backend":true,"post_ctas_fetch_enabled":true,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"responsive_web_nested_quote_preview_enabled":true,"responsive_web_grok_image_annotation_enabled":true,"responsive_web_grok_imagine_annotation_enabled":true,"responsive_web_grok_community_note_auto_translation_is_enabled":true,"responsive_web_enhance_cards_enabled":false}',
    "auth": AUTH_REQUIRED,
    "guest_token": False,
    "id_key": "focalTweetId",
    "id_value": str,
    "variables": {"focalTweetId":"0","with_rux_injections":False,"includePromotedContent":True,"withCommunity":True,"withQuickPromoteEligibilityTweetFields":True,"withBirdwatchNotes":True,"withVoice":True,"withV2Timeline":True},
    "parser": parse_timeline,
    "parser_args": {"root": "threaded_conversation_with_injections_v2", "type_key": "type", "item_key": "itemContent"},
}

TWEET_RESULT_BY_REST_ID = {
    "name": "TweetResultByRestId",
    "query_id": "U8lc5aomF5krJzZ9vJ9wxg",
    "operation": "TweetResultByRestId",
    "bearer": v2bearer,
    "user_agent": None,
    "features": '{"creator_subscriptions_tweet_preview_api_enabled":true,"premium_content_api_read_enabled":false,"communities_web_enable_tweet_community_results_fetch":true,"c9s_tweet_anatomy_moderator_badge_enabled":true,"responsive_web_grok_analyze_button_fetch_trends_enabled":false,"responsive_web_grok_analyze_post_followups_enabled":true,"responsive_web_jetfuel_frame":true,"responsive_web_grok_share_attachment_enabled":true,"responsive_web_grok_annotations_enabled":false,"articles_preview_enabled":true,"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":true,"tweet_awards_web_tipping_enabled":false,"responsive_web_grok_show_grok_translated_post":true,"responsive_web_grok_analysis_button_from_backend":true,"post_ctas_fetch_enabled":true,"creator_subscriptions_quote_tweet_preview_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"profile_label_improvements_pcf_label_in_post_enabled":true,"responsive_web_profile_redirect_enabled":false,"rweb_tipjar_consumption_enabled":false,"verified_phone_label_enabled":false,"responsive_web_grok_image_annotation_enabled":true,"responsive_web_grok_imagine_annotation_enabled":true,"responsive_web_grok_community_note_auto_translation_is_enabled":false,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"responsive_web_graphql_timeline_navigation_enabled":true,"responsive_web_enhance_cards_enabled":false}',
    "auth": AUTH_OPTIONAL,
    "guest_token": True,
    "id_key": "tweetId",
    "id_value": str,
    "variables": {"tweetId":"0","includePromotedContent":True,"withBirdwatchNotes":True,"withVoice":True,"withCommunity":True},
    "parser": parse_single_result,
    "parser_args": {},
}

TWEET_RESULT_BY_REST_ID_ANON = {**TWEET_RESULT_BY_REST_ID, "name": "TweetResultByRestId_Anon", "auth": AUTH_NONE}

TWEET_RESULT_BY_ID = { # Android
    "name": "TweetResultById",
    "query_id": "XcmCoTco-zSOvAZESj78OQ",
    "operation": "TweetResultByIdQuery",
    "bearer": androidBearer,
    "user_agent": ANDROID_UA,
    "features": CONVERSATION_TIMELINE_V2["features"],
    "auth": AUTH_REQUIRED,
    "guest_token": False,
    "id_key": "rest_id",
    "id_value": str,
    "variables": {"includeTweetImpression":True,"includeHasBirdwatchNotes":True,"includeEditPerspective":False,"includeEditControl":True,"includeCommunityTweetRelationship":True,"includeTweetVisibilityNudge":True},
    "parser": parse_single_result,
    "parser_args": {"results_key": "tweet_result"},
}

TWEET_RESULTS_BY_REST_IDS = { # web
    "name": "TweetResultsByRestIds",
    "query_id": "yW_CmYWEKwaOpAEHpNSReg",
    "operation": "TweetResultsByRestIds",
    "bearer": v2bearer,
    "user_agent": None,
    "features": '{"creator_subscriptions_tweet_preview_api_enabled":true,"premium_content_api_read_enabled":false,"communities_web_enable_tweet_community_results_fetch":true,"c9s_tweet_anatomy_moderator_badge_enabled":true,"responsive_web_grok_analyze_button_fetch_trends_enabled":false,"responsive_web_grok_analyze_post_followups_enabled":true,"rweb_cashtags_composer_attachment_enabled":true,"responsive_web_jetfuel_frame":true,"rweb_sports_post_context_enabled":true,"x_elections_post_context_enabled":true,"responsive_web_grok_share_attachment_enabled":true,"responsive_web_grok_annotations_enabled":true,"articles_preview_enabled":true,"responsive_web_edit_tweet_api_enabled":true,"rweb_conversational_replies_downvote_enabled":false,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":true,"content_disclosure_indicator_enabled":true,"content_disclosure_ai_generated_indicator_enabled":true,"responsive_web_grok_show_grok_translated_post":true,"responsive_web_grok_analysis_button_from_backend":true,"post_ctas_fetch_enabled":true,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"rweb_cashtags_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"profile_label_improvements_pcf_label_in_post_enabled":true,"responsive_web_profile_redirect_enabled":true,"rweb_tipjar_consumption_enabled":false,"verified_phone_label_enabled":false,"responsive_web_nested_quote_preview_enabled":true,"responsive_web_grok_image_annotation_enabled":true,"responsive_web_grok_imagine_annotation_enabled":true,"responsive_web_grok_community_note_auto_translation_is_enabled":true,"responsive_web_graphql_timeline_navigation_enabled":true}',
    "field_toggles": '{"withArticleRichContentState":true}',
    "auth": AUTH_REQUIRED,
    "guest_token": False,
    "id_key": "tweetIds",
    "id_value": lambda twid: [twid],
    "variables": {"withCommunity":False,"includePromotedContent":False,"withVoice":False},
    "parser": parse_results_list,
    "parser_args": {"results_key": "tweetResult"},
}

# TODO: add Android GetPostById -SlaVDFjLsmkKK2W0NJ8Xg
# has a different format (missing legacy)

# method priority/order
GET_METHODS = [
    TWEET_RESULT_BY_REST_ID_ANON,
    TWEET_RESULTS_BY_REST_IDS,
    CONVERSATION_TIMELINE_V2,
    TWEET_RESULT_BY_ID,
    TWEET_RESULTS_BY_IDS,
    TWEET_DETAIL,
    TWEET_RESULT_BY_REST_ID,
]
# endpoints that return translations first
GET_METHODS_TL = [
    TWEET_RESULT_BY_REST_ID,
    TWEET_DETAIL,
    CONVERSATION_TIMELINE_V2,
    TWEET_RESULTS_BY_IDS,
    TWEET_RESULT_BY_REST_ID_ANON
]

## users

def parse_user(output, results_key):
    entry = output['data'].get(results_key)
    if isinstance(entry, list):
        entry = entry[0] if entry else None
    if not entry or 'result' not in entry:
        return None
    return entry['result']

# generic setup
_WEB_USER = {
    "bearer": v2bearer,
    "user_agent": None,
    "features": '{"hidden_profile_subscriptions_enabled":true,"profile_label_improvements_pcf_label_in_post_enabled":true,"responsive_web_profile_redirect_enabled":true,"rweb_tipjar_consumption_enabled":false,"verified_phone_label_enabled":false,"subscriptions_verification_info_is_identity_verified_enabled":true,"subscriptions_verification_info_verified_since_enabled":true,"highlights_tweets_tab_ui_enabled":true,"responsive_web_twitter_article_notes_tab_enabled":true,"subscriptions_feature_can_gift_premium":false,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_timeline_navigation_enabled":true}',
    "field_toggles": '{"withAuxiliaryUserLabels":true}',
    "auth": AUTH_REQUIRED,
    "guest_token": False,
    "parser": parse_user,
    "parser_args": {"results_key": "user"},
}

# generic setup
_ANDROID_USER = {
    "bearer": androidBearer,
    "user_agent": ANDROID_UA,
    "features": CONVERSATION_TIMELINE_V2["features"],
    "auth": AUTH_REQUIRED,
    "guest_token": False,
    "parser": parse_user,
    "parser_args": {"results_key": "user_result"},
}

USER_BY_SCREEN_NAME = {**_WEB_USER,
    "name": "UserByScreenName",
    "query_id": "AMIBMjtxEEATh4z8V9GtRg",
    "operation": "UserByScreenName",
    "id_key": "screen_name",
    "id_value": str,
    "variables": {"withGrokTranslatedBio": False},
}

USER_BY_REST_ID = {**_WEB_USER,
    "name": "UserByRestId",
    "query_id": "mxaYWwt52eAb6OAzYHMVzg",
    "operation": "UserByRestId",
    "id_key": "userId",
    "id_value": str,
    "variables": {"withGrokTranslatedBio": False},
}

GET_USER_BY_SCREEN_NAME = {**_ANDROID_USER,
    "name": "GetUserByScreenNameQuery",
    "query_id": "XXUxzuVHY8sa9TCK3HPesA",
    "operation": "GetUserByScreenNameQuery",
    "id_key": "screen_name",
    "id_value": str,
    "variables": {"include_profile_info": True},
}

GET_USER = {**_ANDROID_USER,
    "name": "GetUserQuery",
    "query_id": "s1aijOB4pUNwwrlIXJ0pRw",
    "operation": "GetUserQuery",
    "id_key": "rest_id",
    "id_value": str,
    "variables": {"include_profile_info": True},
}

GET_USERS_BY_IDS = {**_ANDROID_USER,
    "name": "GetUsersByIds",
    "query_id": "mSUbmt8epGuvcqtqjAidFQ",
    "operation": "GetUsersByIds",
    "id_key": "ids",
    "id_value": lambda uid: [uid],
    "variables": {"include_profile_info": True},
    "parser_args": {"results_key": "user_results_by_rest_ids"},
}

USERS_BY_SCREEN_NAMES = {**USER_BY_SCREEN_NAME, # web
    "name": "UsersByScreenNames",
    "query_id": "cACg_kWQkzNQ74lcK5rksQ",
    "operation": "UsersByScreenNames",
    "id_key": "screen_names",
    "id_value": lambda name: [name],
    "variables": {},
    "parser_args": {"results_key": "users"},
}

GET_USER_METHODS_SCREEN_NAME = [
    USER_BY_SCREEN_NAME,
    USERS_BY_SCREEN_NAMES,
    GET_USER_BY_SCREEN_NAME,
]
GET_USER_METHODS_ID = [
    GET_USERS_BY_IDS,
    USER_BY_REST_ID,
    GET_USER,
]

## feed (with_tweets)

def _feed_item_tweet(item):
    content = item.get('itemContent') or item.get('content') or {}
    result = content.get('tweet_results', {}).get('result')
    return _unwrap_visibility(result) if result else None

def parse_feed(output, userId, path):
    node = output['data']
    for key in path:
        node = node[key]
    userId = str(userId)
    tweets = {}
    for instruction in node['instructions']:
        if (instruction.get('type') or instruction.get('__typename')) != 'TimelineAddEntries':
            continue
        for entry in instruction['entries']:
            entryId = entry.get('entryId') or entry.get('entry_id') or ''
            content = entry.get('content', {})
            if entryId.startswith('tweet-'):
                found = [_feed_item_tweet(content)]
            elif 'conversation' in entryId:
                found = [_feed_item_tweet(i.get('item', {})) for i in content.get('items', [])]
                found = [t for t in found if t and t.get('legacy', {}).get('user_id_str') == userId]
            else:
                continue
            for tweet in found:
                if tweet and tweet.get('rest_id'):
                    tweets.setdefault(tweet['rest_id'], tweet)
    return sorted(tweets.values(), key=lambda t: int(t['rest_id']), reverse=True)

_WEB_FEED = {
    "bearer": v2bearer,
    "user_agent": None,
    "features": '{"rweb_video_screen_enabled":false,"rweb_cashtags_enabled":true,"profile_label_improvements_pcf_label_in_post_enabled":true,"responsive_web_profile_redirect_enabled":true,"rweb_tipjar_consumption_enabled":false,"verified_phone_label_enabled":false,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_timeline_navigation_enabled":true,"premium_content_api_read_enabled":false,"communities_web_enable_tweet_community_results_fetch":true,"c9s_tweet_anatomy_moderator_badge_enabled":true,"responsive_web_grok_analyze_button_fetch_trends_enabled":false,"responsive_web_grok_analyze_post_followups_enabled":true,"rweb_cashtags_composer_attachment_enabled":true,"responsive_web_jetfuel_frame":true,"rweb_sports_post_context_enabled":true,"x_elections_post_context_enabled":true,"responsive_web_grok_share_attachment_enabled":true,"responsive_web_grok_annotations_enabled":true,"articles_preview_enabled":true,"responsive_web_edit_tweet_api_enabled":true,"rweb_conversational_replies_downvote_enabled":false,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":true,"content_disclosure_indicator_enabled":true,"content_disclosure_ai_generated_indicator_enabled":true,"responsive_web_grok_show_grok_translated_post":true,"responsive_web_grok_analysis_button_from_backend":true,"post_ctas_fetch_enabled":true,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"responsive_web_nested_quote_preview_enabled":true,"responsive_web_grok_image_annotation_enabled":true,"responsive_web_grok_imagine_annotation_enabled":true,"responsive_web_grok_community_note_auto_translation_is_enabled":true,"responsive_web_enhance_cards_enabled":false}',
    "field_toggles": '{"withArticlePlainText":false}',
    "auth": AUTH_REQUIRED,
    "guest_token": False,
    "transaction_id": True, # required! x-client-transaction-id
    "id_key": "userId",
    "id_value": str,
    "parser": parse_feed,
    "parser_args": {"path": ["user", "result", "timeline", "timeline"]},
}

USER_TWEETS_AND_REPLIES = {**_WEB_FEED,
    "name": "UserTweetsAndReplies",
    "query_id": "FmuxExUC21Xn_C2NwtX5sQ",
    "operation": "UserTweetsAndReplies",
    "variables": {"count": 20, "includePromotedContent": False, "withCommunity": True, "withVoice": True},
}

USER_ORIGINALS_TIMELINE = {**_WEB_FEED, # original tweets only
    "name": "UserOriginalsTimeline",
    "query_id": "ZFKu1DFS63hgrkLzR3Hsdw",
    "operation": "UserOriginalsTimeline",
    "variables": {"count": 20, "includePromotedContent": False, "withVoice": True},
}

# TODO: add Android UserWithProfileTweetsQueryV2 AOyD3Un2H-wFjl9usVRThg
# has a different format (missing legacy)

GET_FEED_METHODS = [
    USER_TWEETS_AND_REPLIES,
    USER_ORIGINALS_TIMELINE,
]
