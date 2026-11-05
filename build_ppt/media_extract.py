"""Extract and downscale media used by the mid-term defense deck."""
import os
import zipfile
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "build_ppt", "media")
os.makedirs(OUT, exist_ok=True)

# 1. PCB iteration images straight out of the report pptx.
pcb_zip = os.path.join(ROOT, "01_报告", "03_PCB迭代记录.pptx")
with zipfile.ZipFile(pcb_zip) as z:
    for name in z.namelist():
        if name.startswith("ppt/media/"):
            target = os.path.join(OUT, "pcb_" + name.split("/")[-1])
            with open(target, "wb") as fh:
                fh.write(z.read(name))

# 2. Screenshots and photos: crop borders, cap width at 1600 px.
JOBS = {
    "05_素材/实物_屏幕实时读数.jpg": ("screen_real.jpg", None),
    "05_素材/ios_成功.jpg": ("ios_ok.jpg", None),
    "05_素材/APP_手机运行截图_2.jpg": ("android_app.jpg", None),
    "05_素材/APP_手机运行截图.jpg": ("android_old.jpg", None),
    "05_素材/PCB_布局截图.jpg": ("pcb_layout_early.jpg", None),
}

for src, (dst, _) in JOBS.items():
    path = os.path.join(ROOT, src)
    if not os.path.exists(path):
        print("missing:", path)
        continue
    im = Image.open(path).convert("RGB")
    if im.width > 1600:
        im = im.resize((1600, round(im.height * 1600 / im.width)), Image.LANCZOS)
    im.save(os.path.join(OUT, dst), quality=92)
    print(dst, im.size)

# 3. Boot animation preview (largest frame) and generated character.
for src, dst in [
    ("02_固件工程/AIR/assets/boot-preview.png", "boot_preview.png"),
    ("02_固件工程/AIR/assets/boot-character-original.png", "boot_char.png"),
]:
    path = os.path.join(ROOT, src)
    if os.path.exists(path):
        im = Image.open(path).convert("RGB")
        if im.width > 1600:
            im = im.resize((1600, round(im.height * 1600 / im.width)), Image.LANCZOS)
        im.save(os.path.join(OUT, dst))
        print(dst, im.size)

print("OUT =", OUT)
