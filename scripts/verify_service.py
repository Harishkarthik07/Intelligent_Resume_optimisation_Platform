import requests
from pathlib import Path

out = []
for url in ('http://127.0.0.1:80/', 'http://127.0.0.1:8000/'):
    try:
        r = requests.get(url, timeout=5)
        out.append(f"URL: {url}\nSTATUS: {r.status_code}\nBODY:\n{r.text[:1000]}\n\n")
    except Exception as e:
        out.append(f"URL: {url}\nERROR: {e}\n\n")

Path('verify_out.txt').write_text('\n'.join(out))
print('Wrote verify_out.txt')
