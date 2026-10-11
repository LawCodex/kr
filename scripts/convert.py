#!/usr/bin/env python3
"""Convert law.go.kr DRF XML (cached by fetch.py under _raw/kr/) to Markdown.

Usage: python convert.py [--raw DIR] [--out DIR]
"""
import argparse
import datetime
import glob
import os
import re
import shutil
import sys

from lxml import etree

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_RAW = os.path.normpath(os.path.join(HERE, "..", "..", "_raw", "kr"))
DEFAULT_OUT = os.path.normpath(os.path.join(HERE, ".."))
CATEGORY_DIRS = ["constitution", "laws", "presidential-decrees", "ordinances", "rules"]

# ---------------------------------------------------------------- romanization
# Revised Romanization of Korean, letter-by-letter (no sound-change rules), for slugs.
INITIALS = ["g", "kk", "n", "d", "tt", "r", "m", "b", "pp", "s", "ss", "", "j", "jj",
            "ch", "k", "t", "p", "h"]
MEDIALS = ["a", "ae", "ya", "yae", "eo", "e", "yeo", "ye", "o", "wa", "wae", "oe", "yo",
           "u", "wo", "we", "wi", "yu", "eu", "ui", "i"]
FINALS = ["", "k", "k", "ks", "n", "nj", "nh", "t", "l", "lk", "lm", "lb", "ls", "lt",
          "lp", "lh", "m", "p", "ps", "t", "t", "ng", "t", "t", "k", "t", "p", "t"]


def romanize(s):
    out = []
    for ch in s:
        o = ord(ch)
        if 0xAC00 <= o <= 0xD7A3:
            o -= 0xAC00
            out.append(INITIALS[o // 588] + MEDIALS[(o % 588) // 28] + FINALS[o % 28])
        elif ch.isascii() and ch.isalnum():
            out.append(ch.lower())
        else:
            out.append(" ")
    return out


def slugify(title, maxlen=80):
    words = []
    for w in re.split(r"\s+", title):
        r = re.sub(r"\s+", "-", "".join(romanize(w)).strip())
        if r:
            words.append(r)
    slug = re.sub(r"-+", "-", "-".join(words)).strip("-")
    if len(slug) > maxlen:
        slug = slug[:maxlen].rsplit("-", 1)[0]
    return slug or "untitled"


# English directory names for ministries / issuing bodies (ordinances and rules).
BODY_SLUGS = {
    "총리령": "prime-minister",
    "국토교통부령": "land-infrastructure-transport",
    "보건복지부령": "health-welfare",
    "행정안전부령": "interior-safety",
    "해양수산부령": "oceans-fisheries",
    "기후에너지환경부령": "climate-energy-environment",
    "농림축산식품부령": "agriculture-food-rural-affairs",
    "법무부령": "justice",
    "교육부령": "education",
    "문화체육관광부령": "culture-sports-tourism",
    "국방부령": "national-defense",
    "재정경제부령": "finance-economy",
    "과학기술정보통신부령": "science-ict",
    "산업통상부령": "trade-industry",
    "고용노동부령": "employment-labor",
    "기획재정부령": "economy-finance",
    "외교부령": "foreign-affairs",
    "성평등가족부령": "gender-equality-family",
    "국가보훈부령": "patriots-veterans-affairs",
    "중소벤처기업부령": "smes-startups",
    "통일부령": "unification",
    "산업통상자원부령": "trade-industry-energy",
    "교육과학기술부령": "education-science-technology",
    "농림수산식품부령": "food-agriculture-forestry-fisheries",
    "행정자치부령": "government-administration-home-affairs",
    "환경부령": "environment",
    "경제기획원령": "economic-planning-board",
    "여성가족부령": "gender-equality-family-2010",
    "교육인적자원부령": "education-human-resources",
    "국토해양부령": "land-transport-maritime",
    "건설교통부령": "construction-transportation",
    "노동부령": "labor",
    "대법원규칙": "supreme-court",
    "헌법재판소규칙": "constitutional-court",
    "중앙선거관리위원회규칙": "national-election-commission",
    "선거관리위원회규칙": "election-commission",
    "국회규칙": "national-assembly",
    "감사원규칙": "board-of-audit-inspection",
}


def classify(kind):
    """Return (directory parts, front-matter type) for a 법령구분명 / 법종구분."""
    if kind == "헌법":
        return ["constitution"], "constitution"
    if kind == "법률":
        return ["laws"], "act"
    if kind == "대통령긴급명령":
        return ["laws"], "emergency-order"
    if kind == "대통령령":
        return ["presidential-decrees"], "presidential-decree"
    if kind == "총리령" or kind.endswith("부령") or kind.endswith("원령"):
        return ["ordinances", BODY_SLUGS.get(kind) or slugify(kind)], "ordinance"
    if kind.endswith("규칙"):
        return ["rules", BODY_SLUGS.get(kind) or slugify(kind)], "rule"
    return ["other"], "unknown"


# ---------------------------------------------------------------- text helpers
BOX = re.compile(r"[─━│┃┌┐└┘├┤┬┴┼┏┓┗┛┣┫┳┻╋═║╔╗╚╝╠╣╦╩╬]")
IMG = re.compile(r'<img\s+[^>]*?src="([^"]+)"[^>]*?(?:alt="([^"]*)")?[^>]*>', re.I)


def fix_url(u):
    u = u.strip()
    if u.startswith("/"):
        u = "https://www.law.go.kr" + u
    return re.sub(r"^http://", "https://", u)


def md_escape(line):
    line = re.sub(r"<(?=[A-Za-z/!?])", "&lt;", line)
    line = re.sub(r"^(\s*)([#>+*-])", r"\1\\\2", line)
    line = re.sub(r"^(\s*\d+)([.)])(\s|$)", r"\1\\\2\3", line)
    return line


def node_text(el):
    """Concatenate all text inside an element (multiple CDATA sections)."""
    if el is None:
        return ""
    raw = etree.tostring(el, encoding=str, with_tail=False)
    parts = CDATA.findall(raw)
    if parts:
        t = "".join(parts)
        if "&lt;" in t or "&gt;" in t:
            t = t.replace("&lt;", "<").replace("&gt;", ">")
        return t
    return "".join(el.itertext())


CDATA = re.compile(r"<!\[CDATA\[(.*?)\]\]>", re.S)
PARSER = etree.XMLParser(strip_cdata=False, huge_tree=True)


IMG_PAIR = re.compile(r'(<img\s[^>]*>)(.*?)(?:</img>|$)', re.I | re.S)


def render_block(text, indent=""):
    """Render text that may contain <img ...>ascii rendering</img> segments."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if "<img" not in text.lower():
        return render_plain(text, indent)
    lines, pos = [], 0
    for m in IMG_PAIR.finditer(text):
        before = text[pos:m.start()]
        if before.strip():
            if lines:
                lines.append("")
            lines.extend(render_plain(before, indent))
        im = IMG.match(m.group(1))
        if lines:
            lines.append("")
        if im:
            lines.append(indent + f"![{im.group(2) or 'image'}]({fix_url(im.group(1))})")
        inner = [l.rstrip() for l in m.group(2).split("\n")]
        while inner and not inner[-1].strip():
            inner.pop()
        while inner and not inner[0].strip():
            inner.pop(0)
        if inner:
            lines.append("")
            lines.append(indent + "```text")
            lines.extend(indent + l.replace("```", "ˋˋˋ") for l in inner)
            lines.append(indent + "```")
        pos = m.end()
    rest = text[pos:]
    if rest.strip():
        if lines:
            lines.append("")
        lines.extend(render_plain(rest, indent))
    return lines


def render_plain(text, indent=""):
    """Render a (possibly multi-line) text block to Markdown lines.

    Lines drawn with box characters go into ```text fences, <img> tags become
    image links, other lines are joined with hard line breaks."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    raw_lines = text.split("\n")
    while raw_lines and not raw_lines[-1].strip():
        raw_lines.pop()
    while raw_lines and not raw_lines[0].strip():
        raw_lines.pop(0)
    out = []  # list of (kind, line)
    for ln in raw_lines:
        ln = ln.rstrip()
        imgs = list(IMG.finditer(ln))
        if imgs:
            rest = IMG.sub("", ln).strip()
            for m in imgs:
                alt = m.group(2) or "image"
                out.append(("img", f"![{alt}]({fix_url(m.group(1))})"))
            if rest:
                out.append(("box" if BOX.search(rest) else "text", rest))
            continue
        out.append(("box" if BOX.search(ln) else "text", ln))
    # a run of lines that contains box drawing (plus any blank lines between) is fenced
    res = []
    i = 0
    while i < len(out):
        kind, ln = out[i]
        if kind == "box":
            j = i
            block = []
            while j < len(out) and out[j][0] in ("box", "text"):
                if out[j][0] == "text":
                    # only absorb non-box lines if a later box line follows soon
                    k = j
                    while k < len(out) and out[k][0] == "text" and k - j < 3:
                        k += 1
                    if not (k < len(out) and out[k][0] == "box"):
                        break
                    block.extend(l for _, l in out[j:k])
                    j = k
                    continue
                block.append(out[j][1])
                j += 1
            res.append(("fence", block))
            i = j
        elif kind == "img":
            res.append(("img", ln))
            i += 1
        else:
            para = []
            while i < len(out) and out[i][0] == "text":
                if out[i][1].strip():
                    para.append(md_escape(out[i][1].strip()))
                elif para:
                    res.append(("para", para))
                    para = []
                i += 1
            if para:
                res.append(("para", para))
    lines = []
    for kind, val in res:
        if lines:
            lines.append("")
        if kind == "fence":
            lines.append(indent + "```text")
            lines.extend(indent + l.replace("```", "ˋˋˋ") for l in val)
            lines.append(indent + "```")
        elif kind == "img":
            lines.append(indent + val)
        else:
            lines.append(indent + ("  \n" + indent).join(val))
    return lines


# ---------------------------------------------------------------- structure
UNIT_RE = re.compile(r"^제\s*\d+\s*(?:의\s*\d+\s*)?(편|장|절|관|항)(?:\s*의\s*\d+)?(?![가-힣])")
UNIT_ORDER = ["편", "장", "절", "관", "항"]


def unit_kind(text):
    m = UNIT_RE.match(text.strip())
    return m.group(1) if m else None


def article_label(art):
    no = (art.findtext("조문번호") or "").strip()
    br = (art.findtext("조문가지번호") or "").strip()
    label = f"제{no}조" + (f"의{br}" if br and br not in ("0", "00") else "")
    return label


def strip_article_prefix(content, label, title):
    c = content.lstrip()
    if c.startswith(label):
        c = c[len(label):]
        if title and c.startswith("(" + title + ")"):
            c = c[len(title) + 2:]
        elif c.startswith("(") and title is None:
            pass
        return c.strip()
    return content.strip()


def heading(level, text):
    text = re.sub(r"\s+", " ", text.strip())
    text = re.sub(r"<(?=[A-Za-z/!?])", "&lt;", text)
    if level <= 6:
        return ["#" * level + " " + text, ""]
    return [f"**{text}**", ""]


def render_items(parent, lines):
    """호 and 목 under a 항 (or directly under a 조)."""
    for ho in parent.findall("호"):
        t = node_text(ho.find("호내용"))
        if t.strip():
            blk = render_block(t, "  ")
            blk[0] = "- " + blk[0][2:]
            lines.extend(blk)
            lines.append("")
        for mok in ho.findall("목"):
            t = node_text(mok.find("목내용"))
            if t.strip():
                blk = render_block(t, "    ")
                blk[0] = "  - " + blk[0][4:]
                lines.extend(blk)
                lines.append("")
            # 세목 (sub-items) if present
            for sm in mok.iter():
                if sm is mok or sm.tag in ("목번호", "목내용"):
                    continue
                if sm.tag.endswith("내용") and node_text(sm).strip():
                    blk = render_block(node_text(sm), "      ")
                    blk[0] = "    - " + blk[0][6:]
                    lines.extend(blk)
                    lines.append("")


def render_article(art, level, lines):
    label = article_label(art)
    title = art.findtext("조문제목")
    title = title.strip() if title else None
    head = label + (f"({title})" if title else "")
    lines.extend(heading(level, head))
    body = strip_article_prefix(node_text(art.find("조문내용")), label, title)
    if body:
        lines.extend(render_block(body))
        lines.append("")
    for hang in art.findall("항"):
        t = node_text(hang.find("항내용"))
        if t.strip():
            lines.extend(render_block(t))
            lines.append("")
        render_items(hang, lines)
    for ref in art.findall("조문참고자료"):
        t = node_text(ref)
        if t.strip():
            lines.extend(render_block(t))
            lines.append("")


def ymd(s):
    s = (s or "").strip()
    if re.fullmatch(r"\d{8}", s):
        return f"{s[:4]}-{s[4:6]}-{s[6:]}"
    return None


def yq(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def convert(xml_path, out_root, today, listinfo):
    root = etree.parse(xml_path, PARSER).getroot()
    info = root.find("기본정보")
    law_id = info.findtext("법령ID").strip()
    title = node_text(info.find("법령명_한글")).strip()
    kind = (info.findtext("법종구분") or "").strip()
    mst = os.path.basename(xml_path)[:-4]
    li = listinfo.get(mst, {})
    if li.get("kind"):
        kind = li["kind"]
    dirs, ftype = classify(kind)
    if dirs[0] in ("laws", "presidential-decrees"):
        dirs = dirs + [law_id[:3]]
    fname = f"{law_id}-{slugify(title)}.md"
    rel = os.path.join(*dirs, fname)

    fm = ["---", f"title: {yq(title)}"]
    hanja = node_text(info.find("법령명_한자")).strip()
    if hanja and hanja != title:
        fm.append(f"title_hanja: {yq(hanja)}")
    abbr = node_text(info.find("법령명약칭")).strip()
    if abbr:
        fm.append(f"short_title: {yq(abbr)}")
    fm.append(f'identifier: "{law_id}"')
    fm.append(f'mst: "{mst}"')
    fm.append(f"type: {ftype}")
    fm.append(f"kind: {yq(kind)}")
    fm += ["jurisdiction: kr", "language: ko"]
    prom_no = (info.findtext("공포번호") or "").strip()
    if prom_no:
        fm.append(f"promulgation_number: {yq(kind + ' 제' + prom_no.lstrip('0') + '호')}")
    d = ymd(info.findtext("공포일자"))
    if d:
        fm.append(f"date: {d}")
    d = ymd(info.findtext("시행일자"))
    if d:
        fm.append(f"effective: {d}")
    amend = (info.findtext("제개정구분") or "").strip()
    if amend:
        fm.append(f"amendment_type: {yq(amend)}")
    min_names = [node_text(e).strip() for e in info.findall("소관부처")]
    min_names = [m for m in min_names if m] or ([li["ministry"]] if li.get("ministry") else [])
    if min_names:
        fm.append(f"ministry: {yq(', '.join(min_names))}")
    fm.append("status: in_force")
    fm.append(f'source: "https://www.law.go.kr/LSW/lsInfoP.do?lsiSeq={mst}"')
    fm.append(f"retrieved: {today}")
    fm.append("---")

    lines = fm + ["", f"# {title}", ""]

    arts = root.find("조문")
    units = arts.findall("조문단위") if arts is not None else []
    present = []
    for u in units:
        if (u.findtext("조문여부") or "").strip() == "전문":
            k = unit_kind(node_text(u.find("조문내용")))
            if k and k not in present:
                present.append(k)
    present = [k for k in UNIT_ORDER if k in present]
    level_of = {k: i + 2 for i, k in enumerate(present)}
    art_level = len(present) + 2
    n_art = 0
    for u in units:
        if (u.findtext("조문여부") or "").strip() == "전문":
            t = node_text(u.find("조문내용")).strip()
            if not t:
                continue
            k = unit_kind(t)
            if k:
                lines.extend(heading(level_of[k], t))
            elif (len(t) <= 20 and "\n" not in t and not t.endswith(".")
                  and not re.fullmatch(r"\d{4}\s*년.*일", t)):
                lines.extend(heading(2, t))
            else:
                lines.extend(render_block(t))
                lines.append("")
        else:
            n_art += 1
            render_article(u, art_level, lines)

    # 부칙 (addenda)
    adds = root.findall("부칙/부칙단위")
    if adds:
        lines.extend(heading(2, "부칙"))
        for a in adds:
            t = node_text(a.find("부칙내용")).strip("\n")
            parts = t.split("\n", 1)
            lines.extend(heading(3, parts[0].strip() or "부칙"))
            if len(parts) > 1 and parts[1].strip():
                lines.extend(render_block(parts[1]))
                lines.append("")

    # 별표/서식 (annexed tables and forms)
    tabs = root.findall("별표/별표단위")
    if tabs:
        lines.extend(heading(2, "별표 · 서식"))
        for b in tabs:
            kindb = (b.findtext("별표구분") or "별표").strip()
            no = (b.findtext("별표번호") or "").lstrip("0") or "0"
            br = (b.findtext("별표가지번호") or "").lstrip("0")
            lab = (f"[{kindb} {no}" + (f"의{br}" if br else "") + "]") if no != "0" else f"[{kindb}]"
            bt = node_text(b.find("별표제목")).strip()
            lines.extend(heading(3, f"{lab} {bt}".strip()))
            links = []
            for tag, nm in (("별표서식PDF파일링크", "PDF"), ("별표서식파일링크", "HWP"),
                            ("별표서식이미지파일링크", "image")):
                u = (b.findtext(tag) or "").strip()
                if u:
                    links.append(f"[{nm}]({fix_url(u)})")
            if links:
                lines.append("Official file: " + " · ".join(links))
                lines.append("")
            body = node_text(b.find("별표내용"))
            if body.strip():
                bl = [l.rstrip() for l in body.replace("\r", "").split("\n")]
                while bl and not bl[-1].strip():
                    bl.pop()
                while bl and not bl[0].strip():
                    bl.pop(0)
                lines.append("```text")
                lines.extend(l.replace("```", "ˋˋˋ") for l in bl)
                lines.append("```")
                lines.append("")

    while lines and lines[-1] == "":
        lines.pop()
    text = "\n".join(lines) + "\n"
    path = os.path.join(out_root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return rel, dirs[0], n_art, len(text.encode())


def load_list(raw):
    info = {}
    for p in sorted(glob.glob(os.path.join(raw, "list", "page-*.xml"))):
        for l in etree.parse(p).getroot().findall("law"):
            info[l.findtext("법령일련번호").strip()] = {
                "kind": (l.findtext("법령구분명") or "").strip(),
                "ministry": (l.findtext("소관부처명") or "").strip(),
            }
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=DEFAULT_RAW)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--only", nargs="*")
    a = ap.parse_args()
    today = datetime.date.today().isoformat()
    listinfo = load_list(a.raw)
    files = sorted(glob.glob(os.path.join(a.raw, "law", "*", "*.xml")))
    if a.only:
        files = [f for f in files if os.path.basename(f)[:-4] in a.only]
    else:
        for d in CATEGORY_DIRS:
            shutil.rmtree(os.path.join(a.out, d), ignore_errors=True)
    counts, seen, big = {}, {}, []
    for f in files:
        mst = os.path.basename(f)[:-4]
        if listinfo and mst not in listinfo:
            continue
        try:
            rel, cat, n, size = convert(f, a.out, today, listinfo)
        except Exception as e:
            print(f"ERROR {f}: {e}", file=sys.stderr)
            continue
        if rel in seen:
            print(f"WARNING duplicate path {rel} ({seen[rel]} / {mst})", file=sys.stderr)
        seen[rel] = mst
        counts[cat] = counts.get(cat, 0) + 1
        if size > 40_000_000:
            big.append((rel, size))
    print(counts, "total", sum(counts.values()))
    for b in big:
        print("BIG", b)


if __name__ == "__main__":
    main()
