from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"C:\Users\Roy\Documents\New project")
OUT_DIR = ROOT / "publish_assets" / "zhihu_watch11_v4" / "final"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PDF_PATH = OUT_DIR / "zhihu_watch11_publish_ready_20260310_final_v4.pdf"

PAGE_W = 1654
PAGE_H = 2339
MARGIN_X = 100
TOP = 100
BOTTOM = 120

BG = "#F6F2EA"
TEXT = "#1E1E1E"
MUTED = "#5E5A55"
ACCENT = "#123E52"
LINE = "#D8CFC3"
TABLE_BG = "#FFFFFF"
TABLE_ALT = "#F3F7FA"

FONT = r"C:\Windows\Fonts\msyh.ttc"
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"


def font(size: int, bold: bool = False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


TITLE = font(56, True)
H2 = font(38, True)
BODY = font(26, False)
BODY_BOLD = font(26, True)
SMALL = font(20, False)
TABLE_HEAD = font(22, True)
TABLE_BODY = font(20, False)


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


def paste_image(page: Image.Image, path: str, x: int, y: int, target_w: int, target_h: int) -> int:
    img = Image.open(path).convert("RGB")
    img.thumbnail((target_w, target_h))
    bg = Image.new("RGB", (target_w, img.height + 24), "#FFFFFF")
    bg.paste(img, ((target_w - img.width) // 2, 12))
    page.paste(bg, (x, y))
    return y + bg.height


def draw_bullets(draw, items: list[str], x: int, y: int, width: int) -> int:
    for item in items:
        y = draw_text_block(draw, f"• {item}", x, y, BODY, TEXT, width, 10)
        y += 4
    return y + 10


def draw_table(draw, x: int, y: int, col_widths: list[int], header: list[str], rows: list[list[str]]) -> int:
    table_width = sum(col_widths)
    line_color = "#D7DDE3"
    cell_pad_x = 12
    cell_pad_y = 10

    def row_height(values: list[str], use_font) -> int:
        heights = []
        for value, width in zip(values, col_widths):
            lines = wrap_text(draw, value, use_font, width - cell_pad_x * 2)
            heights.append(max(1, len(lines)) * (use_font.size + 6) + cell_pad_y * 2)
        return max(heights)

    head_h = row_height(header, TABLE_HEAD)
    draw.rectangle((x, y, x + table_width, y + head_h), fill=ACCENT, outline=line_color, width=2)
    cx = x
    for idx, title in enumerate(header):
        draw.rectangle((cx, y, cx + col_widths[idx], y + head_h), outline=line_color, width=2)
        draw_text_block(draw, title, cx + cell_pad_x, y + cell_pad_y, TABLE_HEAD, "#FFFFFF", col_widths[idx] - cell_pad_x * 2, 6)
        cx += col_widths[idx]
    y += head_h
    for ridx, row in enumerate(rows):
        h = row_height(row, TABLE_BODY)
        fill = TABLE_BG if ridx % 2 == 0 else TABLE_ALT
        draw.rectangle((x, y, x + table_width, y + h), fill=fill, outline=line_color, width=2)
        cx = x
        for idx, value in enumerate(row):
            draw.rectangle((cx, y, cx + col_widths[idx], y + h), outline=line_color, width=2)
            draw_text_block(draw, value, cx + cell_pad_x, y + cell_pad_y, TABLE_BODY, TEXT, col_widths[idx] - cell_pad_x * 2, 6)
            cx += col_widths[idx]
        y += h
    return y


TITLE_TEXT = "Apple Watch Series 11 值不值得买？先别急着看热词，这张 6 维度对比表比发布会摘要更有用"

L0_TEXT = (
    "一句话判词：如果你是深度 iPhone 用户，想要一块长期佩戴、联动顺、健康记录完整的主力表，"
    "Series 11 依然值得重点看；但如果你手上已经是近一代常规款，而且当前没有明显痛点，"
    "这一代更像继续打磨主力体验，而不是必须立刻换的升级。"
)

L0_BULLETS = [
    "更适合：iPhone 主力用户、第一次买 Apple Watch 的用户、老设备换新的人、看重日常佩戴与健康记录的人。",
    "不太适合：近一代常规款用户、非 iPhone 用户、强训练或户外导向用户、纯价格敏感用户。",
    "风险提示：这篇能下的是购买方向结论，不是长期深测终局结论。",
]

DIM_HEADER = ["评测维度", "你真正该看什么", "为什么重要"]
DIM_ROWS = [
    ["健康功能", "新增了什么、补强了什么、哪些真的会长期用", "功能不是越多越值钱，而是会不会进入你的日常"],
    ["运动 / GPS", "跑步、健身、定位、路线记录够不够用", "决定它更像日常表还是训练表"],
    ["外观与材质", "表壳材质、边框、重量、厚度、耐用性", "很多人弃戴，问题不在功能，而在佩戴和质感"],
    ["续航与充电节奏", "一天一充是否打断习惯，快充是否够省心", "续航本质上是佩戴连续性问题"],
    ["系统生态与联动", "和 iPhone、AirPods、支付、健康数据配合顺不顺", "Apple Watch 的核心优势本来就不只是一块表"],
    ["佩戴舒适度", "尺寸、厚度、重量、表带适配度", "决定你会不会真的每天戴"],
]

MATRIX_HEADER = ["维度", "Series 11 当前判断", "上代 / 同类对比", "结论等级"]
MATRIX_ROWS = [
    ["健康功能", "仍是核心卖点之一，方向上继续强化健康记录完整性", "和上一代比先看真实增量；和华为比看健康+续航平衡", "高概率成立"],
    ["运动 / GPS", "对通勤 + 健身 + 轻中度跑步用户大概率够用", "和上一代比看记录稳定性；和 Garmin 比训练路线不是同定位", "高概率成立"],
    ["外观与材质", "仍走主力款完成度路线，重点在细节和佩戴感", "和上一代比看材质、边框、厚度、重量；同价位比看整体完成度", "待长期验证"],
    ["续航与充电", "价值不在纸面数字，而在会不会更少打断佩戴习惯", "和上一代比看充电节奏；和华为比苹果通常不靠续航取胜", "待长期验证"],
    ["生态联动", "仍然是最强护城河之一", "和上一代比重点是是不是更顺；对 iPhone 用户仍很难被替代", "已确认"],
    ["佩戴舒适度", "依然是主力款判断的关键维度之一", "和上一代比看尺寸重量；和 Ultra 3 比更适合多数日常佩戴用户", "待长期验证"],
]

PAGE2_TEXT = (
    "专业单品稿真正该讲的，不是“有没有新词”，而是哪些变化真的会影响购买价值。"
    "\n\n和上一代比，Series 11 最值得看的有 4 件事："
)

PAGE2_BULLETS = [
    "健康功能：看是否带来长期价值，而不是发布期词汇增多。",
    "外观与材质：看表壳材质、边框、厚度、重量和耐用性有没有体感差异。",
    "续航与充电节奏：看是否更少打断全天佩戴和睡眠记录。",
    "佩戴舒适度：看它到底是不是一块能每天戴的主力表。",
]

COMPARE_TEXT = (
    "同品类比较里，SE 3 更像苹果生态的入门口，Ultra 3 更偏高预算、户外和训练场景；"
    "华为 WATCH 系列更容易在续航、安卓兼容和通勤均衡上形成竞争力；"
    "Garmin Forerunner 则更偏训练、路线和恢复体系。"
    "\n\n所以真正的问题不是谁更强，而是谁更像你的主需求。"
)

AUDIENCE_HEADER = ["用户类型", "更推荐看什么", "为什么"]
AUDIENCE_ROWS = [
    ["iPhone 新用户", "Series 11 / SE 3", "先决定你要入门还是直接上主力款"],
    ["旧款用户准备换机", "Series 11", "更值得看整体完成度，而不是只看功能表"],
    ["高预算户外 / 训练用户", "Ultra 3 / Garmin", "这类需求本身就不是 Series 11 的主战场"],
    ["安卓用户", "华为 WATCH / Garmin", "Apple Watch 的生态价值在这里很难完全成立"],
]

APPENDIX_TEXT = (
    "证据口径：事实账本=Apple 官方发布信息、官方产品页、官方支持页面；"
    "方法账本=媒体上手与公开评测中的测试条件和长期使用反馈；"
    "信号账本=社区反馈，只作为“继续观察的点”，不直接当硬结论。"
    "\n\n当前能下的结论：Series 11 依然是苹果生态里最值得重点看的主力均衡款之一；"
    "它最强的价值仍然是生态联动、日用完成度和长期佩戴属性。"
    "\n\n当前还不能下死结论的部分：和上一代相比，健康、续航、佩戴体感到底有多大升级；"
    "外观材质的细节变化是否足以支撑老用户换机；长期反馈能否稳定支撑“升级值得”的判断。"
)


def build_pdf() -> None:
    pages: list[Image.Image] = []
    page, draw = new_page()
    y = TOP
    content_w = PAGE_W - MARGIN_X * 2

    def ensure(space: int):
        nonlocal page, draw, y
        if y + space > PAGE_H - BOTTOM:
            pages.append(page)
            page, draw = new_page()
            y = TOP

    ensure(240)
    y = draw_text_block(draw, TITLE_TEXT, MARGIN_X, y, TITLE, TEXT, content_w, 14)
    y += 24
    draw.line((MARGIN_X, y, PAGE_W - MARGIN_X, y), fill=LINE, width=3)
    y += 30

    ensure(780)
    y = paste_image(page, str(ROOT / "publish_assets" / "zhihu_watch11_v2" / "01_official.jpg"), MARGIN_X, y, content_w, 760)
    y += 24

    ensure(320)
    y = draw_text_block(draw, "L0 结论卡", MARGIN_X, y, H2, ACCENT, content_w, 10)
    y += 12
    y = draw_text_block(draw, L0_TEXT, MARGIN_X, y, BODY, TEXT, content_w, 10)
    y += 16
    y = draw_bullets(draw, L0_BULLETS, MARGIN_X + 6, y, content_w - 6)

    ensure(900)
    y = draw_text_block(draw, "一、先把该比什么立起来", MARGIN_X, y, H2, ACCENT, content_w, 10)
    y += 14
    y = draw_table(draw, MARGIN_X, y, [170, 420, 764], DIM_HEADER, DIM_ROWS)
    y += 24

    ensure(1100)
    y = draw_text_block(draw, "二、L1 可比矩阵", MARGIN_X, y, H2, ACCENT, content_w, 10)
    y += 14
    y = draw_table(draw, MARGIN_X, y, [150, 360, 520, 224], MATRIX_HEADER, MATRIX_ROWS)
    y += 24

    ensure(700)
    y = paste_image(page, str(ROOT / "publish_assets" / "zhihu_watch11_v2" / "02_official.jpg"), MARGIN_X, y, content_w, 620)
    y += 24

    ensure(500)
    y = draw_text_block(draw, "三、和上一代比，真正该看的 4 件事", MARGIN_X, y, H2, ACCENT, content_w, 10)
    y += 12
    y = draw_text_block(draw, PAGE2_TEXT, MARGIN_X, y, BODY, TEXT, content_w, 10)
    y += 10
    y = draw_bullets(draw, PAGE2_BULLETS, MARGIN_X + 6, y, content_w - 6)

    ensure(520)
    y = draw_text_block(draw, "四、和同品类比，Series 11 站在哪一档", MARGIN_X, y, H2, ACCENT, content_w, 10)
    y += 12
    y = draw_text_block(draw, COMPARE_TEXT, MARGIN_X, y, BODY, TEXT, content_w, 10)
    y += 20
    y = draw_table(draw, MARGIN_X, y, [210, 320, 514], AUDIENCE_HEADER, AUDIENCE_ROWS)
    y += 24

    ensure(620)
    y = paste_image(page, str(ROOT / "publish_assets" / "zhihu_watch11_v2" / "03_official.jpg"), MARGIN_X, y, content_w, 560)
    y += 24

    ensure(560)
    y = draw_text_block(draw, "五、L2 证据与方法附录", MARGIN_X, y, H2, ACCENT, content_w, 10)
    y += 12
    y = draw_text_block(draw, APPENDIX_TEXT, MARGIN_X, y, BODY, TEXT, content_w, 10)
    y += 22
    draw.line((MARGIN_X, y, PAGE_W - MARGIN_X, y), fill=LINE, width=2)
    y += 22
    y = draw_text_block(
        draw,
        "来源说明：本文优先参考 Apple 官方发布信息、官方产品页、首批媒体上手与公开评测摘要；图像素材仅使用 Apple 官方无水印图片。",
        MARGIN_X,
        y,
        SMALL,
        MUTED,
        content_w,
        8,
    )

    pages.append(page)
    rgb_pages = [p.convert("RGB") for p in pages]
    rgb_pages[0].save(PDF_PATH, save_all=True, append_images=rgb_pages[1:], resolution=150.0)
    for idx, img in enumerate(rgb_pages, start=1):
        img.save(OUT_DIR / f"pdf_preview_page_{idx}.jpg", quality=92)
    print(PDF_PATH)


if __name__ == "__main__":
    build_pdf()
