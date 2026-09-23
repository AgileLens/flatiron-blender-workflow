"""Side-by-side before/after sheet for matched review renders (PIL only)."""
import sys
from PIL import Image, ImageDraw, ImageFont
def sheet(left, right, out, title, labels=('BEFORE: build 3 (installed)', 'AFTER: build 4 candidate'), width=1400):
    a, b = Image.open(left).convert('RGB'), Image.open(right).convert('RGB')
    w = (width - 30) // 2; h = int(a.height * w / a.width)
    a, b = a.resize((w, h)), b.resize((w, int(b.height * w / b.width)))
    canvas = Image.new('RGB', (width, h + 70), (18, 24, 30)); d = ImageDraw.Draw(canvas)
    try:
        f = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 20)
    except OSError:
        f = ImageFont.load_default()
    d.text((12, 8), title, fill=(235, 235, 235), font=f)
    canvas.paste(a, (10, 60)); canvas.paste(b, (20 + w, 60))
    d.text((12, 36), labels[0], fill=(235, 190, 120), font=f); d.text((22 + w, 36), labels[1], fill=(120, 215, 200), font=f)
    canvas.save(out)
if __name__ == '__main__':
    sheet(*sys.argv[1:5])
