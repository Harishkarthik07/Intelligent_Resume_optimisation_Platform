from pathlib import Path

path = Path(__file__).resolve().parent.parent / 'frontend' / 'index.html'
text = path.read_text(encoding='utf-8')
text = text.replace("Syne", "DM Sans")
text = text.replace(
    "family=Syne:wght@400;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap",
    "family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300&display=swap"
)
path.write_text(text, encoding='utf-8')
print('frontend font updated')
