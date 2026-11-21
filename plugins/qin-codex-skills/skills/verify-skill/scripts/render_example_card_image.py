import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


CARD_WIDTH = 2400
CARD_OUTER_MARGIN = 18
CARD_INNER_MARGIN = 16
CARD_SECTION_GAP = 10
CARD_HEADER_HEIGHT = 72
CARD_LABEL_FONT_SIZE = 18
CARD_BODY_FONT_SIZE = 14
CARD_TITLE_FONT_SIZE = 24
CARD_LABEL_LINE_HEIGHT = 24
CARD_BODY_LINE_HEIGHT = 19
CARD_SECTION_SIDE_MARGIN = 36
CARD_THUMBNAIL_MAX_HEIGHT = 220
CARD_THUMBNAIL_MAX_WIDTH = 260


def _load_font(size):
    try:
        return ImageFont.truetype("/System/Library/Fonts/Supplemental/Menlo.ttc", size)
    except Exception:
        return ImageFont.load_default()


def _text_width(draw, text, font): return draw.textbbox((0, 0), text, font=font)[2]


def _wrap_line(draw, text, font, max_width):
    if not text: return [""]
    wrapped_lines = []
    current_text = ""
    for token in text.split(" "):
        candidate_text = f"{current_text} {token}".strip()
        if current_text and _text_width(draw, candidate_text, font) <= max_width:
            current_text = candidate_text
            continue
        if current_text:
            wrapped_lines.append(current_text)
            current_text = ""
        if _text_width(draw, token, font) <= max_width:
            current_text = token
            continue
        long_token = ""
        for character in token:
            candidate_token = f"{long_token}{character}"
            if long_token and _text_width(draw, candidate_token, font) > max_width:
                wrapped_lines.append(long_token)
                long_token = character
                continue
            long_token = candidate_token
        current_text = long_token
    if current_text: wrapped_lines.append(current_text)
    return wrapped_lines or [""]


def _wrap_sections(draw, text, font, max_width):
    lines = []
    for segment in (part.strip() for part in text.split(" | ") if part.strip()):
        lines.extend(_wrap_line(draw, segment, font, max_width))
    return lines or [""]


def _section_height(body_height): return CARD_INNER_MARGIN * 2 + CARD_LABEL_LINE_HEIGHT + body_height


def _load_thumbnail(image_path):
    if not image_path:
        return None
    source = Image.open(Path(image_path).expanduser().resolve())
    source = source.convert("RGB")
    source.thumbnail((CARD_THUMBNAIL_MAX_WIDTH, CARD_THUMBNAIL_MAX_HEIGHT), Image.Resampling.LANCZOS)
    return source


def main():
    parser = argparse.ArgumentParser(description="Render a compact function/input/output evidence image.")
    parser.add_argument("--output", required=True, help="PNG path to write.")
    parser.add_argument("--title", default="Real API Example", help="Card title.")
    parser.add_argument("--function-name", required=True, help="Function or entry-point name.")
    parser.add_argument("--input-text", required=True, help="Input text to show.")
    parser.add_argument("--input-image-path", help="Optional image to embed inside the input section.")
    parser.add_argument("--output-text", required=True, help="Output text to show.")
    args = parser.parse_args()

    title_font = _load_font(CARD_TITLE_FONT_SIZE)
    label_font = _load_font(CARD_LABEL_FONT_SIZE)
    body_font = _load_font(CARD_BODY_FONT_SIZE)
    probe_image = Image.new("RGB", (CARD_WIDTH, 100), "#ffffff")
    probe_draw = ImageDraw.Draw(probe_image)
    section_width = CARD_WIDTH - (CARD_OUTER_MARGIN * 2) - (CARD_SECTION_SIDE_MARGIN * 2)
    section_content_width = section_width - (CARD_INNER_MARGIN * 2)
    function_lines = _wrap_line(probe_draw, args.function_name, body_font, section_content_width)
    input_thumbnail = _load_thumbnail(args.input_image_path)
    input_text_width = section_content_width
    if input_thumbnail:
        input_text_width -= input_thumbnail.width + CARD_SECTION_GAP
    input_lines = _wrap_sections(probe_draw, args.input_text, body_font, input_text_width)
    output_lines = _wrap_sections(probe_draw, args.output_text, body_font, section_content_width)
    function_body_height = max(len(function_lines) * CARD_BODY_LINE_HEIGHT, CARD_BODY_LINE_HEIGHT)
    input_text_height = max(len(input_lines) * CARD_BODY_LINE_HEIGHT, CARD_BODY_LINE_HEIGHT)
    input_body_height = input_text_height
    if input_thumbnail:
        input_body_height = max(input_body_height, input_thumbnail.height)
    output_body_height = max(len(output_lines) * CARD_BODY_LINE_HEIGHT, CARD_BODY_LINE_HEIGHT)
    function_height = _section_height(function_body_height)
    input_height = _section_height(input_body_height)
    output_height = _section_height(output_body_height)
    image_height = CARD_OUTER_MARGIN * 2 + CARD_HEADER_HEIGHT + function_height + input_height + output_height + CARD_SECTION_GAP * 4

    image = Image.new("RGB", (CARD_WIDTH, image_height), "#f8fafc")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((CARD_OUTER_MARGIN, CARD_OUTER_MARGIN, CARD_WIDTH - CARD_OUTER_MARGIN, image_height - CARD_OUTER_MARGIN), radius=24, fill="#ffffff", outline="#d0d5dd", width=3)
    draw.rounded_rectangle((CARD_OUTER_MARGIN + 16, CARD_OUTER_MARGIN + 16, CARD_WIDTH - CARD_OUTER_MARGIN - 16, CARD_OUTER_MARGIN + 16 + CARD_HEADER_HEIGHT), radius=18, fill="#111827")
    draw.text((CARD_OUTER_MARGIN + 46, CARD_OUTER_MARGIN + 42), args.title, fill="#f9fafb", font=title_font)

    current_top = CARD_OUTER_MARGIN + 16 + CARD_HEADER_HEIGHT + CARD_SECTION_GAP
    for section_label, section_lines, section_height, background_color in [
        ("Function", function_lines, function_height, "#e0e7ff"),
        ("Input", input_lines, input_height, "#eff6ff"),
        ("Output", output_lines, output_height, "#f8fafc"),
    ]:
        left = CARD_OUTER_MARGIN + CARD_SECTION_SIDE_MARGIN
        top = current_top
        right = CARD_WIDTH - CARD_OUTER_MARGIN - CARD_SECTION_SIDE_MARGIN
        bottom = current_top + section_height
        draw.rounded_rectangle((left, top, right, bottom), radius=16, fill=background_color, outline="#d0d5dd", width=2)
        draw.text((left + CARD_INNER_MARGIN, top + CARD_INNER_MARGIN), section_label, fill="#0f172a", font=label_font)
        body_top = top + CARD_INNER_MARGIN + CARD_LABEL_LINE_HEIGHT
        body_height = section_height - CARD_INNER_MARGIN * 2 - CARD_LABEL_LINE_HEIGHT
        text_height = max(len(section_lines) * CARD_BODY_LINE_HEIGHT, CARD_BODY_LINE_HEIGHT)
        text_top = int(body_top + max(0, body_height - text_height) / 2)
        text_left = left + CARD_INNER_MARGIN
        if section_label == "Input" and input_thumbnail:
            thumbnail_left = right - CARD_INNER_MARGIN - input_thumbnail.width
            thumbnail_top = int(body_top + max(0, body_height - input_thumbnail.height) / 2)
            image.paste(input_thumbnail, (thumbnail_left, thumbnail_top))
        for line in section_lines:
            draw.text((text_left, text_top), line, fill="#111827", font=body_font)
            text_top += CARD_BODY_LINE_HEIGHT
        current_top = bottom + CARD_SECTION_GAP

    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
    print(output_path)


if __name__ == "__main__": main()
