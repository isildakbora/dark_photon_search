#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import re
import textwrap

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


class PdfTextWriter:
    def __init__(self, out_path: Path, title: str):
        self.out_path = out_path
        self.title = title
        self.pdf = PdfPages(out_path)
        self.page_no = 0
        self.fig = None
        self.ax = None
        self.y = 0.95
        self._new_page()

    def _new_page(self) -> None:
        if self.fig is not None:
            self._finalize_page()
        self.page_no += 1
        self.fig, self.ax = plt.subplots(figsize=(8.5, 11.0))
        self.ax.set_axis_off()
        self.y = 0.95
        self.ax.text(
            0.05,
            0.985,
            self.title,
            fontsize=9,
            color="#555555",
            va="top",
            ha="left",
        )

    def _finalize_page(self) -> None:
        self.ax.text(
            0.5,
            0.02,
            f"Page {self.page_no}",
            fontsize=9,
            color="#666666",
            va="center",
            ha="center",
        )
        # Keep a fixed page size for consistent printing/viewing.
        self.pdf.savefig(self.fig)
        plt.close(self.fig)

    def close(self) -> None:
        if self.fig is not None:
            self._finalize_page()
        self.pdf.close()

    @staticmethod
    def _wrap_width(fontsize: float, indent: float) -> int:
        base = 110
        indent_penalty = int(indent * 75)
        size_factor = 10.0 / max(7.0, fontsize)
        return max(28, int((base - indent_penalty) * size_factor))

    def _line_height(self, fontsize: float) -> float:
        points_per_page = 72.0 * 11.0
        return (fontsize * 1.38) / points_per_page

    def add_spacer(self, height: float) -> None:
        self.y -= height
        if self.y < 0.06:
            self._new_page()

    def add_text(
        self,
        text: str,
        *,
        fontsize: float = 10.0,
        weight: str = "normal",
        color: str = "#111111",
        indent: float = 0.0,
        family: str = "DejaVu Sans",
    ) -> None:
        if not text:
            self.add_spacer(self._line_height(fontsize))
            return

        wrapped = textwrap.wrap(
            text,
            width=self._wrap_width(fontsize, indent),
            break_long_words=False,
            break_on_hyphens=False,
        )
        if not wrapped:
            wrapped = [""]

        dy = self._line_height(fontsize)
        for line in wrapped:
            if self.y - dy < 0.055:
                self._new_page()
            self.ax.text(
                0.05 + indent,
                self.y,
                line,
                fontsize=fontsize,
                fontweight=weight,
                color=color,
                family=family,
                va="top",
                ha="left",
            )
            self.y -= dy

    def add_rule(self) -> None:
        if self.y < 0.08:
            self._new_page()
        self.ax.plot([0.05, 0.95], [self.y, self.y], color="#999999", linewidth=0.7)
        self.y -= 0.018


def markdown_to_pdf(markdown: str, out_path: Path, title: str) -> None:
    writer = PdfTextWriter(out_path=out_path, title=title)
    in_code_block = False

    for raw_line in markdown.splitlines():
        line = raw_line.rstrip("\n")
        stripped = line.strip()

        if stripped == "```":
            in_code_block = not in_code_block
            writer.add_spacer(0.004)
            continue

        if in_code_block:
            writer.add_text(
                line if line else " ",
                fontsize=8.5,
                family="DejaVu Sans Mono",
                indent=0.03,
                color="#1f2937",
            )
            continue

        if stripped == "---":
            writer.add_rule()
            continue

        if not stripped:
            writer.add_spacer(0.008)
            continue

        if line.startswith("# "):
            writer.add_spacer(0.010)
            writer.add_text(
                line[2:].strip(),
                fontsize=20,
                weight="bold",
                color="#0b172a",
            )
            writer.add_spacer(0.008)
            continue

        if line.startswith("## "):
            writer.add_spacer(0.006)
            writer.add_text(
                line[3:].strip(),
                fontsize=15.0,
                weight="bold",
                color="#12243d",
            )
            writer.add_spacer(0.004)
            continue

        if line.startswith("### "):
            writer.add_spacer(0.004)
            writer.add_text(
                line[4:].strip(),
                fontsize=12.5,
                weight="bold",
                color="#1e3556",
            )
            writer.add_spacer(0.003)
            continue

        numbered_match = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if numbered_match:
            number = numbered_match.group(1)
            rest = numbered_match.group(2)
            writer.add_text(
                f"{number}. {rest}",
                fontsize=10.5,
                indent=0.015,
            )
            continue

        if stripped.startswith("- "):
            writer.add_text(
                f"- {stripped[2:]}",
                fontsize=10.3,
                indent=0.02,
            )
            continue

        writer.add_text(stripped, fontsize=10.4)

    writer.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Streamlit manual PDF from markdown source.")
    parser.add_argument(
        "--source",
        default="docs/Streamlit_User_Manual.md",
        help="Markdown source path.",
    )
    parser.add_argument(
        "--out",
        default="outputs/Streamlit_User_Manual.pdf",
        help="PDF output path.",
    )
    parser.add_argument(
        "--title",
        default="Dark Photon Student Simulation Lab User Manual",
        help="Header title shown on each page.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_path = Path(args.source)
    out_path = Path(args.out)

    if not source_path.exists():
        raise SystemExit(f"Source not found: {source_path}")

    markdown = source_path.read_text(encoding="utf-8")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_to_pdf(markdown=markdown, out_path=out_path, title=args.title)
    print(f"Manual PDF written to: {out_path.resolve()}")


if __name__ == "__main__":
    main()
