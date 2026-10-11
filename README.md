# South Korea — LawCodex (대한민국 법령)

The legislation of the Republic of Korea in force, as plain Markdown, generated from the
official **National Law Information Center** (국가법령정보센터, https://www.law.go.kr), run by
the Ministry of Government Legislation (법제처). Part of [LawCodex](https://github.com/LawCodex):
one repository per jurisdiction.

All texts are in Korean, the official language, reproduced verbatim from the official XML of the
law.go.kr Open API. Nothing is translated or summarised.

- Retrieved: **2026-10-11**
- Version: the current consolidated text (현행법령) of each law as published by law.go.kr,
  i.e. the version in force on the retrieval date, incorporating all amendments.

## Coverage

| Directory | 법령 종류 | Files |
| --- | --- | ---: |
| `constitution/` | 헌법 — Constitution of the Republic of Korea (대한민국헌법) | __CONSTITUTION__ |
| `laws/` | 법률 — Acts of the National Assembly (plus 1 대통령긴급명령, a presidential emergency order with the force of law) | __LAWS__ |
| `presidential-decrees/` | 대통령령 — Presidential Decrees (시행령, 규정, 직제 ...) | __PD__ |
| `ordinances/` | 총리령 · 부령 — Ordinances of the Prime Minister and of the Ministries (시행규칙 ...) | __ORD__ |
| `rules/` | 규칙 — Rules of the National Assembly, Supreme Court, Constitutional Court, election commissions and Board of Audit and Inspection | __RULES__ |
| **Total** | | **__TOTAL__** |

This is every entry of the law.go.kr current-law list (`lawSearch.do?target=law`, which only
returns 현행 = in-force versions): __LISTED__ entries on the retrieval date.

### Not covered

- **Repealed laws and past versions** (연혁법령): only current versions are included. Use the
  git history of this repository to follow changes over time on refresh.
- **Administrative rules** (행정규칙: 훈령, 예규, 고시 ...), **local ordinances** (자치법규:
  조례, 규칙 of provinces and municipalities), treaties (조약), court decisions (판례) and
  Constitutional Court decisions — they are separate targets of the law.go.kr API and were not
  collected.
- **Images, PDF/HWP forms** (별표 서식 files, formula images): not stored in this repository.
  Inline images are kept as links to their official URL on law.go.kr (`![imgNNN](https://www.law.go.kr/flDownload.do?flSeq=...)`),
  and each annexed table/form (별표 · 서식) links to its official PDF, HWP and image file.
  Where law.go.kr provides a text rendering of a table or formula (box-drawing text), it is
  kept verbatim in a ```` ```text ```` block.
- **Amendment statements and reasons** (개정문, 제개정이유) included in the API XML are not
  reproduced; the addenda (부칙) of all amending acts are.

## Structure

```
constitution/001444-daehanmingukheonbeop.md          대한민국헌법
laws/<first 3 digits of 법령ID>/<법령ID>-<romanized title>.md
    laws/001/001706-minbeop.md                       민법
presidential-decrees/<first 3 digits of 법령ID>/<법령ID>-<romanized title>.md
    presidential-decrees/003/003956-sodeuksebeop-sihaengryeong.md   소득세법 시행령
ordinances/<ministry>/<법령ID>-<romanized title>.md
    ordinances/prime-minister/...                    총리령
    ordinances/justice/...                           법무부령
rules/<body>/<법령ID>-<romanized title>.md
    rules/supreme-court/...                          대법원규칙
```

- File names start with the **법령ID** (the stable 6-digit law identifier of law.go.kr, which
  does not change across amendments) followed by a letter-by-letter Revised Romanization of
  the Korean title (truncated to 80 characters). The Korean title is in the front matter and
  the H1. `laws/` and `presidential-decrees/` are sharded by the first three digits of the
  법령ID to keep directories under 1,000 files.
- Ordinances are grouped by issuing ministry, using the ministry name in the ordinance's
  kind (e.g. 법무부령 → `justice/`). A few ordinances still carry the name of a ministry that
  has since been reorganised (e.g. 건설교통부령, 노동부령); they are grouped under that
  historical name.

### Document format

```markdown
---
title: "민법"
identifier: "001706"            # 법령ID (stable)
mst: "284415"                   # 법령일련번호 (MST) of this version
type: act                       # constitution | act | emergency-order | presidential-decree | ordinance | rule
kind: "법률"                    # 법령구분 as given by law.go.kr
jurisdiction: kr
language: ko
promulgation_number: "법률 제21454호"   # of the latest amendment
date: 2026-03-17                # promulgation date (공포일자) of the current version
effective: 2026-03-17           # entry-into-force date (시행일자) of the current version
amendment_type: "일부개정"       # 제정 | 일부개정 | 전부개정 | 타법개정 ...
ministry: "법무부"               # competent ministry (소관부처)
status: in_force
source: "https://www.law.go.kr/LSW/lsInfoP.do?lsiSeq=284415"
retrieved: 2026-10-11
---

# 민법

## 제1편 총칙
### 제1장 통칙
...
```

Hierarchy mapping:

| Korean unit | Markdown |
| --- | --- |
| 편 (part) / 장 (chapter) / 절 (section) / 관 (sub-section) / 항 (sub-sub-section, 민법 only) | headings `##` downwards; only the levels a law actually uses are allocated |
| 조 (article), incl. 조의N | the next heading level (`######` at most; deeper, e.g. in 민법, a **bold** line) — `제3조의2(제목)` |
| 항 (paragraph ①②③) | paragraph |
| 호 (item 1. 2. 3.) | list item `- 1\. ...` |
| 목 (sub-item 가. 나. 다.) | nested list item `  - 가. ...` |
| 부칙 (addenda) | `## 부칙`, one `###` per addendum (`부칙 <제12345호,2020.1.1>`) |
| 별표 · 서식 (annexed tables and forms) | `## 별표 · 서식`, one `###` per annex, with links to the official PDF/HWP/image and the text rendering in a code block |

Editorial notes of law.go.kr such as `<개정 2016.2.3>` or `[본조신설 2018.12.24]` are part of the
official consolidated text and are kept.

## Source

- 국가법령정보센터 Open API (법제처): https://open.law.go.kr — `https://www.law.go.kr/DRF/lawSearch.do?target=law&type=XML`
  (list) and `https://www.law.go.kr/DRF/lawService.do?target=law&type=XML&MST=...` (full text).
- The API requires an `OC` parameter (the id of a registered open.law.go.kr user). The scripts
  use `OC=test`, the sample value used in the official API guide, which the server accepts;
  set the environment variable `LAW_OC` to your own registered id to use that instead.

## Licence / copyright

Under Article 7 of the Korean Copyright Act (저작권법 제7조), the Constitution, laws, treaties,
decrees, ordinances, regulations and similar official texts are **not protected by copyright**.
The law.go.kr Open API data is published by the Ministry of Government Legislation as public data
for free reuse (공공데이터). This repository's Markdown conversion is likewise free to reuse.
This is not an official publication; in case of doubt, refer to law.go.kr.

## Regenerating

```sh
pip install -r scripts/requirements.txt
python scripts/fetch.py     # downloads the list and every law's XML to ../_raw/kr/ (cached)
python scripts/convert.py   # regenerates constitution/ laws/ presidential-decrees/ ordinances/ rules/
```

`fetch.py` uses a descriptive User-Agent, at most 3 concurrent requests with a short delay,
retries with exponential backoff, and caches raw XML so re-runs do not re-download (delete the
cache, or the `list/` directory, to refresh).
