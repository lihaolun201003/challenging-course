# -*- coding: utf-8 -*-
"""对生成的 PPT 做程序化 QA：越界、文本框溢出、明显重叠。"""
import os
import sys
from pptx import Presentation
from pptx.util import Emu

PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "01_报告", "04_中期答辩_初稿.pptx")

prs = Presentation(PATH)
SW, SH = prs.slide_width, prs.slide_height


def est_lines(text, w_emu, size_pt):
    """粗略估算换行数：CJK 按全宽、ASCII 按半宽。"""
    if not text:
        return 0
    size_emu = Emu(int(size_pt * 12700))
    usable = max(w_emu - Emu(int(0.06 * 914400)), size_emu)
    per_line = max(1, int(usable / size_emu))
    width = 0.0
    lines = 1
    for ch in text:
        width += 1.0 if ord(ch) > 0x2E80 else 0.55
        if width > per_line:
            lines += 1
            width = 0
    return lines


problems = []
for idx, slide in enumerate(prs.slides, start=1):
    boxes = []
    for shp in slide.shapes:
        l, t, w, h = shp.left, shp.top, shp.width, shp.height
        name = shp.shape_type
        # 越界（留 0.02" 容差）
        tol = Emu(int(0.02 * 914400))
        if l < -tol or t < -tol or l + w > SW + tol or t + h > SH + tol:
            problems.append(f"P{idx} 越界: {name} ({l/914400:.2f},{t/914400:.2f},"
                            f"{w/914400:.2f}x{h/914400:.2f})")
        if shp.has_text_frame and shp.text_frame.text.strip():
            max_size = 0
            for p in shp.text_frame.paragraphs:
                for r in p.runs:
                    if r.font.size and r.font.size.pt > max_size:
                        max_size = r.font.size.pt
            nlines = est_lines(shp.text_frame.text, w, max_size or 12)
            est_h = Emu(int(nlines * (max_size or 12) * 1.42 * 12700))
            if est_h > h + Emu(int(0.06 * 914400)):
                problems.append(
                    f"P{idx} 可能溢出: '{shp.text_frame.text[:22]}...' "
                    f"box_h={h/914400:.2f}\" est={est_h/914400:.2f}\" "
                    f"({nlines}行 @{max_size}pt w={w/914400:.2f}\")")
            boxes.append((shp.text_frame.text[:18], l, t, w, h))

    # 文本块互相重叠（忽略同属一个卡片的装饰）；只报明显交叠且互不包含的
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            ox = max(0, min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1]))
            oy = max(0, min(a[2] + a[4], b[2] + b[4]) - max(a[2], b[2]))
            if ox > Emu(int(0.25 * 914400)) and oy > Emu(int(0.12 * 914400)):
                area = ox * oy
                small = min(a[3] * a[4], b[3] * b[4])
                if area > small * 0.45:
                    problems.append(
                        f"P{idx} 重叠: '{a[0]}' × '{b[0]}' "
                        f"({ox/914400:.2f}x{oy/914400:.2f}\")")

print(f"slides = {len(prs.slides._sldIdLst)}")
if problems:
    print(f"\n{len(problems)} 条待查：")
    for p in problems:
        print(" -", p)
else:
    print("\n未发现越界 / 溢出 / 重叠问题")
