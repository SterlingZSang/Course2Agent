# Course2Agent

Course2Agent 把一组课程资料转换成一个可引用、可检索、可教学的 course agent。它参考了 [Paper2Agent](https://github.com/jmiao24/Paper2Agent) 的双交付思路，但针对课程场景重新设计：

- **Course2Skill** 决定如何讲解、复习、出 formative quiz、处理课程范围和 assessment integrity。
- **Course2MCP** 负责确定性检索、原文读取、资料覆盖说明和 citation-ready context。

它不是简单的“把 PDF 丢进聊天框”。每条课程证据都保留 source hash 和定位信息，例如 PDF page、PowerPoint slide、notebook cell 或文本行号。

## 当前 MVP

支持 `.pdf`、`.pptx`、`.docx`、`.ipynb`、Markdown、纯文本、代码、CSV/TSV、JSON/YAML 和 HTML。生成的 MCP server 只依赖 Python 标准库；构建 PDF 课程包时额外需要 `pypdf`。

MCP tools：

- `get_course_overview`
- `search_course`
- `read_course_chunk`
- `build_study_context`

## 安装与试用

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e '.[pdf]'

course2agent build examples/demo-course \
  --title 'CELL101 Foundations of Cell Biology' \
  --output dist/cell101-agent

course2agent verify dist/cell101-agent
course2agent search dist/cell101-agent 'cholesterol membrane fluidity'
```

生成结果：

```text
dist/cell101-agent/
├── skill/cell101-foundations-of-cell-biology-course/
│   ├── SKILL.md
│   └── references/
├── mcp/server.py
├── knowledge/
│   ├── manifest.json
│   └── chunks.jsonl
├── sources/
└── USAGE.md
```

## 设计原则

1. **Course-grounded**：课程特定结论必须先检索，并带出处。
2. **Authority-aware**：syllabus/rubric 决定要求；lecture/readings 提供内容；exercise 只代表练习风格。
3. **Pedagogy-aware**：从定义、worked example 到理解检查，而不只是返回相似段落。
4. **Assessment-safe**：可以解释概念、拆 rubric、给反馈，但不伪造实验结果或冒充学生完成受评作业。
5. **Local-first**：默认本地构建、本地检索，不需要外部 API 或 embedding 服务。

## 与 Paper2Agent 的关键差别

Paper2Agent 的 MCP 主要把 research code 变成 scientific tools；Course2Agent 的 MCP 主要把异构课程资料变成可追溯的 evidence tools。课程教学行为放在 skill 中，而检索与出处保持确定性。这一拆分让 agent 能够更换 LLM，同时保留同一套课程证据边界。

## 验证

```bash
python3 -m unittest discover -s tests -v
python3 /path/to/skill-creator/scripts/quick_validate.py skills/course2agent
```

## 下一步

- OCR 与 diagram-aware extraction
- semantic/hybrid retrieval
- prerequisite concept graph 与 mastery state
- instructor/student 两种权限视图
- LMS export（Canvas/Moodle）与可审计的更新流程

本项目是对 Paper2Agent 架构思想的独立课程场景实现；未复制其转换脚本。

