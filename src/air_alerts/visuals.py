"""Small dependency-free SVG and PNG chart helpers."""

from __future__ import annotations

from html import escape
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


PALETTE = ["#2563eb", "#dc2626", "#059669", "#7c3aed", "#ea580c"]
TEXT = "#111827"
MUTED = "#6b7280"
GRID = "#e5e7eb"
FILL = "#eff6ff"


def bar_chart_svg(
    data: pd.DataFrame,
    *,
    label_col: str,
    value_col: str,
    title: str,
    width: int = 920,
    height: int = 440,
    top_n: int = 12,
    suffix: str = "h",
) -> str:
    rows = data.head(top_n).copy()
    if rows.empty:
        return _empty_svg(title, width, height)

    margin_left, margin_right, margin_top, margin_bottom = 190, 34, 58, 34
    plot_w = width - margin_left - margin_right
    bar_h = max(16, int((height - margin_top - margin_bottom) / max(len(rows), 1)) - 8)
    max_value = max(float(rows[value_col].max()), 1.0)
    parts = [_svg_open(width, height), _svg_text(24, 32, title, size=20, weight=700)]
    for i, row in enumerate(rows.itertuples(index=False)):
        label = str(getattr(row, label_col))
        value = float(getattr(row, value_col))
        y = margin_top + i * (bar_h + 8)
        w = max(1, value / max_value * plot_w)
        parts.append(f'<text x="18" y="{y + bar_h - 3}" font-size="13" fill="{TEXT}">{escape(label)}</text>')
        parts.append(
            f'<rect x="{margin_left}" y="{y}" width="{w:.1f}" height="{bar_h}" rx="3" fill="{PALETTE[0]}"></rect>'
        )
        parts.append(
            f'<text x="{margin_left + w + 8:.1f}" y="{y + bar_h - 3}" font-size="13" fill="{MUTED}">'
            f"{value:.1f}{suffix}</text>"
        )
    parts.append("</svg>")
    return "\n".join(parts)


def line_chart_svg(
    data: pd.DataFrame,
    *,
    title: str,
    y_col: str,
    width: int = 920,
    height: int = 430,
) -> str:
    if data.empty:
        return _empty_svg(title, width, height)

    frame = data.copy()
    frame["date_dt"] = pd.to_datetime(frame["date"])
    margin_left, margin_right, margin_top, margin_bottom = 58, 154, 58, 44
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom
    min_date = frame["date_dt"].min()
    max_date = frame["date_dt"].max()
    date_span = max((max_date - min_date).days, 1)
    max_value = max(float(frame[y_col].max()), 1.0)

    parts = [_svg_open(width, height), _svg_text(24, 32, title, size=20, weight=700)]
    parts.append(f'<line x1="{margin_left}" y1="{margin_top + plot_h}" x2="{margin_left + plot_w}" y2="{margin_top + plot_h}" stroke="{GRID}"/>')
    parts.append(f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + plot_h}" stroke="{GRID}"/>')

    for idx, (oblast, group) in enumerate(frame.groupby("oblast", sort=False)):
        points = []
        for row in group.itertuples(index=False):
            x = margin_left + ((row.date_dt - min_date).days / date_span) * plot_w
            y = margin_top + plot_h - (float(getattr(row, y_col)) / max_value) * plot_h
            points.append(f"{x:.1f},{y:.1f}")
        color = PALETTE[idx % len(PALETTE)]
        parts.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" stroke-width="2.4"/>')
        legend_y = margin_top + idx * 24
        parts.append(f'<rect x="{width - margin_right + 18}" y="{legend_y - 10}" width="12" height="12" fill="{color}"/>')
        parts.append(f'<text x="{width - margin_right + 36}" y="{legend_y}" font-size="13" fill="{TEXT}">{escape(str(oblast))}</text>')

    parts.append(_svg_text(margin_left, height - 16, min_date.date().isoformat(), size=12, fill=MUTED))
    parts.append(_svg_text(margin_left + plot_w - 78, height - 16, max_date.date().isoformat(), size=12, fill=MUTED))
    parts.append(_svg_text(margin_left + 4, margin_top + 14, f"max {max_value:.1f}h", size=12, fill=MUTED))
    parts.append("</svg>")
    return "\n".join(parts)


def heatmap_svg(corr: pd.DataFrame, *, title: str, width: int = 700, height: int = 520) -> str:
    if corr.empty:
        return _empty_svg(title, width, height)

    labels = list(corr.index)
    cell = min(64, int((height - 145) / max(len(labels), 1)))
    left, top = 170, 72
    parts = [_svg_open(width, height), _svg_text(24, 32, title, size=20, weight=700)]
    for i, row_label in enumerate(labels):
        parts.append(_svg_text(18, top + i * cell + cell * 0.62, row_label, size=12))
        parts.append(_svg_text(left + i * cell, top - 12, row_label.replace(" oblast", ""), size=11, fill=MUTED, rotate=-35))
        for j, col_label in enumerate(labels):
            value = float(corr.loc[row_label, col_label])
            color = _corr_color(value)
            x = left + j * cell
            y = top + i * cell
            parts.append(f'<rect x="{x}" y="{y}" width="{cell - 2}" height="{cell - 2}" fill="{color}" rx="3"/>')
            parts.append(_svg_text(x + 11, y + cell * 0.6, f"{value:.2f}", size=12, fill="#0f172a"))
    parts.append(_svg_text(24, height - 24, "Daily alert-hour correlation in the selected window.", size=12, fill=MUTED))
    parts.append("</svg>")
    return "\n".join(parts)


def write_bar_png(data: pd.DataFrame, path: Path, *, label_col: str, value_col: str, title: str, top_n: int = 10) -> Path:
    rows = data.head(top_n).copy()
    image = Image.new("RGB", (1200, 700), "white")
    draw = ImageDraw.Draw(image)
    font_title = _font(34, bold=True)
    font = _font(22)
    small = _font(18)
    draw.text((42, 28), title, fill=TEXT, font=font_title)
    if rows.empty:
        draw.text((42, 120), "No data available.", fill=MUTED, font=font)
    else:
        max_value = max(float(rows[value_col].max()), 1.0)
        y = 100
        for row in rows.itertuples(index=False):
            label = str(getattr(row, label_col))
            value = float(getattr(row, value_col))
            bar_w = int(value / max_value * 730)
            draw.text((42, y + 8), label, fill=TEXT, font=small)
            draw.rounded_rectangle((330, y, 330 + bar_w, y + 30), radius=5, fill=PALETTE[0])
            draw.text((342 + bar_w, y + 4), f"{value:.1f}h", fill=MUTED, font=small)
            y += 52
    _save_png(image, path)
    return path


def write_line_png(data: pd.DataFrame, path: Path, *, title: str, y_col: str) -> Path:
    image = Image.new("RGB", (1200, 680), "white")
    draw = ImageDraw.Draw(image)
    draw.text((42, 28), title, fill=TEXT, font=_font(34, bold=True))
    if data.empty:
        draw.text((42, 120), "No data available.", fill=MUTED, font=_font(22))
        _save_png(image, path)
        return path

    frame = data.copy()
    frame["date_dt"] = pd.to_datetime(frame["date"])
    left, top, right, bottom = 80, 110, 970, 570
    draw.line((left, bottom, right, bottom), fill=GRID, width=2)
    draw.line((left, top, left, bottom), fill=GRID, width=2)
    min_date = frame["date_dt"].min()
    max_date = frame["date_dt"].max()
    date_span = max((max_date - min_date).days, 1)
    max_value = max(float(frame[y_col].max()), 1.0)
    for idx, (oblast, group) in enumerate(frame.groupby("oblast", sort=False)):
        color = PALETTE[idx % len(PALETTE)]
        points = []
        for row in group.itertuples(index=False):
            x = left + ((row.date_dt - min_date).days / date_span) * (right - left)
            y = bottom - (float(getattr(row, y_col)) / max_value) * (bottom - top)
            points.append((x, y))
        if len(points) > 1:
            draw.line(points, fill=color, width=4)
        legend_y = top + idx * 34
        draw.rectangle((1010, legend_y, 1030, legend_y + 20), fill=color)
        draw.text((1040, legend_y - 2), str(oblast), fill=TEXT, font=_font(18))
    draw.text((left, 594), min_date.date().isoformat(), fill=MUTED, font=_font(16))
    draw.text((right - 96, 594), max_date.date().isoformat(), fill=MUTED, font=_font(16))
    _save_png(image, path)
    return path


def write_heatmap_png(corr: pd.DataFrame, path: Path, *, title: str) -> Path:
    image = Image.new("RGB", (1000, 760), "white")
    draw = ImageDraw.Draw(image)
    draw.text((42, 28), title, fill=TEXT, font=_font(32, bold=True))
    if corr.empty:
        draw.text((42, 120), "No data available.", fill=MUTED, font=_font(22))
        _save_png(image, path)
        return path

    labels = list(corr.index)
    cell = 86
    left, top = 300, 150
    for i, row_label in enumerate(labels):
        draw.text((42, top + i * cell + 25), row_label, fill=TEXT, font=_font(17))
        draw.text((left + i * cell, 100), row_label.replace(" oblast", ""), fill=MUTED, font=_font(15))
        for j, col_label in enumerate(labels):
            value = float(corr.loc[row_label, col_label])
            x, y = left + j * cell, top + i * cell
            draw.rounded_rectangle((x, y, x + cell - 6, y + cell - 6), radius=6, fill=_corr_color(value))
            draw.text((x + 18, y + 28), f"{value:.2f}", fill=TEXT, font=_font(16))
    _save_png(image, path)
    return path


def write_pipeline_png(path: Path) -> Path:
    image = Image.new("RGB", (1200, 360), "white")
    draw = ImageDraw.Draw(image)
    draw.text((42, 28), "Reproducible analysis pipeline", fill=TEXT, font=_font(34, bold=True))
    boxes = [
        ("Public CSV", "Vadimkin official data"),
        ("Normalize", "UTC -> Europe/Kyiv"),
        ("Union", "oblast interval overlaps"),
        ("Metrics", "duration, night, rolling"),
        ("Artifacts", "HTML, DOCX, README"),
    ]
    x = 52
    for i, (head, body) in enumerate(boxes):
        draw.rounded_rectangle((x, 130, x + 190, 250), radius=14, fill="#f8fafc", outline="#cbd5e1", width=2)
        draw.text((x + 18, 152), head, fill=TEXT, font=_font(22, bold=True))
        draw.text((x + 18, 190), body, fill=MUTED, font=_font(16))
        if i < len(boxes) - 1:
            draw.line((x + 205, 190, x + 246, 190), fill="#64748b", width=4)
            draw.polygon([(x + 246, 190), (x + 232, 182), (x + 232, 198)], fill="#64748b")
        x += 230
    _save_png(image, path)
    return path


def _svg_open(width: int, height: int) -> str:
    return (
        f'<svg viewBox="0 0 {width} {height}" width="100%" height="auto" '
        'role="img" xmlns="http://www.w3.org/2000/svg">'
        f'<rect width="{width}" height="{height}" fill="white"/>'
    )


def _svg_text(x: float, y: float, text: str, *, size: int = 14, weight: int = 400, fill: str = TEXT, rotate: int = 0) -> str:
    transform = f' transform="rotate({rotate} {x} {y})"' if rotate else ""
    return f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}"{transform}>{escape(text)}</text>'


def _empty_svg(title: str, width: int, height: int) -> str:
    return "\n".join(
        [
            _svg_open(width, height),
            _svg_text(24, 32, title, size=20, weight=700),
            _svg_text(24, 88, "No data available for this view.", size=14, fill=MUTED),
            "</svg>",
        ]
    )


def _corr_color(value: float) -> str:
    value = max(-1.0, min(1.0, value))
    if value >= 0:
        intensity = int(255 - value * 115)
        return f"rgb({intensity},{220 - int(value * 80)},{255})"
    intensity = int(255 + value * 70)
    return f"rgb(255,{intensity},{intensity})"


def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _save_png(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
