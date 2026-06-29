#!/usr/bin/env python3

import argparse
import json
from pathlib import Path

from recognition_postprocess import normalize_deck_result, normalize_slide_result


def aggregate_slides(output_dir: Path, master_file: Path, source_file: str = ""):
    slides = []
    slide_files = sorted(
        output_dir.glob("slide_*_result.json"),
        key=lambda path: int(path.stem.split("_")[1]),
    )

    for slide_file in slide_files:
        try:
            slide_number = int(slide_file.stem.split("_")[1])
        except (IndexError, ValueError):
            print(f"  [!] Skip unrecognized file name: {slide_file.name}")
            continue

        try:
            with open(slide_file, "r", encoding="utf-8") as file_obj:
                data = json.load(file_obj)
        except json.JSONDecodeError:
            print(f"  [!] Error decoding {slide_file}")
            continue

        data["slide_number"] = slide_number
        slides.append(normalize_slide_result(data))
        print(f"  [+] Loaded slide {slide_number}")

    master_data = normalize_deck_result(
        {
            "deck_title": "客户PPT标准化转换结果",
            "slides": slides,
        },
        source_file=source_file,
    )

    with open(master_file, "w", encoding="utf-8") as file_obj:
        json.dump(master_data, file_obj, ensure_ascii=False, indent=2)
    print(f"\n[√] Master deck JSON generated: {master_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aggregate per-slide recognition JSON into a normalized deck JSON.")
    parser.add_argument("--output-dir", type=Path, default=Path("output"), help="Directory containing slide_*_result.json files")
    parser.add_argument("--master-file", type=Path, default=Path("output/master_deck.json"), help="Path to write the aggregated deck JSON")
    parser.add_argument("--source-file", default="", help="Optional source PPT path or filename to store in deck metadata")
    args = parser.parse_args()
    aggregate_slides(args.output_dir, args.master_file, source_file=args.source_file)
