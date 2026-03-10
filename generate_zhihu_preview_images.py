from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


OUT_DIR = Path(r"C:\Users\Roy\Documents\New project\preview_assets\zhihu_20260310")
OUT_DIR.mkdir(parents=True, exist_ok=True)

W, H = 1600, 900
BG = "#F6F1E8"
PAPER = "#FFFDF9"
TEXT = "#1E1E1E"
MUTED = "#5C5C5C"
ACCENT = "#C65D3B"
ACCENT2 = "#1F4E5F"
LINE = "#D8CFC3"
GOOD = "#365E32"
WARN = "#9C3D2E"

FONT = r"C:\Windows\Fonts\msyh.ttc"
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"


def f(size: int, bold: bool = False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


TITLE = f(54, True)
H1 = f(40, True)
H2 = f(30, True)
BODY = f(24, False)
SMALL = f(20, False)
MINI = f(18, False)


def card(draw, box, fill=PAPER, outline=LINE, radius=30):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=3)


def wrap(draw, text: str, font, max_width: int):
    lines = []
    current = ""
    for ch in text:
        test = current + ch
        if draw.textbbox((0, 0), test, font=font)[2] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines


def draw_wrapped(draw, text: str, xy, font, fill, max_width: int, line_gap: int = 10):
    x, y = xy
    lines = []
    for para in text.split("\n"):
        if not para:
            lines.append("")
            continue
        lines.extend(wrap(draw, para, font, max_width))
    cur_y = y
    for line in lines:
        if line == "":
            cur_y += font.size + line_gap
            continue
        draw.text((x, cur_y), line, font=font, fill=fill)
        cur_y += font.size + line_gap
    return cur_y


def badge(draw, xy, text: str, fill, text_fill=PAPER):
    x, y = xy
    w = draw.textbbox((0, 0), text, font=MINI)[2] + 36
    h = 42
    draw.rounded_rectangle((x, y, x + w, y + h), radius=21, fill=fill)
    draw.text((x + 18, y + 9), text, font=MINI, fill=text_fill)
    return x + w


def save(img: Image.Image, name: str):
    img.save(OUT_DIR / name, quality=95)


def build_cover():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    card(d, (60, 60, 1540, 840), fill=PAPER)
    d.rectangle((1040, 120, 1460, 780), fill="#EFE5D7", outline=LINE, width=3)
    d.rounded_rectangle((1120, 220, 1380, 480), radius=130, fill="#2C2C2C")
    d.ellipse((1215, 315, 1285, 385), fill="#D7CFC1")
    d.rectangle((220, 200, 980, 230), fill=ACCENT)
    d.text((220, 270), "扫地机器人别乱买", font=TITLE, fill=TEXT)
    d.text((220, 350), "先看家庭场景，再看机器能力", font=H1, fill=ACCENT2)
    d.text((220, 430), "这不是参数比赛，而是家庭清洁决策。", font=H2, fill=MUTED)
    endx = badge(d, (220, 520), "家庭场景", ACCENT2)
    endx = badge(d, (endx + 16, 520), "维护成本", ACCENT)
    badge(d, (endx + 16, 520), "防缠绕", GOOD)
    d.text((220, 610), "适合知乎长文头图 / 公众号封面内页首图", font=SMALL, fill=MUTED)
    save(img, "01_cover_preview.jpg")


def build_dimensions():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((100, 80), "选购前先看这 4 个判断维度", font=TITLE, fill=TEXT)
    boxes = [
        (100, 190, 760, 430, "面积结构", "你家是小户型、大户型，还是桌椅、地毯、门槛很多的复杂地面？", ACCENT2),
        (840, 190, 1500, 430, "毛发脏污", "有没有宠物、长头发成员、儿童餐椅这些高频脏污来源？", ACCENT),
        (100, 470, 760, 710, "维护意愿", "你愿不愿意自己频繁清主刷、边刷、尘盒和拖布？", GOOD),
        (840, 470, 1500, 710, "长期成本", "除了机身价格，耗材和维护步骤你能不能长期接受？", WARN),
    ]
    for x1, y1, x2, y2, title, body, color in boxes:
        card(d, (x1, y1, x2, y2), fill=PAPER)
        d.rectangle((x1, y1, x2, y1 + 16), fill=color)
        d.text((x1 + 30, y1 + 42), title, font=H1, fill=TEXT)
        draw_wrapped(d, body, (x1 + 30, y1 + 115), BODY, MUTED, x2 - x1 - 60)
    d.text((100, 790), "图注：真正影响体验的，通常不是参数上限，而是这四个判断维度。", font=SMALL, fill=MUTED)
    save(img, "02_four_dimensions.jpg")


def build_compare():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((100, 80), "误区对比：不要只看吸力参数", font=TITLE, fill=TEXT)
    card(d, (100, 180, 730, 760), fill="#FFF4F0")
    d.text((150, 230), "错误看法", font=H1, fill=WARN)
    wrong = ["只看 8000Pa / 12000Pa", "参数越大越好", "宣传页最显眼的就是重点"]
    for i, text in enumerate(wrong):
        d.text((150, 330 + i * 110), f"× {text}", font=H2, fill=TEXT)
    card(d, (870, 180, 1500, 760), fill="#F4FBF8")
    d.text((920, 230), "更稳的判断顺序", font=H1, fill=GOOD)
    right = ["先看导航和覆盖", "再看防缠绕和毛发处理", "最后再看吸力上限"]
    for i, text in enumerate(right):
        d.text((920, 330 + i * 110), f"✓ {text}", font=H2, fill=TEXT)
    d.line((770, 470, 840, 470), fill=ACCENT, width=8)
    d.polygon([(840, 470), (810, 450), (810, 490)], fill=ACCENT)
    d.text((100, 800), "图注：吸力不是不重要，而是不该成为唯一判断标准。", font=SMALL, fill=MUTED)
    save(img, "03_compare_absorption.jpg")


def build_scene_grid():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((100, 80), "先按家庭场景分组，再去看机型", font=TITLE, fill=TEXT)
    scenes = [
        ("小户型 / 租房", "优先看性价比、路径规划、维护简单", ACCENT2),
        ("养宠家庭", "优先看防缠绕、毛发处理、清理频率", ACCENT),
        ("大户型家庭", "优先看续航、回充续扫、路径稳定", GOOD),
        ("有娃家庭", "优先看避障、即时清洁、拖后维护", WARN),
    ]
    coords = [(100, 200, 760, 430), (840, 200, 1500, 430), (100, 500, 760, 730), (840, 500, 1500, 730)]
    for (title, body, color), (x1, y1, x2, y2) in zip(scenes, coords):
        card(d, (x1, y1, x2, y2), fill=PAPER)
        d.rounded_rectangle((x1 + 28, y1 + 24, x1 + 180, y1 + 70), radius=23, fill=color)
        d.text((x1 + 48, y1 + 33), "场景", font=MINI, fill=PAPER)
        d.text((x1 + 28, y1 + 110), title, font=H1, fill=TEXT)
        draw_wrapped(d, body, (x1 + 28, y1 + 190), BODY, MUTED, x2 - x1 - 56)
    d.text((100, 800), "图注：先按家庭场景分组，再去看具体机型，筛选效率会高很多。", font=SMALL, fill=MUTED)
    save(img, "04_scene_grid.jpg")


def build_flow():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((100, 80), "一个够用的选购顺序", font=TITLE, fill=TEXT)
    steps = [
        ("1", "列家庭场景", ACCENT2),
        ("2", "定预算上限", ACCENT),
        ("3", "看导航 / 防缠绕", GOOD),
        ("4", "看维护成本", WARN),
        ("5", "再做型号对比", "#6C5B7B"),
    ]
    start_x = 110
    for idx, (num, label, color) in enumerate(steps):
        x1 = start_x + idx * 290
        card(d, (x1, 300, x1 + 230, 540), fill=PAPER)
        d.ellipse((x1 + 75, 330, x1 + 155, 410), fill=color)
        d.text((x1 + 105, 345), num, font=H1, fill=PAPER)
        draw_wrapped(d, label, (x1 + 28, 445), H2, TEXT, 174)
        if idx < len(steps) - 1:
            d.line((x1 + 230, 420, x1 + 290, 420), fill=LINE, width=8)
            d.polygon([(x1 + 290, 420), (x1 + 264, 404), (x1 + 264, 436)], fill=LINE)
    d.text((100, 650), "图注：如果只记一张图，记这张就够了。", font=SMALL, fill=MUTED)
    save(img, "05_flow_chart.jpg")


def build_pitfall():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((100, 80), "一个常见踩坑场景", font=TITLE, fill=TEXT)
    card(d, (100, 170, 930, 760), fill=PAPER)
    d.rectangle((180, 270, 700, 600), outline=ACCENT2, width=5)
    d.rectangle((260, 300, 620, 430), outline=LINE, width=4)
    d.ellipse((260, 500, 350, 590), outline=LINE, width=4)
    d.ellipse((530, 500, 620, 590), outline=LINE, width=4)
    d.ellipse((390, 560, 490, 660), fill="#2C2C2C")
    d.text((150, 690), "真实图建议：餐桌椅 + 地毯 / 边角 + 机器人本体", font=SMALL, fill=MUTED)
    card(d, (980, 170, 1500, 760), fill="#FFF8F4")
    d.text((1020, 220), "常见问题", font=H1, fill=WARN)
    items = ["餐桌和椅子周围反复漏扫", "毛发缠绕导致清理频率高", "基站维护比想象中更麻烦"]
    for i, text in enumerate(items):
        draw_wrapped(d, f"{i + 1}. {text}", (1020, 320 + i * 130), BODY, TEXT, 420)
    d.text((100, 800), "图注：很多踩坑不是机器绝对不行，而是家庭场景和产品能力没对上。", font=SMALL, fill=MUTED)
    save(img, "06_pitfall_scene.jpg")


def build_summary():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((100, 80), "结尾总结图：收藏时最有用的一张", font=TITLE, fill=TEXT)
    card(d, (100, 180, 1500, 760), fill=PAPER)
    headers = ["家庭场景", "优先看什么", "不要先看什么"]
    col_x = [140, 500, 1050]
    for x, header in zip(col_x, headers):
        d.text((x, 230), header, font=H2, fill=ACCENT2)
    for y in [300, 410, 520, 630]:
        d.line((130, y, 1470, y), fill=LINE, width=3)
    rows = [
        ("小户型 / 租房", "性价比、路径规划、维护简单", "一味追高配"),
        ("养宠家庭", "防缠绕、毛发处理、清理频率", "只看吸力数字"),
        ("大户型家庭", "续航、回充续扫、路径稳定", "只看宣传页参数"),
        ("有娃家庭", "避障、即时清洁、拖后维护", "功能越多越好"),
    ]
    ys = [330, 440, 550, 660]
    widths = [300, 470, 320]
    for y, row in zip(ys, rows):
        for x, text, width in zip(col_x, row, widths):
            draw_wrapped(d, text, (x, y), BODY, TEXT, width)
    d.text((100, 800), "图注：结尾优先放这种能直接复用的总结图，更容易获得收藏。", font=SMALL, fill=MUTED)
    save(img, "07_summary_table.jpg")


def main():
    build_cover()
    build_dimensions()
    build_compare()
    build_scene_grid()
    build_flow()
    build_pitfall()
    build_summary()
    print(OUT_DIR)


if __name__ == "__main__":
    main()
