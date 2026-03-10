from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"C:\Users\Roy\Documents\New project")
ASSET_DIR = ROOT / "publish_assets" / "zhihu_smartwatch_guide_20260310"
OUT_DIR = ASSET_DIR / "final"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PDF_PATH = OUT_DIR / "zhihu_smartwatch_buying_guide_20260310_final.pdf"

PAGE_W = 1654
PAGE_H = 2339
MARGIN_X = 92
TOP = 88
BOTTOM = 110
CONTENT_W = PAGE_W - MARGIN_X * 2

BG = "#F5F1EA"
TEXT = "#1F1F1F"
MUTED = "#5B5751"
ACCENT = "#123E52"
LINE = "#D8CFC3"
TABLE_BG = "#FFFFFF"
TABLE_ALT = "#F1F5F7"

FONT = r"C:\Windows\Fonts\msyh.ttc"
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"


def font(size: int, bold: bool = False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


TITLE = font(52, True)
H2 = font(34, True)
BODY = font(25, False)
SMALL = font(19, False)
TABLE_HEAD = font(20, True)
TABLE_BODY = font(18, False)


TITLE_TEXT = "2026 智能手表怎么选？Apple Watch、华为 WATCH、Garmin Forerunner 一篇讲清"
LEAD_TEXT = (
    "智能手表最容易买错的地方，不是产品不够好，而是把完全不同路线的表放在同一个标准里硬比。"
    "如果你用 iPhone，Apple Watch 通常是最省心的主路；如果你是安卓用户，更在意续航、健康和日常通勤佩戴，"
    "华为 WATCH 更容易成立；如果你本来就是跑步、骑行、训练导向，Garmin Forerunner 的逻辑会更对。"
)

L0_BULLETS = [
    "先看手机生态，再看使用场景，最后再缩到预算和系列，决策效率会高很多。",
    "Apple Watch 强在生态协同和日常完成度，华为 WATCH 强在续航与健康平衡，Garmin Forerunner 强在训练和 GPS。",
    "不要先看参数表。先把自己归类成通勤型、均衡型还是训练型，后面的选择会快很多。",
]

COMPARE_HEADER = ["维度", "Apple Watch", "华为 WATCH", "Garmin Forerunner"]
COMPARE_ROWS = [
    ["核心路线", "iPhone 生态里的主力日常表", "安卓友好、续航与健康平衡", "训练导向的专业工具表"],
    ["健康功能", "健康记录完整，和 iPhone/健康生态配合顺", "健康能力和日常佩戴体验更均衡", "偏训练监测和恢复逻辑，日常健康不是第一卖点"],
    ["外观材质", "设计成熟，日常佩戴接受度高", "款式选择更丰富，通勤佩戴更友好", "更偏工具化和训练风格"],
    ["续航节奏", "日常够用，但不是长续航路线", "更适合在意少充电、长期佩戴的人", "长训练场景更稳，但日常智能体验不是重点"],
    ["运动 / GPS", "基础运动和日常健身够用", "均衡够用，偏通勤+轻运动", "GPS、训练计划、恢复指标更强"],
    ["更适合谁", "深度 iPhone 用户", "安卓用户，重视健康和续航的人", "跑步、骑行、训练目标明确的人"],
]

BUDGET_HEADER = ["预算段", "优先看谁", "更适合什么人", "容易踩的坑"]
BUDGET_ROWS = [
    ["1000-2000 元", "入门系列 / 基础款", "第一块表、轻运动、以通知和健康记录为主", "一上来只盯旗舰功能，忽视续航和佩戴感受"],
    ["2000-3000 元", "主力均衡款", "通勤 + 健身都要兼顾的大多数用户", "只看参数，不看生态和日常使用频率"],
    ["3000 元以上", "高端系列 / 训练向系列", "高频佩戴、训练需求更强、预算更充足", "以为越贵就一定更适合自己"],
]

SHORTLIST = [
    "Apple Watch SE 3：更适合 iPhone 用户、第一次买表、预算更敏感的人。",
    "Apple Watch Series 11：更适合大多数 iPhone 用户，通勤、健康、基础运动都要兼顾。",
    "Apple Watch Ultra 3：更适合户外、训练、高预算人群，不是普通入门用户的默认答案。",
    "HUAWEI WATCH GT 6 / GT 6 Pro：更适合安卓用户，想在续航、健康和通勤佩戴之间拿平衡。",
    "HUAWEI WATCH 5：更适合更看重旗舰感和完整日常体验的安卓用户。",
    "Garmin Forerunner 265：更适合跑步入门到进阶用户。",
    "Garmin Forerunner 570 / 970：更适合训练更重、路线和恢复需求更强的人。",
]

MISTAKES = [
    "把 Apple Watch、华为 WATCH、Garmin Forerunner 当成同一类产品硬比。",
    "把“能记录运动”和“适合训练”混为一谈。",
    "一上来只看最贵的系列，没有先按手机生态和场景做第一轮筛选。",
]

STEPS = [
    "先确认手机生态：iPhone 还是安卓。",
    "再确认主要场景：通勤、均衡、训练，哪个优先级最高。",
    "然后定预算：1000-2000、2000-3000、3000+。",
    "先缩到品牌，再缩到系列，最后才看具体型号和细节参数。",
]

SOURCE_TEXT = (
    "资料说明：本文的品牌与系列判断，优先参考 Apple、华为、Garmin 官方公开产品页与发布资料。"
    "正式发布前，仍应按品牌当前在售页面做最后一轮核对。"
)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, use_font, max_width: int) -> list[str]:
    lines: list[str] = []
    for para in text.split("\n"):
        if not para:
            lines.append("")
            continue
        current = ""
        for ch in para:
            test = current + ch
            if draw.textbbox((0, 0), test, font=use_font)[2] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = ch
        if current:
            lines.append(current)
    return lines


def new_page() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (PAGE_W, PAGE_H), BG)
    return img, ImageDraw.Draw(img)


def draw_text_block(draw, text: str, x: int, y: int, use_font, fill: str, max_width: int, line_gap: int = 10) -> int:
    for line in wrap_text(draw, text, use_font, max_width):
        if line == "":
            y += use_font.size + line_gap
            continue
        draw.text((x, y), line, font=use_font, fill=fill)
        y += use_font.size + line_gap
    return y


def paste_image(page: Image.Image, path: Path, x: int, y: int, target_w: int, target_h: int) -> int:
    img = Image.open(path).convert("RGBA")
    bg_img = Image.new("RGB", img.size, "#FFFFFF")
    bg_img.paste(img, mask=img.split()[-1])
    img = bg_img
    img.thumbnail((target_w, target_h))
    bg = Image.new("RGB", (target_w, img.height + 24), "#FFFFFF")
    bg.paste(img, ((target_w - img.width) // 2, 12))
    page.paste(bg, (x, y))
    return y + bg.height


def draw_bullets(draw, items: list[str], x: int, y: int, width: int) -> int:
    for item in items:
        y = draw_text_block(draw, f"• {item}", x, y, BODY, TEXT, width, 9)
        y += 4
    return y + 10


def draw_table(draw, x: int, y: int, col_widths: list[int], header: list[str], rows: list[list[str]]) -> int:
    table_width = sum(col_widths)
    line_color = "#D7DDE3"
    cell_pad_x = 10
    cell_pad_y = 8

    def row_height(values: list[str], use_font) -> int:
        heights = []
        for value, width in zip(values, col_widths):
            lines = wrap_text(draw, value, use_font, width - cell_pad_x * 2)
            heights.append(max(1, len(lines)) * (use_font.size + 5) + cell_pad_y * 2)
        return max(heights)

    head_h = row_height(header, TABLE_HEAD)
    draw.rectangle((x, y, x + table_width, y + head_h), fill=ACCENT, outline=line_color, width=2)
    cx = x
    for idx, title in enumerate(header):
        draw.rectangle((cx, y, cx + col_widths[idx], y + head_h), outline=line_color, width=2)
        draw_text_block(draw, title, cx + cell_pad_x, y + cell_pad_y, TABLE_HEAD, "#FFFFFF", col_widths[idx] - cell_pad_x * 2, 5)
        cx += col_widths[idx]
    y += head_h
    for ridx, row in enumerate(rows):
        h = row_height(row, TABLE_BODY)
        fill = TABLE_BG if ridx % 2 == 0 else TABLE_ALT
        draw.rectangle((x, y, x + table_width, y + h), fill=fill, outline=line_color, width=2)
        cx = x
        for idx, value in enumerate(row):
            draw.rectangle((cx, y, cx + col_widths[idx], y + h), outline=line_color, width=2)
            draw_text_block(draw, value, cx + cell_pad_x, y + cell_pad_y, TABLE_BODY, TEXT, col_widths[idx] - cell_pad_x * 2, 5)
            cx += col_widths[idx]
        y += h
    return y


def build_pdf() -> None:
    pages = []
    page, draw = new_page()
    y = TOP

    def ensure(space: int):
        nonlocal page, draw, y
        if y + space > PAGE_H - BOTTOM:
            pages.append(page)
            page, draw = new_page()
            y = TOP

    ensure(260)
    y = draw_text_block(draw, TITLE_TEXT, MARGIN_X, y, TITLE, TEXT, CONTENT_W, 12)
    y += 18
    y = draw_text_block(draw, LEAD_TEXT, MARGIN_X, y, BODY, TEXT, CONTENT_W, 9)
    y += 18
    draw.line((MARGIN_X, y, PAGE_W - MARGIN_X, y), fill=LINE, width=3)
    y += 26

    ensure(520)
    y = paste_image(page, ASSET_DIR / "01_apple.jpg", MARGIN_X, y, CONTENT_W, 460)
    y += 18

    ensure(360)
    y = draw_text_block(draw, "L0 结论卡", MARGIN_X, y, H2, ACCENT, CONTENT_W, 10)
    y += 12
    y = draw_bullets(draw, L0_BULLETS, MARGIN_X + 4, y, CONTENT_W - 4)

    ensure(880)
    y = draw_text_block(draw, "一、核心对比先看这 6 个维度", MARGIN_X, y, H2, ACCENT, CONTENT_W, 10)
    y += 12
    y = draw_table(draw, MARGIN_X, y, [132, 318, 318, 402], COMPARE_HEADER, COMPARE_ROWS)
    y += 22

    ensure(420)
    y = paste_image(page, ASSET_DIR / "02_huawei.png", MARGIN_X, y, CONTENT_W, 340)
    y += 18

    ensure(700)
    y = draw_text_block(draw, "二、预算怎么分，看这一张表就够了", MARGIN_X, y, H2, ACCENT, CONTENT_W, 10)
    y += 12
    y = draw_table(draw, MARGIN_X, y, [180, 256, 330, 336], BUDGET_HEADER, BUDGET_ROWS)
    y += 22

    ensure(420)
    y = paste_image(page, ASSET_DIR / "03_garmin.jpg", MARGIN_X, y, CONTENT_W, 320)
    y += 18

    ensure(620)
    y = draw_text_block(draw, "三、直接给快速推荐清单", MARGIN_X, y, H2, ACCENT, CONTENT_W, 10)
    y += 10
    y = draw_bullets(draw, SHORTLIST, MARGIN_X + 4, y, CONTENT_W - 4)

    ensure(400)
    y = draw_text_block(draw, "四、最容易买错的 3 种情况", MARGIN_X, y, H2, ACCENT, CONTENT_W, 10)
    y += 10
    y = draw_bullets(draw, MISTAKES, MARGIN_X + 4, y, CONTENT_W - 4)

    ensure(360)
    y = draw_text_block(draw, "五、最终缩圈顺序", MARGIN_X, y, H2, ACCENT, CONTENT_W, 10)
    y += 10
    y = draw_bullets(draw, STEPS, MARGIN_X + 4, y, CONTENT_W - 4)

    ensure(280)
    y = draw_text_block(draw, "资料说明", MARGIN_X, y, H2, ACCENT, CONTENT_W, 10)
    y += 10
    y = draw_text_block(draw, SOURCE_TEXT, MARGIN_X, y, SMALL, MUTED, CONTENT_W, 8)

    pages.append(page)
    rgb_pages = [p.convert("RGB") for p in pages]
    rgb_pages[0].save(PDF_PATH, save_all=True, append_images=rgb_pages[1:], resolution=150.0)
    for idx, img in enumerate(rgb_pages, start=1):
        img.save(OUT_DIR / f"pdf_preview_page_{idx}.jpg", quality=92)
    print(PDF_PATH)


if __name__ == "__main__":
    build_pdf()
