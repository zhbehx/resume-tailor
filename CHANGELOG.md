# 更新记录

## v1.0.1 — 2026-10-27

修复弱动词误报。

- 旧规则用「出现位置 <= 6 字」判断是否在句首，导致名词搭配被误判：
  `销售跟进响应时间从 26 小时缩到 4 小时` 里的「跟进」被报成弱动词。
- 新规则要求弱动词处于**主语位置**：要么在条目开头，要么前面只有以代词结尾的短状语
  （我 / 我们 / 本人 / 自己）。同一句现在判 0 处，而 `这次改版我参与了…` 仍会被抓到。
- 英文弱动词词表从 4 个扩到 12 个，新增 worked on / supported / coordinated /
  participated in / contributed to / in charge of / took part in / dealt with。
- 回归验证：旧稿仍 6 处弱动词 / 5.0 分，新稿仍 0 处 / 90.0 分（examples 里的数字全部不变）。

## v1.0.0 — 2026-10-26

- `SKILL.md`：五条原则、Step 0–5 工作流、默认交付格式、6 条反模式
- `references/jd-decode.md`：三类要求拆解、隐性信号对照表、ATS 与人筛规则、JD 陷阱
- `references/bullet-formulas.md`：XYZ 公式、20 条 bullet 公式、强弱动词对照、无数字换算三步法
- `references/skills-lexicon.txt`：约 200 条能力词库，按职能分类
- `scripts/check_jd_match.py`：覆盖率 / 量化率 / 弱动词检查，支持 `--fail-under` 与 `--json`
- `examples/01-pm-to-growth.md`：B 端转增长岗完整案例（综合分 5.0 → 90.0，实测输出）
