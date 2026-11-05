# -*- coding: utf-8 -*-
"""中期答辩 PPT 初稿生成脚本（16:9，中文，微软雅黑）。"""
import os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "media")
OUT = os.path.join(ROOT, "01_报告", "04_中期答辩_初稿.pptx")

# ---------- 调色板（源自实物屏幕配色：深藏青底 + 青色强调） ----------
INK = RGBColor(0x0E, 0x1F, 0x33)      # 深藏青（主色）
INK_SOFT = RGBColor(0x16, 0x2E, 0x4A)  # 深藏青的浅一档（卡片）
TEAL = RGBColor(0x2B, 0xB8, 0xC4)      # 青色（强调，取自屏幕 PM2.5 读数色）
TEAL_DEEP = RGBColor(0x1F, 0x8E, 0x99)  # 青色深档（线条）
BG = RGBColor(0xF4, 0xF7, 0xFA)        # 内容页底色
CARD = RGBColor(0xFF, 0xFF, 0xFF)
TEXT = RGBColor(0x21, 0x2B, 0x36)
MUTED = RGBColor(0x5A, 0x6B, 0x7B)
LINE = RGBColor(0xD3, 0xDC, 0xE4)
AMBER = RGBColor(0xE8, 0xA3, 0x3D)
GREEN = RGBColor(0x3D, 0xAE, 0x77)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT = "微软雅黑"

EMU = 914400
prs = Presentation()
prs.slide_width = Inches(13.33)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]

PAGES = []  # (shape, footer_text)


def slide_new(dark=False):
    s = prs.slides.add_slide(BLANK)
    bg = s.background.fill
    bg.solid()
    bg.fore_color.rgb = INK if dark else BG
    return s


def rect(s, x, y, w, h, fill=None, line=None, lw=0.75, rounded=False, radius=0.06, shadow=False):
    shp = s.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE,
        Inches(x), Inches(y), Inches(w), Inches(h))
    if rounded:
        try:
            shp.adjustments[0] = radius
        except Exception:
            pass
    if fill is None:
        shp.fill.background()
    else:
        shp.fill.solid()
        shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(lw)
    if not shadow:
        shp.shadow.inherit = False
    shp.text_frame.paragraphs[0].text = ""
    return shp


def card(s, x, y, w, h, fill=CARD, line=None, radius=0.07):
    return rect(s, x, y, w, h, fill=fill, line=line, rounded=True, radius=radius)


def text(s, x, y, w, h, runs, size=15, color=TEXT, bold=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, spacing=4, lh=1.0, font=FONT, wrap=True):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = wrap
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    if isinstance(runs, str):
        runs = [runs]
    first = True
    for item in runs:
        if isinstance(item, str):
            item = {"t": item}
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = item.get("align", align)
        p.space_after = Pt(item.get("spacing", spacing))
        lhv = item.get("lh", lh)
        if lhv != 1.0:
            p.line_spacing = lhv
        segs = item["t"] if isinstance(item["t"], list) else [item["t"]]
        for seg in segs:
            if isinstance(seg, str):
                seg = {"t": seg}
            r = p.add_run()
            r.text = seg["t"]
            r.font.name = item.get("font", font)
            r.font.size = Pt(seg.get("size", item.get("size", size)))
            r.font.bold = seg.get("bold", item.get("bold", bold))
            r.font.color.rgb = seg.get("color", item.get("color", color))
    return tb


def head(s, kicker, title, page):
    text(s, 0.5, 0.34, 8.0, 0.28, kicker, size=12, color=TEAL_DEEP, bold=True, spacing=0)
    text(s, 0.5, 0.62, 11.3, 0.55, title, size=26, color=TEXT, bold=True, spacing=0)
    text(s, 12.23, 6.98, 0.6, 0.3, f"{page:02d}", size=11, color=MUTED,
         align=PP_ALIGN.RIGHT, spacing=0)


def footer(s, txt):
    text(s, 0.5, 6.98, 9.5, 0.3, txt, size=11, color=MUTED, spacing=0)


def chip(s, x, y, w, h, label, fill, fg=WHITE, size=12, bold=True):
    c = rect(s, x, y, w, h, fill=fill, rounded=True, radius=0.5)
    tf = c.text_frame
    tf.word_wrap = False
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = label
    r.font.name = FONT
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.color.rgb = fg
    return c


def chip_auto(s, x, y, label, fill, fg=WHITE, size=12, pad=0.14, h=0.3):
    w = pad * 2 + 0.0115 * size * len(label) + 0.06 * size / 12
    return chip(s, x, y, w, h, label, fill, fg=fg, size=size), w


def pill_outline(s, x, y, w, h, label, line=TEAL_DEEP, fg=TEAL_DEEP, size=12):
    c = rect(s, x, y, w, h, fill=None, line=line, lw=1.0, rounded=True, radius=0.5)
    tf = c.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = label
    r.font.name = FONT
    r.font.size = Pt(size)
    r.font.bold = True
    r.font.color.rgb = fg
    return c


def bar(s, x, y, w, h, frac, label, color=TEAL):
    rect(s, x, y, w, h, fill=LINE, rounded=True, radius=0.5)
    rect(s, x, y, max(w * frac, 0.14), h, fill=color, rounded=True, radius=0.5)
    return text(s, x + w + 0.12, y - 0.045, 3.2, h + 0.1, label, size=12, color=MUTED,
                anchor=MSO_ANCHOR.MIDDLE, spacing=0)


def flow_box(s, x, y, w, h, color, title, sub=None, tsize=13, ssize=10.5, dark_text=False):
    b = card(s, x, y, w, h)
    tf = b.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.06)
    tf.margin_top = tf.margin_bottom = Inches(0.03)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.space_after = Pt(1)
    r = p.add_run()
    r.text = title
    r.font.name = FONT
    r.font.size = Pt(tsize)
    r.font.bold = True
    r.font.color.rgb = color
    if sub:
        p2 = tf.add_paragraph()
        p2.alignment = PP_ALIGN.CENTER
        r2 = p2.add_run()
        r2.text = sub
        r2.font.name = FONT
        r2.font.size = Pt(ssize)
        r2.font.color.rgb = MUTED
    return b


def arrow_r(s, x, y, w=0.3, color=TEAL_DEEP):
    a = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(y - 0.09),
                           Inches(w), Inches(0.18))
    a.fill.solid()
    a.fill.fore_color.rgb = color
    a.line.fill.background()
    a.shadow.inherit = False
    return a


def arrow_d(s, x, y, h=0.28, color=TEAL_DEEP):
    a = s.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, Inches(x - 0.09), Inches(y),
                           Inches(0.18), Inches(h))
    a.fill.solid()
    a.fill.fore_color.rgb = color
    a.line.fill.background()
    a.shadow.inherit = False
    return a


def pic(s, path, x, y, w, h):
    pic = s.shapes.add_picture(path, Inches(x), Inches(y), Inches(w), Inches(h))
    pic.shadow.inherit = False
    return pic


def table_grid(s, x, y, w, col_w, rows, header, body_size=12.5, head_size=12.5,
               row_h=0.42, head_h=0.44, aligns=None, fills=None):
    n = len(rows)
    for j, htxt in enumerate(header):
        hx = x + sum(col_w[:j])
        rect(s, hx, y, col_w[j], head_h, fill=INK)
        text(s, hx + 0.1, y, col_w[j] - 0.2, head_h, htxt, size=head_size, color=WHITE,
             bold=True, align=(aligns[j] if aligns else PP_ALIGN.LEFT),
             anchor=MSO_ANCHOR.MIDDLE, spacing=0)
    for i, row in enumerate(rows):
        ry = y + head_h + i * row_h
        if fills and fills[i] is not None:
            rect(s, x, ry, w, row_h, fill=fills[i])
        for j, cell in enumerate(row):
            cx = x + sum(col_w[:j])
            if j > 0:
                rect(s, cx, ry, 0.01, row_h, fill=LINE)  # 竖细线
            if isinstance(cell, tuple) and len(cell) == 3 and isinstance(cell[2], bool):
                txt, col, bold = cell
            else:
                txt, col, bold = cell, TEXT, False
            text(s, cx + 0.1, ry, col_w[j] - 0.2, row_h, txt, size=body_size, color=col,
                 bold=bold, align=(aligns[j] if aligns else PP_ALIGN.LEFT),
                 anchor=MSO_ANCHOR.MIDDLE, spacing=0)
        if i < n - 1:
            rect(s, x, ry + row_h - 0.008, w, 0.008, fill=LINE)
    rect(s, x, y + head_h + (n - 1) * row_h + row_h - 0.008, w, 0.008, fill=LINE)


# =====================================================================
# P1 封面（深底）
# =====================================================================
s = slide_new(dark=True)
# 右侧图片区
PW, PH = 4.55, 6.5
pic(s, os.path.join(MEDIA, "screen_real.jpg"), 8.18, 0.5, PW, PH)
# 封面用裸图 + 左侧文字，避免文字压图
text(s, 0.75, 1.28, 7.1, 0.4, "挑战性课程 · 中期答辩", size=15, color=TEAL, bold=True, spacing=0)
text(s, 0.75, 1.9, 7.4, 2.9, [
    {"t": "基于 STM32F411RE 与 2.8 英寸 TFT LCD", "size": 20, "lh": 1.3, "spacing": 4,
     "color": RGBColor(0x9F, 0xB6, 0xC4)},
    {"t": "多参数空气质量监测系统", "size": 36, "bold": True, "lh": 1.2, "spacing": 8},
    {"t": "方案实施设计 · 进展与问题 · 下一步计划", "size": 15, "color": MUTED, "lh": 1.2},
], color=WHITE)
card(s, 0.75, 4.9, 3.0, 1.32, fill=INK_SOFT)
text(s, 0.95, 5.06, 2.6, 1.0, [
    {"t": "李昊伦 / 杨皓 / 赵旭东", "size": 13.5, "color": WHITE, "spacing": 3},
    {"t": "指导教师：待填", "size": 11.5, "color": MUTED, "spacing": 3},
    {"t": "2026 年 10 月", "size": 11.5, "color": MUTED},
])
text(s, 0.75, 6.72, 7.0, 0.3, "AIR MONITOR  ·  PMS5003ST  ·  ILI9341  ·  USART6 蓝牙",
     size=11.5, color=TEAL, bold=True, spacing=0)

# =====================================================================
# P2 进展总览
# =====================================================================
s = slide_new()
head(s, "PROGRESS OVERVIEW", "进展总览：核心链路全部打通，已有一台可演示整机", 2)
rows = [
    ("环境感知", "PMS5003ST 六参数采集", "完成", GREEN, "40 s 采集 42 帧真实数据"),
    ("本地显示", "ILI9341 实时界面 / 开机动画", "完成", GREEN, "点灯、GUI、动画已实机验证"),
    ("蓝牙通信", "USART6 + HC-06", "完成", GREEN, "9600 8N1 每秒上报"),
    ("手机 APP", "点灯 Blinker（iOS）", "完成", GREEN, "六项读数实时显示"),
    ("声光报警", "蜂鸣器（选做）", "待实施", AMBER, "方案已设计"),
    ("整机装配", "3D 打印外壳", "待实施", AMBER, "外形与开孔规划中"),
]
y0, rh = 1.62, 0.545
for i, (name, sub, st, col, ev) in enumerate(rows):
    yy = y0 + i * (rh + 0.09)
    card(s, 0.5, yy, 8.05, rh)
    dot = rect(s, 0.72, yy + 0.205, 0.13, 0.13, fill=col, rounded=True, radius=0.5)
    text(s, 0.98, yy + 0.075, 1.5, 0.4, name, size=14, bold=True, spacing=0,
         anchor=MSO_ANCHOR.MIDDLE)
    text(s, 2.42, yy + 0.075, 2.75, 0.4, sub, size=11.5, color=MUTED, spacing=0,
         anchor=MSO_ANCHOR.MIDDLE)
    chip(s, 5.32, yy + 0.135, 0.92, 0.28, st, col, size=11.5)
    text(s, 6.42, yy + 0.075, 2.0, 0.4, ev, size=10, color=MUTED, spacing=0,
         anchor=MSO_ANCHOR.MIDDLE)
card(s, 8.78, 1.62, 4.05, 3.62)
text(s, 9.05, 1.8, 3.5, 0.3, "手机端实测：点灯 Blinker（iOS）", size=12.5, bold=True, spacing=0)
pic(s, os.path.join(MEDIA, "ios_ok.jpg"), 9.62, 2.18, 2.57, 2.9)
footer(s, "证据：logs/blinker-uart6-verification-20261010.json · 屏幕读数实拍 · PILOT 验证记录")

# =====================================================================
# P3 需求分析与设计考虑
# =====================================================================
s = slide_new()
head(s, "REQUIREMENTS", "设计考虑：需求边界决定方案取舍", 3)
text(s, 0.5, 1.5, 9.0, 0.4,
     [{"t": [{"t": "设计原则：", "bold": True, "color": TEAL_DEEP},
             {"t": "本地实时可视 + 手机远程查看双通道；不依赖定制 PCB 也能交付。"}]}],
     size=15, spacing=0)
cards = [
    ("六项监测参数", TEAL,
     [("PM1.0 / PM2.5 / PM10", "颗粒物，µg/m³"),
      ("HCHO", "甲醛，mg/m³"),
      ("温度 / 湿度", "°C / %RH")]),
    ("双通道数据分发", TEAL,
     [("本地", "2.8″ TFT 实时读数 + 状态机"),
      ("远程", "蓝牙每秒上报 + 手机 APP"),
      ("不造假数据", "无有效帧时不发送零值")]),
    ("交付约束", AMBER,
     [("开发周期", "优先打通功能，再做结构"),
      ("焊接风险", "避免改焊桥 / 手工改板"),
      ("可复现", "开发板 + 扩展板组合方案")]),
]
for i, (t, col, items) in enumerate(cards):
    x = 0.5 + i * 4.27
    card(s, x, 2.15, 4.05, 4.35)
    text(s, x + 0.3, 2.42, 3.5, 0.4, t, size=17, bold=True, color=col, spacing=0)
    yy = 3.15
    for name, sub in items:
        rect(s, x + 0.3, yy + 0.09, 0.1, 0.1, fill=col, rounded=True, radius=0.5)
        text(s, x + 0.55, yy, 3.3, 0.34, name, size=13.5, bold=True, spacing=0)
        text(s, x + 0.55, yy + 0.32, 3.3, 0.6, sub, size=11.5, color=MUTED, spacing=0, lh=1.1)
        yy += 1.02
footer(s, "约束来源：板卡三版迭代经验 + 焊接桥风险 + 课程开发周期")

# =====================================================================
# P4 系统总体架构
# =====================================================================
s = slide_new()
head(s, "SYSTEM ARCHITECTURE", "系统总体方案：感知 → 主控 → 双通道输出", 4)
# 左：PMS
flow_box(s, 0.5, 2.5, 2.55, 1.5, TEAL_DEEP, "PMS5003ST", "六参数环境传感器\n5V 供电 · 3.3V 串口电平", tsize=14)
# 中：MCU
mcu = card(s, 3.62, 1.85, 3.35, 2.8)
text(s, 3.62, 2.1, 3.35, 0.5, "NUCLEO-F411RE", size=17, bold=True, align=PP_ALIGN.CENTER, spacing=2)
text(s, 3.62, 2.5, 3.35, 0.3, "STM32F411RE · 100 MHz\n512 KB Flash / 128 KB RAM",
     size=11, color=MUTED, align=PP_ALIGN.CENTER, spacing=0, lh=1.15)
# 数据流
flow_box(s, 3.82, 3.32, 1.1, 0.62, TEXT, "40 B 帧校验", tsize=11)
flow_box(s, 5.02, 3.32, 1.1, 0.62, TEXT, "六参数解析", tsize=11)
flow_box(s, 6.22, 3.32, 0.55, 0.62, TEXT, "分发", tsize=11)
text(s, 3.62, 4.15, 3.35, 0.3, "数据流：采集 → 校验 → 解析 → 双通道分发",
     size=10.5, color=MUTED, align=PP_ALIGN.CENTER, spacing=0)
# 右：两路输出
flow_box(s, 9.85, 1.95, 2.95, 1.35, TEAL_DEEP, "ILI9341 2.8″ TFT", "240×320 SPI · 实时读数 / 状态机\n500 ms 局部刷新", tsize=14)
flow_box(s, 9.85, 3.6, 2.95, 1.35, TEAL_DEEP, "HC-06 → 手机 APP", "USART6 · 9600 8N1\nJSON 每秒上报 · iOS 已验证", tsize=14)
# 连接箭头
arrow_r(s, 3.12, 3.25, 0.42)
text(s, 2.75, 2.85, 1.0, 0.3, "USART1", size=11, color=MUTED, align=PP_ALIGN.CENTER, spacing=0)
text(s, 2.75, 3.6, 1.0, 0.3, "9600 8N1", size=11, color=MUTED, align=PP_ALIGN.CENTER, spacing=0)
arrow_r(s, 7.25, 2.62, 0.42)
arrow_r(s, 7.25, 4.27, 0.42)
text(s, 6.83, 2.2, 1.3, 0.3, "SPI1 + GPIO", size=11, color=MUTED, align=PP_ALIGN.CENTER, spacing=0)
text(s, 6.83, 4.42, 1.3, 0.3, "USART6", size=11, color=MUTED, align=PP_ALIGN.CENTER, spacing=0)
# 底部：调试链路
flow_box(s, 3.62, 5.15, 3.35, 1.0, MUTED, "ST-Link / SWD", "烧录 · 调试 · 115200 日志（USART2 常驻）", tsize=12)
arrow_d(s, 5.3, 4.7, 0.3, color=LINE)
text(s, 0.5, 6.35, 12.3, 0.4,
     "引脚规划原则：显式指定串口引脚，避免占用屏幕的 PB6 / PA5；USART6 走 PA11/PA12 直连排针，不改 SB13/14/62/63 焊桥。",
     size=11.5, color=MUTED, spacing=0)

# =====================================================================
# P5 MCU 选型
# =====================================================================
s = slide_new()
head(s, "MODULE 1/6 · MCU", "MCU 选型：为什么是 NUCLEO-F411RE", 5)
rows = [
    ("STM32F411RE", (("NUCLEO-F411RE 开发板", TEAL_DEEP, True)), "100 MHz", "512 K / 128 K",
     "2×UART + 1×SPI", (("✅ 选用", GREEN, True))),
    ("STM32F103", "经典 F1 系列", "72 MHz", "64 K / 20 K", "双串口勉强、帧缓冲吃紧",
     (("✗", MUTED, False))),
    ("51 / AVR", "8 位单片机", "≤ 20 MHz", "≤ 8 K", "无法承载 320×240 界面",
     (("✗", MUTED, False))),
]
table_grid(s, 0.5, 1.6, 12.33, [2.15, 2.1, 1.35, 1.75, 3.58, 1.4], rows,
           ["候选", "说明", "主频", "Flash / RAM", "外设需求匹配", "结论"],
           aligns=[PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER,
                   PP_ALIGN.LEFT, PP_ALIGN.CENTER])
card(s, 0.5, 3.85, 12.33, 2.4)
text(s, 0.85, 4.08, 6.5, 0.4, "当前固件资源占用（本机构建实测）", size=15,
     bold=True, spacing=0)
text(s, 0.98, 4.6, 4.6, 0.28, "Flash 48 144 B / 512 KB（9.2%）", size=10.5, color=MUTED, spacing=0)
bar(s, 0.95, 4.88, 5.0, 0.26, 0.092, "")
text(s, 0.98, 5.3, 4.6, 0.28, "静态 RAM 8 988 B / 128 KB（6.9%）", size=10.5, color=MUTED, spacing=0)
bar(s, 0.95, 5.58, 5.0, 0.26, 0.069, "", color=TEAL_DEEP)
rect(s, 6.5, 4.15, 0.01, 1.75, fill=LINE)
text(s, 6.75, 4.22, 5.85, 1.7, [
    {"t": "选型结论", "size": 14, "bold": True, "color": TEAL_DEEP, "spacing": 4},
    {"t": "片上 ST-Link：烧录 / 调试 / 串口日志一条线，无需外接仿真器", "size": 12, "spacing": 3, "lh": 1.2},
    {"t": "显式指定串口引脚，避免占用屏幕的 PB6 / PA5 复用引脚", "size": 12, "spacing": 3, "lh": 1.2},
    {"t": "资源余量充足，为报警、曲线与外壳联调留出空间", "size": 12, "lh": 1.2},
], spacing=2)
footer(s, "证据：.pio/build/nucleo_f411re_uart6 构建日志 · firmware/MANIFEST.md")

# =====================================================================
# P6 传感器模块
# =====================================================================
s = slide_new()
head(s, "MODULE 2/6 · SENSOR", "传感器模块：PMS5003ST 六参数一颗搞定", 6)
card(s, 0.5, 1.62, 4.85, 5.2)
text(s, 0.8, 1.86, 4.3, 0.4, "选型理由", size=16, bold=True, color=TEAL_DEEP, spacing=0)
text(s, 0.8, 2.28, 4.3, 1.6, [
    {"t": "一颗传感器同时输出 PM1.0 / PM2.5 / PM10 / HCHO / 温度 / 湿度六项，", "size": 12.5, "lh": 1.25},
    {"t": "免去多传感器拼装与标定 —— PMS7003 无甲醛、PMS5003T 无甲醛，只有 ST 版本满足要求。", "size": 12.5, "lh": 1.25},
], spacing=2)
text(s, 0.8, 3.78, 4.3, 1.6, [
    {"t": "一根线接收、默认主动上报：", "size": 12.5, "bold": True, "color": TEAL_DEEP, "spacing": 3, "lh": 1.2},
    {"t": "TXD → D2 / PA10（USART1 RX，9600 8N1）", "size": 12.5, "spacing": 3, "lh": 1.2},
    {"t": "RXD 悬空：程序不发命令，纯接收", "size": 12.5, "spacing": 3, "lh": 1.2},
    {"t": "SET / RESET 悬空（内部上拉）", "size": 12.5, "spacing": 3, "lh": 1.2},
    {"t": "VCC = 5 V，串口逻辑 3.3 V，与开发板共地", "size": 12.5, "lh": 1.2},
], spacing=2)
text(s, 0.8, 5.78, 4.3, 0.35, "接法要点", size=13.5, bold=True, spacing=0)
text(s, 0.8, 6.14, 4.3, 0.9, [
    {"t": "三线连接（VCC / GND / TXD）即可出全部六项读数", "size": 11.5, "color": MUTED, "spacing": 3, "lh": 1.2},
    {"t": "无需驱动库、无需 AT 指令，上电即持续输出 40 字节帧", "size": 11.5, "color": MUTED, "lh": 1.2},
], spacing=2)
card(s, 5.6, 1.62, 7.23, 5.2)
text(s, 5.9, 1.86, 6.6, 0.4, "解析软件：40 字节帧 + 校验状态机", size=16, bold=True,
     color=TEAL_DEEP, spacing=0)
fx, fy = 5.92, 2.42
cols = [("找帧头 0x42 0x4D", 1.28), ("校验长度 0x24", 1.28), ("累加和 = 末尾 16 位", 1.42),
        ("校验失败 → 丢帧重找", 1.42)]
xs = [fx, fx + 1.46, fx + 2.92, fx + 4.52]
for i, ((t, w), bx) in enumerate(zip(cols, xs)):
    col = GREEN if i < 3 else AMBER
    flow_box(s, bx, fy, w, 0.78, col, t, tsize=11)
    if i < 3:
        arrow_r(s, bx + w + 0.005, fy + 0.39, 0.15)
text(s, fx, fy + 0.98, 6.6, 1.15, [
    {"t": "通过 → 更新六项读数并上屏 / 上报；失败 → 丢弃整帧重新寻找帧头", "size": 12.5, "spacing": 4},
    {"t": "半帧停顿 > 250 ms 丢弃；连续 10 s 无有效帧 → 屏幕 NO DATA 并清空读数", "size": 12.5, "spacing": 4},
    {"t": "单位换算：温度 = 有符号数/10；湿度 = 值/10；甲醛 = 值/1000 → mg/m³", "size": 12.5},
], spacing=2)
for i, (num, lab) in enumerate([("42", "连续帧（40 s）"), ("0", "校验错误"), ("0", "长度错误")]):
    bx = 6.0 + i * 2.1
    card(s, bx, 5.35, 1.85, 1.1, fill=BG)
    text(s, bx, 5.48, 1.85, 0.55, num, size=26, bold=True, color=TEAL,
         align=PP_ALIGN.CENTER, spacing=0)
    text(s, bx, 6.02, 1.85, 0.3, lab, size=11, color=MUTED, align=PP_ALIGN.CENTER, spacing=0)
footer(s, "证据：logs/pms-verification.json · 30 s WARMUP 为颗粒物风扇稳定时间")

# =====================================================================
# P7 显示模块
# =====================================================================
s = slide_new()
head(s, "MODULE 3/6 · DISPLAY", "显示模块：ILI9341 本地面板与开机动画", 7)
card(s, 0.5, 1.62, 5.35, 5.2)
text(s, 0.8, 1.86, 4.8, 0.4, "选型：2.8″ SPI TFT（ILI9341）", size=16, bold=True,
     color=TEAL_DEEP, spacing=0)
text(s, 0.8, 2.3, 4.85, 2.2, [
    {"t": "240×320 · RGB 65K · SPI 仅需 5 根线（SCK/MOSI/CS/DC/RESET）", "size": 12.5, "spacing": 4},
    {"t": "资料齐全、例程成熟，Adafruit_ILI9341 1.6.4 稳定驱动", "size": 12.5, "spacing": 4},
    {"t": "接线：CS=D10/PB6、DC=D4/PB5、RESET=D7/PA8、MOSI=D11/PA7、SCK=D13/PA5、背光常亮", "size": 12.5, "spacing": 4, "lh": 1.2},
    {"t": "触摸 / SD 卡本期不启用", "size": 12.5, "color": MUTED},
], spacing=2)
text(s, 0.8, 4.62, 4.85, 0.35, "软件亮点", size=14, bold=True, spacing=0)
text(s, 0.8, 5.0, 4.85, 1.7, [
    {"t": [{"t": "开机动画：", "bold": True, "size": 12.5},
            {"t": "角色图转 4-bit 灰度数组入库（15 KB Flash），5 KiB 分条缓冲绘制，约 3.5 s 进入监测页", "size": 12.5}], "spacing": 5, "lh": 1.2},
    {"t": [{"t": "白屏优化：", "bold": True, "size": 12.5},
            {"t": "先写入完整首帧再发 DISPON；运行期每 500 ms 仅局部刷新数值区", "size": 12.5}], "spacing": 5, "lh": 1.2},
    {"t": [{"t": "状态机上屏：", "bold": True, "size": 12.5},
            {"t": "WAITING / WARMUP / LIVE / NO DATA / SENSOR ERROR", "size": 12.5}], "lh": 1.2},
], spacing=2)
# 右：界面线框
card(s, 6.1, 1.62, 3.1, 5.2)
text(s, 6.1, 1.78, 3.1, 0.3, "界面布局（固件绘制逻辑）", size=12, bold=True,
     color=MUTED, align=PP_ALIGN.CENTER, spacing=0)
fx, fy, fw, fh = 6.38, 2.25, 2.54, 4.3
rect(s, fx, fy, fw, fh, fill=BG, line=LINE, lw=1.0, rounded=True, radius=0.02)
text(s, fx + 0.12, fy + 0.1, 1.6, 0.25, "AIR MONITOR", size=9.5, bold=True, color=TEAL_DEEP, spacing=0)
text(s, fx + 1.75, fy + 0.11, 0.7, 0.25, "PMS5003ST", size=7, color=MUTED, spacing=0)
rect(s, fx + 0.1, fy + 0.42, fw - 0.2, 0.62, fill=CARD, rounded=True, radius=0.1)
text(s, fx + 0.2, fy + 0.48, 1.0, 0.2, "PM2.5  ug/m3", size=6.5, color=MUTED, spacing=0)
text(s, fx + 0.2, fy + 0.62, 1.2, 0.36, "64", size=20, bold=True, color=TEAL, spacing=0)
text(s, fx + 1.62, fy + 0.48, 0.8, 0.2, "PM1.0   39", size=7, spacing=0)
text(s, fx + 1.62, fy + 0.72, 0.8, 0.2, "PM10    76", size=7, spacing=0)
rect(s, fx + 0.1, fy + 1.14, 1.16, 0.52, fill=CARD, rounded=True, radius=0.1)
rect(s, fx + 1.34, fy + 1.14, 1.16, 0.52, fill=CARD, rounded=True, radius=0.1)
text(s, fx + 0.18, fy + 1.19, 1.0, 0.18, "TEMP (C)", size=6.5, color=MUTED, spacing=0)
text(s, fx + 0.18, fy + 1.34, 1.0, 0.26, "22.9", size=12, bold=True, spacing=0)
text(s, fx + 1.42, fy + 1.19, 1.0, 0.18, "HUMIDITY (%)", size=6.5, color=MUTED, spacing=0)
text(s, fx + 1.42, fy + 1.34, 1.0, 0.26, "69.1", size=12, bold=True, spacing=0)
rect(s, fx + 0.1, fy + 1.78, fw - 0.2, 0.4, fill=CARD, rounded=True, radius=0.1)
text(s, fx + 0.18, fy + 1.86, 0.6, 0.2, "HCHO", size=6.5, color=MUTED, spacing=0)
text(s, fx + 0.75, fy + 1.86, 1.2, 0.2, "0.000", size=9, bold=True, spacing=0)
text(s, fx + 1.9, fy + 1.87, 0.55, 0.2, "mg/m3", size=6.5, color=MUTED, spacing=0)
text(s, fx + 0.12, fy + 3.35, fw - 0.24, 0.2, "WARMUP: 3 s   receiving valid data", size=6.5, color=AMBER, spacing=0)
text(s, fx + 0.12, fy + 3.6, fw - 0.24, 0.2, "Frames:42  Age:0s  Bad:0", size=6.5, color=MUTED, spacing=0)
card(s, 9.48, 1.62, 3.35, 5.2)
text(s, 9.73, 1.86, 2.85, 0.4, "实物验证", size=16, bold=True, color=TEAL_DEEP, spacing=0)
pic(s, os.path.join(MEDIA, "screen_real.jpg"), 9.72, 2.35, 2.85, 2.44)
text(s, 9.73, 4.95, 2.9, 1.6, [
    {"t": "开机动画实测 3 465 ms，绘制 31 帧，期间传感器/蓝牙不间断", "size": 11, "color": MUTED, "spacing": 4, "lh": 1.2},
    {"t": "启动白屏优化后，复位启动不再明显闪白（用户实屏确认）", "size": 11, "color": MUTED, "lh": 1.2},
], spacing=2)
footer(s, "证据：logs/boot-verification.json · logs/startup-verification.json")

# =====================================================================
# P8 蓝牙模块
# =====================================================================
s = slide_new()
head(s, "MODULE 4/6 · BLUETOOTH", "蓝牙模块：从焊桥改造到免焊桥 + 通用 App", 8)
rows = [
    ("方案 A：USART2", "HC-06 经典 SPP", "需改 SB13/14/62/63 焊桥", "安卓仅收不发", ("✗ 弃用", MUTED, True)),
    ("方案 B：USART6", "走 PA11/PA12 直连排针", "免焊桥，仅换两根杜邦线", "安卓端收发未打通", ("过渡", AMBER, True)),
    ("方案 C：USART6 + Blinker", "BLE JSON 数值组件", "免焊桥 · 通用 App", "iOS 六项读数全显", ("✅ 当前", GREEN, True)),
]
table_grid(s, 0.5, 1.6, 12.33, [2.3, 3.3, 3.2, 2.43, 1.1], rows,
           ["方案", "协议", "接线成本", "手机端结果", "结论"],
           row_h=0.5,
           aligns=[PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.CENTER])
card(s, 0.5, 3.72, 5.9, 3.08)
text(s, 0.8, 3.94, 5.3, 0.4, "当前接线与协议", size=15, bold=True, color=TEAL_DEEP, spacing=0)
text(s, 0.8, 4.37, 5.35, 1.25, [
    {"t": "模块 RXD → PA11 / CN10-14，TXD → PA12 / CN10-12", "size": 12.5, "spacing": 4},
    {"t": "9600 8N1 · 每秒一帧 JSON · 独立 USART6 不占用调试口", "size": 12.5, "spacing": 4},
    {"t": "换线必须断电重上电后再烧录", "size": 12.5, "color": MUTED},
], spacing=2)
rect(s, 0.8, 5.5, 5.3, 1.08, fill=BG, rounded=True, radius=0.08)
text(s, 0.98, 5.6, 5.0, 0.9, [
    {"t": "{\"pm25\":{\"val\":24},\"hcho\":{\"val\":0.000},", "size": 11, "font": "Consolas", "spacing": 2},
    {"t": " \"temp\":{\"val\":19,\"uni\":\"℃\"},\"humi\":{\"val\":79.7,\"uni\":\"%\"}}", "size": 11, "font": "Consolas"},
], spacing=0)
card(s, 6.65, 3.72, 6.18, 3.08)
text(s, 6.95, 3.94, 5.6, 0.4, "实现要点", size=15, bold=True, color=TEAL_DEEP, spacing=0)
text(s, 6.95, 4.37, 5.6, 2.2, [
    {"t": [{"t": "不装完整 Blinker 库", "size": 12.5, "bold": True},
            {"t": "，固件按组件键名自组 JSON —— 兼容协议、省 Flash", "size": 12.5}], "spacing": 6, "lh": 1.2},
    {"t": [{"t": "1 KiB 环形发送队列", "size": 12.5, "bold": True},
            {"t": "，非阻塞分批写出，动画期间也不丢数据", "size": 12.5}], "spacing": 6, "lh": 1.2},
    {"t": [{"t": "保留命令通道", "size": 12.5, "bold": True},
            {"t": "：PING / GET / STREAM ON·OFF / HELP；响应 Blinker 状态查询", "size": 12.5}], "spacing": 6, "lh": 1.2},
    {"t": [{"t": "无效数据不发送", "size": 12.5, "bold": True},
            {"t": "：无有效帧时不报零值，等待恢复自动续传", "size": 12.5}], "lh": 1.2},
], spacing=2)
footer(s, "证据：docs/Blinker-integration.md · logs/blinker-uart6-verification-20261010.json")

# =====================================================================
# P9 声光报警（选做）
# =====================================================================
s = slide_new()
head(s, "MODULE 5/6 · ALARM", "声光报警：方案设计完成，待实施", 9)
chip(s, 12.1, 0.66, 0.72, 0.3, "选做", AMBER, fg=INK, size=11.5)
card(s, 0.5, 1.7, 6.0, 5.1)
text(s, 0.8, 1.94, 5.4, 0.4, "报警策略：阈值分级", size=16, bold=True, color=TEAL_DEEP, spacing=0)
steps = [
    ("阈值判定", "PM2.5 / HCHO 等参数超过设定阈值（分级）"),
    ("光报警", "屏幕数值变色 + 状态行提示，复用现有界面"),
    ("声报警", "蜂鸣器断续提示音，超限消除后自动停止"),
]
yy = 2.5
for i, (t, sub) in enumerate(steps):
    flow_box(s, 0.85, yy, 2.1, 0.72, TEAL_DEEP, t, tsize=12.5)
    text(s, 3.1, yy + 0.03, 3.3, 0.7, sub, size=11.5, color=MUTED, spacing=0, lh=1.15)
    if i < 2:
        arrow_d(s, 1.9, yy + 0.78, 0.26)
    yy += 1.1
text(s, 0.85, 5.85, 5.4, 0.7,
     [{"t": [{"t": "触发逻辑：", "bold": True, "size": 12},
             {"t": "上电自检响一声 → 主循环比较阈值 → 超限报警 / 回落解除", "size": 12}]}],
     spacing=0, lh=1.2)
card(s, 6.65, 1.7, 6.18, 5.1)
text(s, 6.95, 1.94, 5.6, 0.4, "选型与硬件设计", size=16, bold=True, color=TEAL_DEEP, spacing=0)
cards2 = [
    ("蜂鸣器选型", "3.3 V 有源蜂鸣器：驱动简单、免 PWM 音调方案"),
    ("驱动电路", "GPIO → 1 kΩ 基极电阻 → NPN 三极管 → 蜂鸣器；续流二极管与去耦电容"),
    ("引脚规划", "选用空闲 GPIO，避开 LCD 的 PA5 / PB6 与两路串口；PWM 方案备用"),
]
yy = 2.5
for t, sub in cards2:
    text(s, 6.95, yy, 5.5, 0.32, t, size=13.5, bold=True, spacing=0)
    text(s, 6.95, yy + 0.3, 5.6, 0.75, sub, size=11.5, color=MUTED, spacing=0, lh=1.2)
    yy += 1.2
rect(s, 6.95, 6.0, 0.42, 0.42, fill=BG, line=LINE, lw=1.0, rounded=True, radius=0.25)
text(s, 7.5, 6.05, 5.2, 0.35, "选做项：功能链路已设计，整机装配阶段实施", size=11.5,
     color=MUTED, spacing=0)
footer(s, "定位：满足“声光报警”模块设计要求；实施排在整机装配阶段")

# =====================================================================
# P10 手机 APP
# =====================================================================
s = slide_new()
head(s, "MODULE 6/6 · APP", "手机 APP：两条路线，一条已跑通", 10)
card(s, 0.5, 1.62, 4.05, 5.2)
text(s, 0.78, 1.84, 3.6, 0.35, "自研 App（MIT App Inventor）", size=13.5, bold=True, spacing=0)
chip(s, 0.78, 2.26, 0.98, 0.28, "安卓端", AMBER, fg=INK, size=11)
pic(s, os.path.join(MEDIA, "android_app.jpg"), 1.26, 2.72, 2.52, 3.2)
text(s, 0.78, 6.05, 3.7, 0.7, [
    {"t": "为 $ENV 协议自研 · 蓝牙状态已连接", "size": 11, "color": MUTED, "spacing": 3},
    {"t": "但数值未更新 —— 待安卓端适配", "size": 11, "color": AMBER},
], spacing=0)
card(s, 4.75, 1.62, 4.05, 5.2)
text(s, 5.03, 1.84, 3.6, 0.35, "通用 App（点灯 Blinker）", size=13.5, bold=True, spacing=0)
chip(s, 5.03, 2.26, 0.98, 0.28, "iOS 端", GREEN, size=11)
pic(s, os.path.join(MEDIA, "ios_ok.jpg"), 5.52, 2.72, 2.52, 3.2)
text(s, 5.03, 6.05, 3.7, 0.7, [
    {"t": "配置 6 个数字组件键名即用", "size": 11, "color": MUTED, "spacing": 3},
    {"t": "pm1 / pm25 / pm10 / hcho / temp / humi", "size": 11, "color": TEAL_DEEP, "bold": True},
], spacing=0)
card(s, 9.0, 1.62, 3.83, 5.2)
text(s, 9.28, 1.84, 3.3, 0.35, "取舍与分工", size=13.5, bold=True, color=TEAL_DEEP, spacing=0)
text(s, 9.28, 2.3, 3.35, 2.6, [
    {"t": "数据链路本身（板 → 模块 → 手机）已由 Blinker + iOS 验证跑通", "size": 12.5, "spacing": 8, "lh": 1.25},
    {"t": "自研 App 定位为界面定制化方向，协议字段与固件一一对应", "size": 12.5, "spacing": 8, "lh": 1.25},
    {"t": "固件同时保留 $ENV 旧协议构建（nucleo_f411re_env），两条路线互不冲突", "size": 12.5, "spacing": 8, "lh": 1.25},
    {"t": "后续：补齐安卓端解析适配，作为验收演示的备用通道", "size": 12.5, "color": MUTED, "lh": 1.25},
], spacing=2)
rect(s, 9.32, 5.12, 3.15, 0.02, fill=LINE)
for i, (lab, col) in enumerate([("iOS 完成", GREEN), ("安卓适配", AMBER), ("验收演示", MUTED)]):
    dx = 9.32 + i * 1.575
    rect(s, dx, 5.06, 0.14, 0.14, fill=col, rounded=True, radius=0.5)
    text(s, dx - 0.48, 5.32, 1.1, 0.3, lab, size=10.5, color=MUTED,
         align=PP_ALIGN.CENTER, spacing=0)
text(s, 9.28, 5.92, 3.4, 0.8,
     "KPI：验收时两条手机通道均可演示六项实时读数", size=12, bold=True,
     color=TEAL_DEEP, spacing=0, lh=1.25)
footer(s, "证据：05_素材 ios_成功.jpg · APP_手机运行截图_2.jpg · docs/HC06-integration.md")

# =====================================================================
# P11 目前进展
# =====================================================================
s = slide_new()
head(s, "MILESTONES", "目前进展：核心链路全部实测通过", 11)
stats = [
    ("48 144 B", "Flash 占用（9.2%）", TEAL),
    ("8 988 B", "静态 RAM（6.9%）", TEAL),
    ("14 + 6", "项自动化测试通过", TEAL),
    ("42 / 42", "帧校验全通过（40 s）", GREEN),
]
for i, (num, lab, col) in enumerate(stats):
    x = 0.5 + i * 3.14
    card(s, x, 1.62, 2.94, 1.55)
    text(s, x, 1.85, 2.94, 0.7, num, size=32, bold=True, color=col,
         align=PP_ALIGN.CENTER, spacing=0)
    text(s, x, 2.62, 2.94, 0.35, lab, size=12, color=MUTED, align=PP_ALIGN.CENTER, spacing=0)
card(s, 0.5, 3.42, 7.6, 3.35)
text(s, 0.8, 3.64, 7.0, 0.4, "已完成的验证节点", size=15, bold=True, color=TEAL_DEEP, spacing=0)
items = [
    ("传感器", "40 s 采集 42 帧，长度 / 校验 / 半帧超时错误均为 0"),
    ("显示", "点灯 → GUI → 开机动画 → 白屏优化，逐版实机验证"),
    ("蓝牙", "USART6 接线后烧录校验通过；COM3 只读采集到连续有效 JSON"),
    ("手机端", "iOS Blinker 六项读数实时显示（见附图）"),
    ("工程化", "8 个阶段快照备份 · 每版固件留存 SHA-256 指纹 · 20 项自动化测试"),
]
yy = 4.12
for name, ev in items:
    rect(s, 0.85, yy + 0.1, 0.11, 0.11, fill=TEAL, rounded=True, radius=0.5)
    text(s, 1.08, yy - 0.02, 1.05, 0.35, name, size=12.5, bold=True, spacing=0)
    text(s, 2.2, yy - 0.02, 5.75, 0.6, ev, size=12, color=MUTED, spacing=0, lh=1.15)
    yy += 0.5
card(s, 8.35, 3.42, 4.48, 3.35)
text(s, 8.62, 3.64, 4.0, 0.4, "实机记录", size=15, bold=True, color=TEAL_DEEP, spacing=0)
pic(s, os.path.join(MEDIA, "screen_real.jpg"), 8.75, 4.1, 1.85, 2.47)
text(s, 10.75, 4.25, 1.95, 2.2, [
    {"t": "屏幕六项真实读数", "size": 11, "spacing": 2, "lh": 1.25},
    {"t": "PM2.5 64 · 22.9℃ · 69%RH", "size": 11, "color": TEAL_DEEP, "spacing": 6, "lh": 1.25},
    {"t": "开机动画 3 465 ms\n绘制 31 帧", "size": 11, "spacing": 6, "lh": 1.25},
    {"t": "蓝牙每秒一帧 JSON\niOS 端持续刷新", "size": 11, "lh": 1.25},
], spacing=2)
footer(s, "证据：logs/ · firmware/MANIFEST.md · 每份验证 JSON 含固件 SHA-256")

# =====================================================================
# P12 遇到的问题与解决方案
# =====================================================================
s = slide_new()
head(s, "CHALLENGES", "遇到的问题与解决方案", 12)
probs = [
    ("问题一", "板子迭代太多，每版都有新问题", [
        ("现象", "初版到第三版改版逐版推进，丝印与实际信号对不上、走线错误、连线依赖焊桥改造"),
        ("根因", "定制 PCB 从改图到打样周期长，每轮改动都引入新缺陷，延误功能联调"),
        ("解决", "转向 NUCLEO 开发板 + 扩展板免焊接方案；先冻结全部功能，再规划外壳"),
    ]),
    ("问题二", "蓝牙在安卓 / iOS 两端适配不通", [
        ("现象", "模块配对成功，但安卓自研 App 数值一直不更新（界面停留“等待蓝牙数据”）"),
        ("根因", "手机端 App 与固件协议适配问题，且依赖 USART2 焊桥改造存在不确定性"),
        ("解决", "换 USART6 免焊桥排除硬件变量；改用 Blinker 通用 App，iOS 端六项读数全部显示"),
    ]),
    ("问题三", "屏幕开机瞬间闪白", [
        ("现象", "上电 / 复位后先出现一段白屏，再进入开机动画"),
        ("根因", "背光是 3V3 常亮、上电即亮，软件的关显命令管不到背光"),
        ("解决", "显示保持关闭 → 完整首帧写入显存 → 再发 DISPON 点亮，白屏基本消除"),
    ]),
]
for i, (tag, title, rows_) in enumerate(probs):
    y = 1.62 + i * 1.78
    card(s, 0.5, y, 12.33, 1.62)
    chip(s, 0.78, y + 0.22, 0.82, 0.3, tag, INK, size=11.5)
    text(s, 1.78, y + 0.17, 4.4, 0.4, title, size=15, bold=True, spacing=0)
    yy = y + 0.62
    for lab, txt in rows_:
        text(s, 0.85, yy, 0.62, 0.28, lab, size=11.5, bold=True, color=TEAL_DEEP, spacing=0)
        text(s, 1.55, yy - 0.012, 11.05, 0.29, txt, size=11.5, color=TEXT, spacing=0, lh=1.1)
        yy += 0.315
footer(s, "证据：01_报告/03_PCB迭代记录.pptx · docs/Blinker-integration.md · logs/startup-verification.json")

# =====================================================================
# P13 下一步改进计划
# =====================================================================
s = slide_new()
head(s, "NEXT STEPS", "下一步改进计划：三项收尾工作", 13)
steps = [
    ("01", "蜂鸣器报警（选做）",
     ["选 3.3 V 有源蜂鸣器 + 三极管驱动电路",
      "阈值分级触发，与屏幕变色联动",
      "规避 PA5 / PB6 与两路串口引脚"],
     "声光报警闭环 · 增强演示效果"),
    ("02", "3D 打印外壳与整机装配",
     ["外形建模与屏幕开窗定位",
      "传感器进气口 / 蜂鸣器声孔 / 排针检修口",
      "安装体与线束固定，整机联调"],
     "从“开发板演示”到“完整样机”"),
    ("03", "收尾与文档",
     ["修正外设接口表，对齐当前固件引脚",
      "录制整机演示视频（含手机端画面）",
      "文档与固件归档、指纹补齐"],
     "交付物完整、可复现"),
]
for i, (num, title, items, tagline) in enumerate(steps):
    x = 0.5 + i * 4.27
    card(s, x, 1.72, 4.05, 4.45)
    text(s, x + 0.3, 1.94, 1.2, 0.9, num, size=42, bold=True, color=TEAL, spacing=0)
    text(s, x + 0.3, 2.92, 3.45, 0.42, title, size=15.5, bold=True, spacing=0)
    yy = 3.5
    for it in items:
        rect(s, x + 0.32, yy + 0.11, 0.09, 0.09, fill=TEAL, rounded=True, radius=0.5)
        text(s, x + 0.56, yy, 3.25, 0.64, it, size=12, color=MUTED, spacing=0, lh=1.2)
        yy += 0.62
    chip(s, x + 0.3, 5.46, 2.6, 0.34, tagline, INK, size=11.5)
footer(s, "实施顺序：先报警模块（小改动）→ 外壳设计装配（依赖外形冻结）→ 文档收尾")

# =====================================================================
# P14 与预期目标的差距与改进方案
# =====================================================================
s = slide_new()
head(s, "GAP ANALYSIS", "与预期目标的差距与具体改进方案", 14)
rows = [
    ("多参数环境实时采集", ("完成", GREEN, True), "6 参数 40 s 连续实测 42 帧无错", "—"),
    ("2.8″ TFT 本地实时显示", ("完成", GREEN, True), "读数 + 状态机 + 开机动画", "—"),
    (("蓝牙无线传输 · 手机实时显示", AMBER, True), ("iOS 完成", AMBER, True),
     "iOS 六项读数已显示；安卓端待适配", "补齐安卓解析 → 验收前完成"),
    ("声光报警（选做）", ("设计完成", AMBER, True), "方案 / 器件 / 驱动电路已定", "整机装配阶段实现"),
    ("完整可演示整机", ("样机阶段", AMBER, True), "开发板 + 扩展板组合", "3D 外壳装配 → 完整样机"),
]
table_grid(s, 0.5, 1.62, 12.33, [3.4, 1.5, 3.7, 3.73], rows,
           ["预期目标（开题）", "当前状态", "依据", "具体改进方案"],
           row_h=0.78, head_h=0.46,
           aligns=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.LEFT])
text(s, 0.5, 6.35, 12.3, 0.45,
     "说明：四项核心功能（采集 / 显示 / 传输 / App）已全部跑通；剩余差距集中在选做项与结构装配，均在可实施范围内。",
     size=12, color=MUTED, spacing=0)

# =====================================================================
# P15 封底
# =====================================================================
s = slide_new(dark=True)
text(s, 0.75, 2.55, 7.5, 1.4, "恳请各位老师批评指正", size=38, bold=True, color=WHITE, spacing=4)
text(s, 0.75, 3.9, 7.0, 0.4, "基于 STM32F411RE 的多参数空气质量监测系统", size=15,
     color=TEAL, spacing=0)
text(s, 0.75, 5.4, 7.0, 0.7, [
    {"t": "李昊伦 / 杨皓 / 赵旭东", "size": 14, "spacing": 4},
    {"t": "2026 年 10 月", "size": 12, "color": MUTED},
], color=WHITE)
pic(s, os.path.join(MEDIA, "screen_real.jpg"), 9.35, 1.15, 3.35, 5.2)

for i, sl in enumerate(prs.slides, start=1):
    pass

prs.save(OUT)
print("saved:", OUT)
print("slides:", len(prs.slides._sldIdLst))
