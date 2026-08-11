import requests
payload = {
    'status': 200,
    'content': '<?xml version="1.0" encoding="UTF-8"?><Response><Say>Namaste. Main Rakshika hun, NDRF ki taraf se. Aapke jile mein ek aapatkaalin suchna hai. Kripaya surakshit sthan par jaayein. Kisi bhi aapatkal mein ek ek do par call karein. Dhanyavaad. Surakshit rahein.</Say></Response>',
    'content_type': 'application/xml',
    'charset': 'UTF-8'
}
resp = requests.post('https://run.mocky.io/api/mock', json=payload, verify=False)
print(resp.text)
