#!/usr/bin/env python3
"""按目标 JD 检查简历：关键词覆盖率、量化率、弱动词。

用法：
    python scripts/check_jd_match.py --jd jd.txt --resume resume.txt
    python scripts/check_jd_match.py --jd jd.txt --resume resume.txt --fail-under 0.6
    python scripts/check_jd_match.py --jd jd.txt --resume resume.txt --json

退出码：正常 0；覆盖率低于 --fail-under 时 1；参数/文件错误 2。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_LEXICON = Path(__file__).resolve().parent.parent / "references" / "skills-lexicon.txt"

WEAK_PATTERNS = [
    "负责", "参与", "协助", "配合", "跟进", "支持工作", "本人",
    "responsible for", "involved in", "assisted", "helped with",
    "worked on", "supported", "coordinated", "participated in",
    "contributed to", "in charge of", "took part in", "dealt with",
]

# 弱动词只在「主语位置」才算：条目开头，或前面只有以代词结尾的短状语。
# 反例：「销售跟进响应时间从 26 小时缩到 4 小时」——『跟进』是名词搭配的一部分。
SUBJECT_TAIL = ("我", "我们", "本人", "自己", "咱")


def at_subject_position(body: str, pos: int) -> bool:
    prefix = body[:pos].strip(" ，,、：:的")
    if not prefix:
        return True
    return len(prefix) <= 8 and prefix.endswith(SUBJECT_TAIL)

# 数字或“百分比/数量”迹象：阿拉伯数字，或 中文数量 + 单位
NUMBER_RE = re.compile(
    r"\d|百分之|半|翻[一二两三]?倍|[一二三四五六七八九十百千万亿]+\s*(?:%|个|项|人|家|单|次|天|周|月|年|小时|万|千|元|倍|分)"
)

SPLIT_RE = re.compile(r"[。；;\n!?！？]")


def load_lexicon(path: Path) -> list[str]:
    terms: list[str] = []
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        term = line.split("|")[0].strip()
        if term and term not in terms:
            terms.append(term)
    terms.sort(key=len, reverse=True)
    return terms


def find_terms(text: str, terms: list[str]) -> list[str]:
    low = text.lower()
    hits = [t for t in terms if t.lower() in low]
    # 去掉被更长命中词包含的短词：命中「漏斗分析」时不再单列「漏斗」
    return [t for t in hits if not any(t != o and t.lower() in o.lower() for o in hits)]


def bullets(text: str) -> list[str]:
    out = []
    for line in text.splitlines():
        s = line.strip().lstrip("-*·•|0123456789.、()（） ").strip()
        if len(s) >= 8:
            out.append(s)
    return out


def analyze(jd: str, resume: str, terms: list[str]) -> dict:
    jd_terms = find_terms(jd, terms)
    resume_terms = find_terms(resume, terms)
    matched = [t for t in jd_terms if t in resume_terms]
    missing = [t for t in jd_terms if t not in resume_terms]
    extra = [t for t in resume_terms if t not in jd_terms]

    lines = bullets(resume)
    quantified = [b for b in lines if NUMBER_RE.search(b)]
    quant_rate = round(len(quantified) / len(lines), 3) if lines else 0.0

    weak_hits = []
    for i, line in enumerate(resume.splitlines(), start=1):
        body = line.strip().lstrip("-*·•|0123456789.、()（） ").strip()
        for pat in WEAK_PATTERNS:
            pos = body.lower().find(pat.lower())
            if pos >= 0 and at_subject_position(body, pos):
                weak_hits.append({"line": i, "word": pat, "text": line.strip()[:100]})
                break

    coverage = round(len(matched) / len(jd_terms), 3) if jd_terms else 0.0
    weak_penalty = min(1.0, len(weak_hits) / max(1, len(lines)))
    score = round(coverage * 50 + quant_rate * 30 + (1 - weak_penalty) * 20, 1)

    # 建议：把缺失词按在 JD 中出现的次数排序，先补高频的
    missing_ranked = sorted(missing, key=lambda t: -jd.lower().count(t.lower()))

    return {
        "jd_term_count": len(jd_terms),
        "coverage": coverage,
        "matched": matched,
        "missing": missing,
        "missing_ranked": missing_ranked[:12],
        "resume_only_terms": extra[:15],
        "bullet_count": len(lines),
        "quantified_count": len(quantified),
        "quant_rate": quant_rate,
        "weak_verb_hits": weak_hits,
        "score": score,
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="按 JD 检查简历匹配度")
    ap.add_argument("--jd", required=True, help="JD 文本文件")
    ap.add_argument("--resume", required=True, help="简历文本文件")
    ap.add_argument("--lexicon", type=Path, default=DEFAULT_LEXICON, help="能力词库")
    ap.add_argument("--fail-under", type=float, default=None, help="覆盖率低于该值时退出码 1")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    for p in (Path(args.jd), Path(args.resume), args.lexicon):
        if not p.is_file():
            print(f"找不到文件：{p}", file=sys.stderr)
            return 2

    jd = Path(args.jd).read_text(encoding="utf-8-sig")
    resume = Path(args.resume).read_text(encoding="utf-8-sig")
    terms = load_lexicon(args.lexicon)
    r = analyze(jd, resume, terms)

    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print(f"关键词覆盖：{r['coverage'] * 100:.0f}%  （JD {r['jd_term_count']} 个能力词，命中 {len(r['matched'])} 个）")
        print(f"量化率    ：{r['quant_rate'] * 100:.0f}%  （{r['quantified_count']}/{r['bullet_count']} 条 bullet 含数字）")
        print(f"弱动词    ：{len(r['weak_verb_hits'])} 处")
        print(f"综合评分  ：{r['score']}/100")
        if r["missing_ranked"]:
            print("\nJD 高频但简历缺失（优先补）：" + "、".join(r["missing_ranked"]))
        if r["weak_verb_hits"]:
            print("\n弱动词句（改成强动词 + 成果）：")
            for h in r["weak_verb_hits"][:8]:
                print(f"  第 {h['line']} 行 [{h['word']}] {h['text']}")
        if r["quant_rate"] < 0.6:
            print("\n提示：量化率偏低。把“做过很多/提升了”换算成 规模、频次、时长、比例 四类数字。")
        if r["coverage"] < 0.6:
            print("提示：覆盖率偏低。先补证据（项目/结果），再润色措辞。")

    if args.fail_under is not None and r["coverage"] < args.fail_under:
        return 1
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main(sys.argv[1:]))
