from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"C:\Users\Roy\Documents\New project")
OUT_DIR = ROOT / "publish_assets" / "zhihu_watch11_v2" / "final"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PDF_PATH = OUT_DIR / "zhihu_watch11_publish_ready_20260310_final.pdf"

PAGE_W = 1654
PAGE_H = 2339
MARGIN_X = 110
TOP = 110
BOTTOM = 120

BG = "#F7F3EC"
TEXT = "#1F1F1F"
MUTED = "#5E5A55"
ACCENT = "#123E52"
LINE = "#D8CFC3"

FONT = r"C:\Windows\Fonts\msyh.ttc"
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"


def font(size: int, bold: bool = False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


TITLE = font(60, True)
H2 = font(40, True)
BODY = font(28, False)
SMALL = font(22, False)


BLOCKS = [
    ("title", "Apple Watch Series 11 值不值得买？我把官方信息、媒体上手和首批反馈梳理后，结论是这三句"),
    ("image", str(ROOT / "publish_assets" / "zhihu_watch11_v2" / "01_official.jpg"), 760),
    (
        "text",
        "先给结论：如果你本来就在 iPhone 生态里，Apple Watch Series 11 依然是最稳的主力款之一。"
        "如果你现在用的是近两代 Apple Watch，而且没有明显痛点，这一代未必值得第一时间换。"
        "如果你买表最看重的是“戴上就省心、联动顺、记录完整”，Series 11 值得重点看；"
        "如果你更看重极限运动、超长续航或纯性价比，那它不一定是你的最优解。"
        "\n\n这篇不是个人长期深测后的终局评测，而是一篇更适合知乎搜索场景的首轮判断稿。"
        "证据口径主要来自 Apple 官方发布信息与产品页、首批媒体上手与公开评测，以及公开用户反馈里已经出现的共性判断。"
    ),
    ("heading", "一、先说最关键的：Series 11 更像“把成熟体验继续拉顺”"),
    (
        "text",
        "很多人看新品，第一反应是找“有没有革命性升级”。"
        "但 Apple Watch 这类产品，真正影响长期体验的，往往不是单个参数爆点，而是你会不会更愿意每天戴、每天用、每天不折腾。"
        "\n\n从目前公开信息看，Series 11 这代最重要的价值，仍然集中在三件事："
        "\n1. 苹果生态里的联动完整性"
        "\n2. 日常佩戴和健康记录的连续性"
        "\n3. 对大多数普通用户来说足够均衡，而不是只在某个点上特别激进"
    ),
    ("heading", "二、哪些判断现在已经可以说得比较稳"),
    (
        "bullet",
        [
            "它依然最适合深度 iPhone 用户。",
            "它对新用户和老旧设备用户更友好。",
            "它不是给所有人准备的，尤其不适合非 iPhone 用户、极度在意长续航的人、训练导向用户和纯价格敏感用户。",
        ],
    ),
    ("image", str(ROOT / "publish_assets" / "zhihu_watch11_v2" / "02_official.jpg"), 620),
    ("heading", "三、宣传点和实料要分开看"),
    (
        "text",
        "很多稿子会把发布会讲法、媒体标题和真实购买建议混在一起，最后看起来信息很多，实际上没有完成判断。"
        "\n\n这篇更建议你按三层来理解："
        "\n- 已确认：官方定位、苹果生态联动、Series 11 仍是主力均衡款。"
        "\n- 高概率成立：媒体普遍会把“整体体验继续变顺”当成重点。"
        "\n- 仍待验证：续航在高频真实场景里的稳定性、近两代老用户的升级感、它与 SE 和 Ultra 相比的长期价值平衡。"
    ),
    ("heading", "四、适合谁，不适合谁"),
    (
        "bullet",
        [
            "更适合：深度 iPhone 用户、第一次买 Apple Watch 的人、老旧设备用户、看重日常佩戴体验和系统完整性的人。",
            "不太适合：近两代 Apple Watch 用户、非 iPhone 用户、训练或极限户外导向用户、纯价格敏感用户。",
        ],
    ),
    ("heading", "五、现在买，还是等等？"),
    (
        "text",
        "我的判断是：新用户、老旧款用户可以直接进入重点候选名单；近两代用户先别急着冲，除非你很明确地在等这代解决你的痛点。"
        "\n\n这类产品最怕的不是“买贵”，而是你为一堆边际升级多花了钱，但日常体感并没有同步变强。"
    ),
    ("image", str(ROOT / "publish_assets" / "zhihu_watch11_v2" / "03_official.jpg"), 560),
    ("heading", "六、哪些地方我建议继续观察"),
    (
        "bullet",
        [
            "长时间、高频真实场景下的续航稳定性。",
            "普通用户对佩戴舒适度和日常稳定性的持续反馈。",
            "近两代老用户对升级感的真实评价。",
            "它和 SE、Ultra 两端定位产品相比，价格与价值平衡点是否最优。",
        ],
    ),
    ("heading", "最终结论"),
    (
        "text",
        "Apple Watch Series 11 不是那种一看发布会就能让所有老用户立刻心动的产品。"
        "但它很可能仍然是苹果生态里最稳、最完整、最适合大多数人的主力款之一。"
        "\n\n如果你是苹果生态新用户，或者你手上的旧表已经到了该换的时候，它值得认真看。"
        "如果你已经在用近代产品，而且当前体验并不差，那更建议你先等等，把注意力放到长期体验反馈上。"
    ),
    (
        "footer",
        "来源说明：本文优先参考 Apple 官方发布信息、官方产品页、首批媒体上手与公开评测摘要；图像素材仅使用 Apple 官方无水印图片。",
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
            needed = 80
        elif block_type == "image":
            needed = int(rest[0]) + 50 if rest else 500
        elif block_type == "bullet":
            needed = 240
        else:
            needed = 260

        if y + needed > PAGE_H - BOTTOM:
            pages.append(page)
            page, draw = new_page()
            y = TOP

        if block_type == "title":
            y = draw_text_block(draw, payload, MARGIN_X, y, TITLE, TEXT, content_w, 16)
            y += 28
            draw.line((MARGIN_X, y, PAGE_W - MARGIN_X, y), fill=LINE, width=3)
            y += 34
        elif block_type == "heading":
            y = draw_text_block(draw, payload, MARGIN_X, y, H2, ACCENT, content_w, 12)
            y += 16
        elif block_type == "text":
            y = draw_text_block(draw, payload, MARGIN_X, y, BODY, TEXT, content_w, 12)
            y += 24
        elif block_type == "bullet":
            items: list[str] = payload
            for item in items:
                y = draw_text_block(draw, f"• {item}", MARGIN_X + 6, y, BODY, TEXT, content_w - 6, 12)
                y += 6
            y += 16
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
