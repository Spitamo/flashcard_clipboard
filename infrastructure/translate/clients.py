import requests


def google_translate(text: str, source: str, target: str, timeout: float) -> str:
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": source,
        "tl": target,
        "dt": "t",
        "q": text
    }
    r = requests.get(url, params=params, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    return "".join(part[0] for part in data[0])

def mymemory_translate(text: str, source: str, target: str, timeout: float) -> str:
    url = "https://api.mymemory.translated.net/get"
    params = {"q": text, "langpair": f"{source}|{target}"}
    r = requests.get(url, params=params, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    return data["responseData"]["translatedText"]

