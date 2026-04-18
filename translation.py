import deepl
from configHandler import config

validLanguages = ['AF', 'AN', 'AR', 'AS', 'AY', 'AZ', 'BA', 'BE', 'BG', 'BN', 'BR', 'BS', 'CA', 'CS', 'CY', 'DA', 'DE', 'DE-DE', 'EL', 'EN', 'EO', 'ES', 'ES-419', 'ET', 'EU', 'FA', 'FI', 'FR', 'FR-FR', 'GA', 'GL', 'GN', 'GU', 'HA', 'HE', 'HI', 'HR', 'HT', 'HU', 'HY', 'ID', 'IG', 'IS', 'IT', 'JA', 'JV', 'KA', 'KK', 'KO', 'KY', 'LA', 'LB', 'LN', 'LT', 'LV', 'MG', 'MI', 'MK', 'ML', 'MN', 'MR', 'MS', 'MT', 'MY', 'NB', 'NE', 'NL', 'OC', 'OM', 'PA', 'PL', 'PS', 'PT-BR', 'PT-PT', 'QU', 'RO', 'RU', 'SA', 'SK', 'SL', 'SQ', 'SR', 'ST', 'SU', 'SV', 'SW', 'TA', 'TE', 'TG', 'TH', 'TK', 'TL', 'TN', 'TR', 'TS', 'TT', 'UK', 'UR', 'UZ', 'VI', 'WO', 'XH', 'YI', 'ZH', 'ZH-HANS', 'ZH-HANT', 'ZU']
languageAliases = {
    #"EN":"EN-US",
    "JP":"JA",
}

mergedLangs=(validLanguages+list(languageAliases.keys()))

def getDeeplTranslation(text,target):
    target = target.upper()
    if target == "EN":
        target = "EN-US"
    try:
        if 'deeplKey' not in config["config"] or config["config"]["deeplKey"] == None:
            return None
        deepl_client = deepl.Translator(config["config"]["deeplKey"])
        result = deepl_client.translate_text(text, target_lang=target)
        return {
            "text":result.text,
            "source_language":result.detected_source_lang,
            "destination_language":target
        }
    except Exception as e:
        return None