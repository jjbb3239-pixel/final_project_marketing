#!/usr/bin/env python3
"""구글 드라이브 소재 → 랜딩페이지 반영 + 소재별 UTM 생성.

    python3 tools/sync_landing.py          # 바뀔 내용만 보여 줌 (파일 안 바꿈)
    python3 tools/sync_landing.py --write  # 실제로 index.html, 이미지, UTM 파일 갱신

입력 (드라이브, config.json 의 drive_root):
    랜딩/copy.csv            slot,내용,설명
    랜딩/images/<이름>.*     hero / instructor / og
    광고소재/<N차>/<파일>    N팀_N차_소재유형_번호[_카드].ext
출력:
    03_landing_page/index.html        (landing.template.html 을 채운 결과)
    03_landing_page/assets/*.webp
    06_ads_tracking/utm.csv  +  드라이브 광고소재/utm_목록.csv
"""
import csv, datetime, html, json, os, re, sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "tools/config.json").read_text(encoding="utf-8"))
DRIVE = Path(os.environ.get("SYNC_DRIVE_ROOT", CFG["drive_root"]))  # 테스트 시 다른 폴더 지정
LANDING = ROOT / CFG["landing_dir"]
IMG_EXT = {".jpg", ".jpeg", ".png", ".webp"}
TODAY = datetime.date.today()


# ---------- 문구 ----------

def read_copy():
    path = DRIVE / "랜딩/copy.csv"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        return {r["slot"].strip(): r["내용"].strip() for r in csv.DictReader(f) if r.get("내용", "").strip()}


def lines(text):
    return [html.escape(l.strip()) for l in text.splitlines() if l.strip()]


def render(slot, text):
    """slot 이름 끝부분으로 표시 형태를 정함."""
    ls = lines(text)
    kind = slot.split(".")[-1]
    if kind.startswith("card"):
        head, body = ls[0], ls[1:]
        return f"<h3>{head}</h3>" + "".join(f"<p>{l}</p>" for l in body)
    if kind in ("rush", "calm", "bio", "donts"):
        return "<ul>" + "".join(f"<li>{l}</li>" for l in ls) + "</ul>"
    if kind == "a":
        return "".join(f"<p>{l}</p>" for l in ls)
    return "<br>".join(ls)


# ---------- 이미지 ----------

def find_images():
    d = DRIVE / "랜딩/images"
    found = {}
    if d.exists():
        for p in d.iterdir():
            if p.suffix.lower() in IMG_EXT and p.stem in CFG["image_slots"]:
                found[p.stem] = p
    return found


def convert_image(src, name, width, write):
    """WebP로 변환, 가로 width 이하, 200KB 이하가 되도록 품질 조절."""
    from PIL import Image, ImageOps
    out = LANDING / "assets" / f"{name}.webp"
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    if write:
        out.parent.mkdir(exist_ok=True)
        for q in (82, 75, 68, 60, 52):
            im.save(out, "WEBP", quality=q, method=6)
            if out.stat().st_size <= 200_000:
                break
    return f"assets/{name}.webp", im.width, im.height


# ---------- HTML slot 치환 ----------

class SlotFinder(HTMLParser):
    """data-slot 요소의 (시작태그 시작, 시작태그 끝, 종료태그 시작, 종료태그 끝) 위치를 찾음."""
    VOID = {"br", "img", "meta", "link", "input", "hr", "source"}

    def __init__(self, text):
        super().__init__(convert_charrefs=False)
        self.text, self.stack, self.slots = text, [], []
        self.line_starts = [0] + [m.end() for m in re.finditer("\n", text)]
        self.feed(text)

    def pos(self):
        line, col = self.getpos()
        return self.line_starts[line - 1] + col

    def handle_starttag(self, tag, attrs):
        if tag in self.VOID:
            return
        start = self.pos()
        end = start + len(self.get_starttag_text())
        self.stack.append((tag, dict(attrs).get("data-slot"), start, end))

    def handle_endtag(self, tag):
        while self.stack:
            t, slot, s, e = self.stack.pop()
            if t == tag:
                if slot:
                    es = self.pos()
                    self.slots.append((slot, s, e, es, es + len(f"</{tag}>")))
                return


def drop_ph(start_tag):
    start_tag = re.sub(r'class="([^"]*)"', lambda m: 'class="%s"' % " ".join(c for c in m.group(1).split() if c != "ph"), start_tag)
    return start_tag.replace(' class=""', "")


def fill(template, values):
    found = SlotFinder(template).slots
    out, changed = template, []
    for slot, s, e, es, ee in sorted(found, key=lambda x: -x[1]):
        if slot not in values:
            continue
        new_start = drop_ph(template[s:e])
        out = out[:s] + new_start + values[slot] + out[es:]
        changed.append(slot)
    return out, sorted(set(changed))


# ---------- UTM ----------

NAME_RE = re.compile(r"^(?P<team>\d+)(?P<unit>조|팀)_(?P<round>\d+)차_(?P<type>[^_]+)_(?P<num>\d+)(?:_(?P<card>\d+))?$")
RESERVED = {"%": "%25", "&": "%26", "=": "%3D", "#": "%23", "?": "%3F", "+": "%2B", " ": "%20"}


def enc(v):
    """URL 문법에 쓰이는 문자만 바꾸고 한글은 그대로 둠 (소재 이름을 읽을 수 있게)."""
    return "".join(RESERVED.get(ch, ch) for ch in str(v))


def utm_url(base, params):
    return base + ("&" if "?" in base else "?") + "&".join(f"{k}={enc(v)}" for k, v in params.items())


def build_utm_rows():
    u = CFG["utm"]
    rows, skipped = [], []
    seen = set()
    for rdir in sorted((DRIVE / "광고소재").glob("*차")):
        for p in sorted(rdir.iterdir()):
            if p.name.startswith(".") or p.suffix.lower() in (".ini", ".csv"):
                continue
            m = NAME_RE.match(p.stem)
            if not m:
                skipped.append(p.name)
                continue
            creative = f"{m['team']}{m['unit']}_{m['round']}차_{m['type']}_{m['num']}"  # 캐러셀 카드는 소재 하나로 묶음
            if any(ch in RESERVED for ch in creative):
                skipped.append(f"{p.name} (공백·특수문자)")
                continue
            if creative in seen:
                continue
            seen.add(creative)
            ch = u["channels"]["meta"]
            params = {**ch, "utm_campaign": u["campaign"], "utm_content": creative}
            rows.append({"차수": f"{m['round']}차", "채널": "Meta", "소재": creative, "소재유형": m["type"], **params,
                         "광고 URL": utm_url(CFG["landing_url"], params),
                         "CTA Full URL": utm_url(CFG["cta_base"], params)})
    for ad in u.get("google_ads", []):
        ch = u["channels"]["google"]
        params = {**ch, "utm_campaign": u["campaign"], "utm_content": ad["content"]}
        if ad.get("term"):
            params["utm_term"] = ad["term"]
        rows.append({"차수": ad.get("round", ""), "채널": "Google", "소재": ad["content"], "소재유형": "검색광고", **params,
                     "광고 URL": utm_url(CFG["landing_url"], params),
                     "CTA Full URL": utm_url(CFG["cta_base"], params)})
    return rows, skipped


def write_csv(path, rows):
    cols = ["차수", "채널", "소재", "소재유형", "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "광고 URL", "CTA Full URL"]
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


# ---------- 실행 ----------

def main():
    write = "--write" in sys.argv
    if not DRIVE.exists():
        sys.exit(f"드라이브 폴더가 없습니다: {DRIVE}\nWSL에서 'mount -t drvfs G: /mnt/g' 후 다시 실행하세요.")

    copy = read_copy()
    values = {k: render(k, v) for k, v in copy.items() if not k.startswith("seo.")}
    for k in ("hero.cta", "apply.cta"):  # 버튼은 줄바꿈 없이
        if k in copy:
            values[k] = html.escape(" ".join(copy[k].split()))

    template = (LANDING / "landing.template.html").read_text(encoding="utf-8")
    page = template
    og_image = None
    for name, src in find_images().items():
        spec = CFG["image_slots"][name]
        path, w, h = convert_image(src, name, spec["width"], write)
        if spec.get("og"):
            og_image = (path, w, h)
            continue
        load = 'fetchpriority="high"' if spec.get("priority") else 'loading="lazy"'
        values[spec["slot"]] = f'<img class="slot-img" src="{path}" width="{w}" height="{h}" alt="{html.escape(spec["alt"])}" {load} decoding="async">'

    page, changed = fill(page, values)

    # SEO 문구, 공유 이미지, CTA 기본 UTM, 업데이트 날짜
    if "seo.title" in copy:
        t = html.escape(copy["seo.title"])
        page = re.sub(r"<title>.*?</title>", f"<title>{t}</title>", page, count=1)
        page = re.sub(r'(<meta property="og:title" content=")[^"]*', rf"\g<1>{t}", page, count=1)
        changed.append("seo.title")
    if "seo.description" in copy:
        d = html.escape(copy["seo.description"])
        page = re.sub(r'(<meta name="description" content=")[^"]*', rf"\g<1>{d}", page, count=1)
        page = re.sub(r'(<meta property="og:description" content=")[^"]*', rf"\g<1>{d}", page, count=1)
        changed.append("seo.description")
    if og_image:
        path, w, h = og_image
        page = re.sub(r"<!-- 공유 이미지 준비되면 주석 해제[^\n]*\n(.*?)\n\s*-->",
                      lambda m: m.group(1), page, count=1, flags=re.S)
        page = page.replace(CFG["landing_url"] + "assets/og.jpg", CFG["landing_url"] + path)
        page = page.replace('og:image:width" content="1200"', f'og:image:width" content="{w}"')
        page = page.replace('og:image:height" content="630"', f'og:image:height" content="{h}"')
        changed.append("og.image")

    u = CFG["utm"]
    d = u["cta_default"]
    cta_url = utm_url(CFG["cta_base"], {"utm_source": d["utm_source"], "utm_medium": d["utm_medium"], "utm_campaign": u["campaign"], "utm_content": d["utm_content"]})
    page = page.replace(f'href="{CFG["cta_base"]}"', f'href="{html.escape(cta_url)}"')

    old = (LANDING / "index.html").read_text(encoding="utf-8")
    stamp = re.compile(r'<time data-build="updated" datetime="[^"]*">[^<]*</time>')
    if stamp.sub("", page) == stamp.sub("", old):  # 내용이 같으면 날짜도 그대로
        page = old
    else:
        page = stamp.sub(f'<time data-build="updated" datetime="{TODAY}">{TODAY.year}년 {TODAY.month}월 {TODAY.day}일</time>', page)

    rows, skipped = build_utm_rows()

    # ---- 결과 보고 ----
    empty = [s for s, *_ in SlotFinder(template).slots if s not in values]
    print(f"[랜딩] 채워진 칸 {len(changed)}개: {', '.join(changed) or '없음'}")
    print(f"[랜딩] 비어 있는 칸 {len(set(empty))}개: {', '.join(sorted(set(empty)))}")
    print(f"[랜딩] index.html {'변경 있음' if page != old else '변경 없음'}")
    print(f"[UTM] 소재 {len(rows)}개" + (f", 파일명 규칙 안 맞아 건너뜀: {', '.join(skipped)}" if skipped else ""))
    for r in rows:
        print(f"  {r['차수']} {r['채널']} {r['소재']}\n    광고 URL : {r['광고 URL']}")
    print(f"[CTA] 기본 링크: {cta_url}")

    if not write:
        print("\n(미리보기만 했습니다. 반영하려면 --write)")
        return
    (LANDING / "index.html").write_text(page, encoding="utf-8")
    sm = LANDING / "sitemap.xml"
    sm.write_text(re.sub(r"<lastmod>[^<]*</lastmod>", f"<lastmod>{TODAY}</lastmod>", sm.read_text(encoding="utf-8")), encoding="utf-8")
    write_csv(ROOT / "06_ads_tracking/utm.csv", rows)
    write_csv(DRIVE / "광고소재/utm_목록.csv", rows)
    print("\n반영 완료: index.html, sitemap.xml, 06_ads_tracking/utm.csv, 드라이브 광고소재/utm_목록.csv")


if __name__ == "__main__":
    main()
