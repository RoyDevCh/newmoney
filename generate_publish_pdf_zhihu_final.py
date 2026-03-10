from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"C:\Users\Roy\Documents\New project")
OUT_DIR = ROOT / "publish_assets" / "zhihu_final_20260310"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PDF_PATH = OUT_DIR / "zhihu_publish_ready_20260310_final.pdf"

PAGE_W = 1654
PAGE_H = 2339
MARGIN_X = 110
TOP = 110
BOTTOM = 120

BG = "#F7F3EC"
TEXT = "#1F1F1F"
MUTED = "#5E5A55"
ACCENT = "#1F4E5F"
LINE = "#D8CFC3"

FONT = r"C:\Windows\Fonts\msyh.ttc"
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"


def font(size: int, bold: bool = False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


TITLE = font(64, True)
H2 = font(42, True)
BODY = font(28, False)
BODY_BOLD = font(28, True)
SMALL = font(22, False)


BLOCKS = [
    ("title", "别再只看吸力参数买扫地机器人了：普通家庭 2026 选购避坑指南"),
    ("image", str(OUT_DIR / "cover_real_product.jpg"), 760),
    (
        "text",
        "很多人第一次买扫地机器人，做法都差不多：先看排行榜，再看参数表，然后在几个热门型号里反复横跳。"
        "看了半天，最后记住的还是那几个最显眼的词：8000Pa、AI 避障、全自动基站、旗舰款。"
        "\n\n问题在于，这些词并不能直接回答一个最关键的问题：这台机器，到底适不适合你家。"
        "\n\n我把公开评测、长期追评、用户反馈和常见家庭场景整理了一轮之后，结论很明确："
        "对大多数普通家庭来说，真正决定体验的，不是参数上限，而是家庭场景和产品能力有没有对上。"
        "如果顺序错了，预算再高，也一样容易踩坑。",
    ),
    ("heading", "先给结论：普通家庭选扫地机器人，先看这 4 件事"),
    (
        "bullet",
        [
            "你家面积和地面结构是什么样",
            "有没有宠物、长头发成员、儿童餐椅这类高频脏污来源",
            "你愿不愿意自己做日常维护",
            "你是否接受持续性的耗材和维护成本",
        ],
    ),
    ("image", str(ROOT / "preview_assets" / "zhihu_20260310" / "02_four_dimensions.jpg"), 540),
    (
        "text",
        "为什么要先看这四件事？因为它们直接决定了一台机器在你家里会不会频繁出现这些问题："
        "桌椅周围反复漏扫、毛发缠绕导致清理频率过高、扫到一半回充、基站维护麻烦、最后机器没坏但你已经懒得再开它。"
        "\n\n很多所谓的“买错”，并不是机器绝对差，而是选购时先看了参数，后看了场景。",
    ),
    ("heading", "一、最常见的 3 个误区"),
    (
        "text",
        "误区 1：把吸力参数当成核心判断标准。很多商品页喜欢把 8000Pa、10000Pa、12000Pa 这类数字放得很大，给人的感觉是参数越高，清洁效果越强。"
        "但长期公开评测和追评反复说明：在日常硬地板、普通灰尘、头发碎屑这类家庭场景里，决定最终体验的往往不是吸力天花板，而是路径规划、边角覆盖和毛发处理。"
        "\n\n尤其是养宠家庭、长头发家庭、桌椅复杂或边角多的家庭，优先级通常更像这样：防缠绕 > 路径规划 > 日常维护成本 > 吸力数字。",
    ),
    ("image", str(ROOT / "preview_assets" / "zhihu_20260310" / "03_compare_absorption.jpg"), 500),
    (
        "text",
        "误区 2：买的时候只看机身价格，不算长期成本。真正影响长期体验的，往往还有耗材和维护时间成本。"
        "真正让一台机器“闲置”的，未必是它贵，而是它太烦。"
        "\n\n误区 3：希望一台机器解决所有清洁问题。更实际的做法是先明确你最想解决的那个高频问题："
        "是浮灰、宠物毛发、大户型返工，还是拖地维护本身太累。只要主问题定清楚，筛选难度会立刻下降。",
    ),
    ("heading", "二、按家庭场景做第一轮筛选，比直接看型号更重要"),
    ("image", str(ROOT / "preview_assets" / "zhihu_20260310" / "04_scene_grid.jpg"), 620),
    (
        "text",
        "如果你不想一上来就陷进型号海里，最好的办法不是继续刷测评，而是先把自己归到场景里。"
        "\n\n小户型 / 租房：优先看性价比、路径规划、维护简单。"
        "\n养宠家庭：优先看防缠绕、毛发处理、清理频率。"
        "\n大户型家庭：优先看续航、回充续扫、路径规划稳定性。"
        "\n有娃家庭：优先看避障、即时清洁、拖地后的维护便利性。",
    ),
    ("heading", "三、一个够用的筛选顺序"),
    (
        "bullet",
        [
            "第一步：列家庭场景",
            "第二步：定预算上限",
            "第三步：优先看导航和防缠绕",
            "第四步：补看维护和耗材成本",
            "第五步：最后才是型号细比",
        ],
    ),
    ("image", str(ROOT / "preview_assets" / "zhihu_20260310" / "05_flow_chart.jpg"), 460),
    (
        "text",
        "这条顺序最大的价值在于：它可以先帮你排掉一批明显不适合你的产品。"
        "很多时候你真正需要的，不是在 5 台机器里选 1 台，而是先把 5 台里不适合自己的 3 台剔掉。",
    ),
    ("heading", "四、一个很常见的踩坑场景"),
    ("image", str(OUT_DIR / "scene_real_livingroom.jpg"), 560),
    (
        "text",
        "很常见的一种情况是：预算先定在 2500 左右，买的时候重点看了宣传页参数，结果真正用起来才发现："
        "餐桌和椅子周围反复漏扫、毛发缠绕导致清理频率很高、基站维护步骤比预期复杂。"
        "\n\n这类情况为什么会出现？因为前面没有先做“家庭场景筛选”，而是直接拿型号当起点。"
        "如果你在选购前先把家庭面积、毛发情况、维护意愿、长期成本接受度写下来，第一轮其实就能少看掉很多明显不匹配的机型。",
    ),
    ("heading", "五、最后给普通家庭的建议"),
    (
        "bullet",
        [
            "不追最强，只追最适合",
            "不先看参数，先看场景",
            "不只算买入价，也算维护成本",
            "不追功能堆满，先解决最高频问题",
        ],
    ),
    (
        "text",
        "扫地机器人说到底不是“炫配置”的产品，而是一个每天要不要用、值不值得用、能不能坚持用下去的家庭工具。"
        "真正值得买的，不一定是参数最猛的那台，而是那台能在你家里持续减少返工的机器。",
    ),
    ("image", str(ROOT / "preview_assets" / "zhihu_20260310" / "07_summary_table.jpg"), 580),
    (
        "footer",
        "来源说明：本文优先参考公开评测、长期追评、用户反馈和常见家庭使用场景整理而成。",
    ),
]


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
    draw = ImageDraw.Draw(img)
    return img, draw


def draw_text_block(draw, text: str, x: int, y: int, use_font, fill: str, max_width: int, line_gap: int = 12) -> int:
    for line in wrap_text(draw, text, use_font, max_width):
        if line == "":
            y += use_font.size + line_gap
            continue
        draw.text((x, y), line, font=use_font, fill=fill)
        y += use_font.size + line_gap
    return y


def resized_height(path: str, target_width: int) -> int:
    img = Image.open(path)
    w, h = img.size
    scale = target_width / w
    return int(h * scale)


def paste_image(page: Image.Image, path: str, x: int, y: int, target_w: int, target_h: int) -> int:
    img = Image.open(path).convert("RGB")
    img.thumbnail((target_w, target_h))
    bg = Image.new("RGB", (target_w, img.height + 24), "#FFFFFF")
    bg.paste(img, ((target_w - img.width) // 2, 12))
    page.paste(bg, (x, y))
    return y + bg.height


def build_pdf() -> None:
    pages: list[Image.Image] = []
    page, draw = new_page()
    y = TOP
    content_w = PAGE_W - MARGIN_X * 2

    for block_type, payload, *rest in BLOCKS:
        if block_type == "title":
            needed = 200
        elif block_type == "heading":
            needed = 90
        elif block_type == "image":
            needed = int(rest[0]) + 40 if rest else 420
        elif block_type == "bullet":
            needed = 220
        else:
            needed = 260

        if y + needed > PAGE_H - BOTTOM:
            pages.append(page)
            page, draw = new_page()
            y = TOP

        if block_type == "title":
            y = draw_text_block(draw, payload, MARGIN_X, y, TITLE, TEXT, content_w, 16)
            y += 30
            draw.line((MARGIN_X, y, PAGE_W - MARGIN_X, y), fill=LINE, width=3)
            y += 36
        elif block_type == "heading":
            y = draw_text_block(draw, payload, MARGIN_X, y, H2, ACCENT, content_w, 12)
            y += 18
        elif block_type == "text":
            y = draw_text_block(draw, payload, MARGIN_X, y, BODY, TEXT, content_w, 12)
            y += 28
        elif block_type == "bullet":
            items: list[str] = payload
            for item in items:
                y = draw_text_block(draw, f"• {item}", MARGIN_X + 10, y, BODY, TEXT, content_w - 10, 12)
                y += 6
            y += 18
        elif block_type == "image":
            max_h = int(rest[0]) if rest else 520
            y = paste_image(page, payload, MARGIN_X, y, content_w, max_h)
            y += 26
        elif block_type == "footer":
            draw.line((MARGIN_X, y, PAGE_W - MARGIN_X, y), fill=LINE, width=2)
            y += 24
            y = draw_text_block(draw, payload, MARGIN_X, y, SMALL, MUTED, content_w, 10)
            y += 20

    pages.append(page)
    rgb_pages = [p.convert("RGB") for p in pages]
    rgb_pages[0].save(PDF_PATH, save_all=True, append_images=rgb_pages[1:], resolution=150.0)
    for idx, img in enumerate(rgb_pages, start=1):
        img.save(OUT_DIR / f"pdf_preview_page_{idx}.jpg", quality=92)
    print(PDF_PATH)


if __name__ == "__main__":
    build_pdf()
