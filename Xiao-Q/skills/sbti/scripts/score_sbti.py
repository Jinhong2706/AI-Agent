from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "sbti_data.json"


with DATA_PATH.open("r", encoding="utf-8") as fh:
    DATA = json.load(fh)


DIMENSION_META = DATA["dimensionMeta"]
QUESTIONS = DATA["questions"]
SPECIAL_QUESTIONS = DATA["specialQuestions"]
TYPE_LIBRARY = DATA["typeLibrary"]
TYPE_IMAGES = DATA["typeImages"]
NORMAL_TYPES = DATA["normalTypes"]
DIMENSION_EXPLANATIONS = DATA["dimensionExplanations"]
DIMENSION_ORDER = DATA["dimensionOrder"]
DRUNK_TRIGGER_QUESTION_ID = DATA["drunkTriggerQuestionId"]
QUESTION_LOOKUP = {question["id"]: question for question in QUESTIONS + SPECIAL_QUESTIONS}


def sum_to_level(score: int) -> str:
    if score <= 3:
        return "L"
    if score == 4:
        return "M"
    return "H"


def level_num(level: str) -> int:
    return {"L": 1, "M": 2, "H": 3}[level]


def parse_pattern(pattern: str) -> list[str]:
    return list(pattern.replace("-", ""))


def required_question_ids(answers: dict[str, int]) -> list[str]:
    required = [question["id"] for question in QUESTIONS]
    required.append("drink_gate_q1")
    if answers.get("drink_gate_q1") == 3:
        required.append(DRUNK_TRIGGER_QUESTION_ID)
    return required


def validate_answers(answers: dict[str, int]) -> None:
    known_ids = set(QUESTION_LOOKUP)
    unknown = sorted(set(answers) - known_ids)
    if unknown:
        raise ValueError(f"Unknown question ids: {', '.join(unknown)}")

    invalid_values: list[str] = []
    for question_id, value in answers.items():
        allowed = {option["value"] for option in QUESTION_LOOKUP[question_id]["options"]}
        if value not in allowed:
            invalid_values.append(
                f"{question_id}={value} (allowed: {sorted(allowed)})"
            )
    if invalid_values:
        raise ValueError("Invalid option values: " + "; ".join(invalid_values))

    missing = [qid for qid in required_question_ids(answers) if qid not in answers]
    if missing:
        raise ValueError("Missing required answers: " + ", ".join(missing))


def compute_result(answers: dict[str, int]) -> dict:
    validate_answers(answers)

    raw_scores = {dim: 0 for dim in DIMENSION_META}
    levels: dict[str, str] = {}
    dimension_details = []

    for question in QUESTIONS:
        raw_scores[question["dim"]] += int(answers.get(question["id"], 0))

    for dim, score in raw_scores.items():
        levels[dim] = sum_to_level(score)

    user_vector = [level_num(levels[dim]) for dim in DIMENSION_ORDER]
    ranked = []
    for normal_type in NORMAL_TYPES:
        vector = [level_num(level) for level in parse_pattern(normal_type["pattern"])]
        distance = 0
        exact = 0
        for index, current in enumerate(vector):
            diff = abs(user_vector[index] - current)
            distance += diff
            if diff == 0:
                exact += 1
        similarity = max(0, round((1 - distance / 30) * 100))
        merged = {
            **TYPE_LIBRARY[normal_type["code"]],
            **normal_type,
            "distance": distance,
            "exact": exact,
            "similarity": similarity,
        }
        ranked.append(merged)

    ranked.sort(
        key=lambda item: (item["distance"], -item["exact"], -item["similarity"])
    )

    best_normal = ranked[0]
    drunk_triggered = answers.get(DRUNK_TRIGGER_QUESTION_ID) == 2

    mode_kicker = "你的主类型"
    badge = f"匹配度 {best_normal['similarity']}% · 精准命中 {best_normal['exact']}/15 维"
    sub = "维度命中度较高，当前结果可视为你的第一人格画像。"
    special = False
    secondary_type = None
    final_type = best_normal

    if drunk_triggered:
        final_type = TYPE_LIBRARY["DRUNK"]
        secondary_type = best_normal
        mode_kicker = "隐藏人格已激活"
        badge = "匹配度 100% · 酒精异常因子已接管"
        sub = "乙醇亲和性过强，系统已直接跳过常规人格审判。"
        special = True
    elif best_normal["similarity"] < 60:
        final_type = TYPE_LIBRARY["HHHH"]
        mode_kicker = "系统强制兜底"
        badge = f"标准人格库最高匹配仅 {best_normal['similarity']}%"
        sub = "标准人格库对你的脑回路集体罢工了，于是系统把你强制分配给了 HHHH。"
        special = True

    image_file = TYPE_IMAGES.get(final_type["code"])
    image_path = str((ROOT / image_file).resolve()) if image_file else None

    for dim in DIMENSION_ORDER:
        level = levels[dim]
        meta = DIMENSION_META[dim]
        dimension_details.append(
            {
                "id": dim,
                "name": meta["name"],
                "model": meta["model"],
                "rawScore": raw_scores[dim],
                "level": level,
                "explanation": DIMENSION_EXPLANATIONS[dim][level],
            }
        )

    return {
        "finalType": final_type,
        "modeKicker": mode_kicker,
        "badge": badge,
        "sub": sub,
        "special": special,
        "secondaryType": secondary_type,
        "bestNormal": best_normal,
        "top3": ranked[:3],
        "rawScores": raw_scores,
        "levels": levels,
        "dimensions": dimension_details,
        "imageFile": image_file,
        "imagePath": image_path,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Score SBTI answers.")
    parser.add_argument(
        "--answers-json",
        required=True,
        help="JSON object mapping question ids to numeric option values.",
    )
    args = parser.parse_args()

    try:
        answers = json.loads(args.answers_json)
        if not isinstance(answers, dict):
            raise ValueError("answers-json must decode to an object.")
        normalized_answers = {str(key): int(value) for key, value in answers.items()}
        result = compute_result(normalized_answers)
    except Exception as exc:  # noqa: BLE001
        print(str(exc), file=sys.stderr)
        return 1

    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
