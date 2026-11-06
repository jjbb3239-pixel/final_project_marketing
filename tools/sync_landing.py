#!/usr/bin/env python3
"""랜딩페이지 소재 반영과 빌드. 두 단계로 나뉨 (여러 명이 동시에 작업해도 Git이 엉키지 않게).

    python3 tools/sync_landing.py pull           # 드라이브 → 저장소 (문구 스냅샷, 이미지, UTM). 드라이브 담당 1명만
    python3 tools/sync_landing.py pull --dry     # pull 결과만 미리 보기
    python3 tools/sync_landing.py build          # 저장소 → 사이트 파일 (03_landing_page/dist). Vercel도 배포 때 이걸 실행
    python3 tools/sync_landing.py build --check  # 템플릿에 문제가 없는지만 확인

Git에 올리는 것 (사람이 고치는 원본):
    03_landing_page/landing.template.html      디자인·구조
    03_landing_page/content/copy.csv           문구 (pull 이 드라이브에서 복사)
    03_landing_page/content/images.json        이미지 목록 (pull 이 작성)
    03_landing_page/content/qa-copy.csv        qa-preview 용 샘플 문구
    03_landing_page/assets/*.webp              이미지 (pull 이 변환)
Git에 올리지 않는 것 (build 결과물, .gitignore):
    03_landing_page/dist/                      index.html, qa-preview.html, sitemap.xml + 정적 파일 복사본
"""
import csv, datetime, html, json, os, re, shutil, sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "tools/config.json").read_text(encoding="utf-8"))
DRIVE = Path(os.environ.get("SYNC_DRIVE_ROOT", CFG["drive_root"]))  # 테스트 시 다른 폴더 지정
LANDING = ROOT / CFG["landing_dir"]
CONTENT = LANDING / "content"
IMG_EXT = {".jpg", ".jpeg", ".png", ".webp"}
TODAY = datetime.date.today()


# ---------- 문구 ----------

def read_copy(path):
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
    # 바이럴(자체 운영 블로그·SNS): 채널마다 고정 링크 1개, 글별 구분 없음
    v = u.get("viral")
    for ch in (v or {}).get("channels", []):
        params = {"utm_source": ch["utm_source"], "utm_medium": v["utm_medium"], "utm_campaign": v["campaign"]}
        rows.append({"차수": "상시", "채널": ch["name"], "소재": "바이럴", "소재유형": "바이럴", **params,
                     "광고 URL": utm_url(CFG["landing_url"], params),
                     "CTA Full URL": utm_url(CFG["cta_base"], params)})
    return rows, skipped


def write_csv(path, rows):
    cols = ["차수", "채널", "소재", "소재유형", "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "광고 URL", "CTA Full URL"]
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


# ---------- 페이지 조립 ----------

def build_page(template, copy, images):
    """템플릿 + 문구 + 이미지 목록 → 완성 HTML."""
    values = {k: render(k, v) for k, v in copy.items() if not k.startswith("seo.")}
    for k in ("hero.cta", "apply.cta"):  # 버튼은 줄바꿈 없이
        if k in copy:
            values[k] = html.escape(" ".join(copy[k].split()))
    og_image = None
    for im in images:
        if im.get("og"):
            og_image = im
            continue
        load = 'fetchpriority="high"' if im.get("priority") else 'loading="lazy"'
        values[im["slot"]] = f'<img class="slot-img" src="{im["path"]}" width="{im["w"]}" height="{im["h"]}" alt="{html.escape(im["alt"])}" {load} decoding="async">'

    page, changed = fill(template, values)
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
        page = re.sub(r"<!-- 공유 이미지 준비되면 주석 해제[^\n]*\n(.*?)\n\s*-->", lambda m: m.group(1), page, count=1, flags=re.S)
        page = page.replace(CFG["landing_url"] + "assets/og.jpg", CFG["landing_url"] + og_image["path"])
        page = page.replace('og:image:width" content="1200"', f'og:image:width" content="{og_image["w"]}"')
        page = page.replace('og:image:height" content="630"', f'og:image:height" content="{og_image["h"]}"')
        changed.append("og.image")

    u = CFG["utm"]; d = u["cta_default"]
    cta_url = utm_url(CFG["cta_base"], {"utm_source": d["utm_source"], "utm_medium": d["utm_medium"], "utm_campaign": u["campaign"], "utm_content": d["utm_content"]})
    page = page.replace(f'href="{CFG["cta_base"]}"', f'href="{html.escape(cta_url)}"')
    page = re.sub(r'<time data-build="updated" datetime="[^"]*">[^<]*</time>',
                  f'<time data-build="updated" datetime="{TODAY}">{TODAY.year}년 {TODAY.month}월 {TODAY.day}일</time>', page)
    empty = sorted({s for s, *_ in SlotFinder(template).slots if s not in values})
    return page, changed, empty, cta_url


def qa_version(page):
    """점검용: 추적(GTM·Clarity) 끄고 검색 노출 막기."""
    page = re.sub(r"(GTM_ID:\s*')[^']*'", r"\g<1>XXXXXXX'", page)
    page = re.sub(r"(CLARITY_ID:\s*')[^']*'", r"\g<1>XXXXXXXXXX'", page)
    return page.replace('<meta name="robots" content="index, follow, max-image-preview:large">', '<meta name="robots" content="noindex, nofollow">')


def read_images(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


# ---------- 실행 ----------

SOURCE_ONLY = {"landing.template.html", "content", "dist", "README.md", "vercel.json", ".vercelignore"}


def cmd_build(argv):
    """저장소의 원본으로 사이트 파일을 만듦. 드라이브·Pillow 필요 없음 (Vercel 빌드에서도 실행)."""
    out = LANDING / "dist"
    template = (LANDING / "landing.template.html").read_text(encoding="utf-8")
    copy, images = read_copy(CONTENT / "copy.csv"), read_images(CONTENT / "images.json")
    page, changed, empty, cta_url = build_page(template, copy, images)
    qa_page, *_ = build_page(template, read_copy(CONTENT / "qa-copy.csv"), read_images(CONTENT / "qa-images.json"))
    print(f"[빌드] 채워진 칸 {len(changed)}개, 비어 있는 칸 {len(empty)}개: {', '.join(empty) or '없음'}")
    print(f"[빌드] CTA 기본 링크: {cta_url}")
    if "--check" in argv:
        print("(확인만 했습니다)")
        return
    if out.exists():
        shutil.rmtree(out)
    out.mkdir()
    for item in LANDING.iterdir():  # 정적 파일 복사 (assets, robots.txt, wireframe 등)
        if item.name in SOURCE_ONLY or item.name.startswith("."):
            continue
        (shutil.copytree if item.is_dir() else shutil.copy2)(item, out / item.name)
    # Publish the merged landing at the production homepage as well as /wireframe/.
    shutil.copy2(out / "wireframe" / "index.html", out / "index.html")
    (out / "qa-preview.html").write_text(qa_version(qa_page), encoding="utf-8")
    blog_dir = out / "wireframe" / "blog"
    if blog_dir.is_dir():
        bootstrap = (blog_dir / "tracking-head.inc").read_text(encoding="utf-8")
        marker = "<!-- Blog analytics: keep the team's existing Meta and Ads tags inactive on these pages. -->"
        for article in blog_dir.rglob("*.html"):
            content = article.read_text(encoding="utf-8")
            if marker in content:
                if (content.count(marker) != 1 or content.count('/wireframe/blog/tracking.js') != 1
                        or "'gtm.blocklist': ['html', 'awct', 'gclidw']" not in content
                        or content.find(marker) > content.find('</head>')):
                    raise ValueError(f"Invalid blog tracking setup: {article.name}")
                continue
            if ('googletagmanager.com/gtm.js' in content or 'googletagmanager.com/gtag/js' in content
                    or '/wireframe/blog/tracking.js' in content or content.count('</head>') != 1):
                raise ValueError(f"Check existing blog tracking or head element: {article.name}")
            article.write_text(content.replace('</head>', bootstrap + '\n</head>', 1), encoding="utf-8")
    blog_urls = [f'{CFG["landing_url"].rstrip("/")}/wireframe/blog/{p.relative_to(blog_dir).as_posix()}'
                 for p in sorted(blog_dir.rglob("*.html"))] if blog_dir.is_dir() else []
    sitemap_entries = [f'  <url><loc>{html.escape(CFG["landing_url"])}</loc><lastmod>{TODAY}</lastmod></url>']
    sitemap_entries += [f'  <url><loc>{html.escape(url)}</loc></url>' for url in blog_urls]
    (out / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + '\n'.join(sitemap_entries) + '\n</urlset>\n', encoding="utf-8")
    print(f"[빌드] 완료: {out.relative_to(ROOT)}/ (index.html, qa-preview.html, sitemap.xml + 정적 파일)")


def cmd_pull(argv):
    """드라이브의 문구·이미지를 저장소로 가져오고 소재별 UTM을 만듦. 드라이브 담당 1명만 실행."""
    write = "--dry" not in argv
    if not DRIVE.exists():
        sys.exit(f"드라이브 폴더가 없습니다: {DRIVE}\nWSL에서 'mount -t drvfs G: /mnt/g' 후 다시 실행하세요.")
    src = DRIVE / "랜딩/copy.csv"
    images = []
    for name, p in find_images().items():
        spec = CFG["image_slots"][name]
        path, w, h = convert_image(p, name, spec["width"], write)
        images.append({"slot": spec.get("slot"), "path": path, "w": w, "h": h, "alt": spec.get("alt", ""),
                       "priority": bool(spec.get("priority")), "og": bool(spec.get("og"))})
    rows, skipped = build_utm_rows()
    copy = read_copy(src)
    print(f"[pull] 문구 {len(copy)}칸, 이미지 {len(images)}개: {', '.join(i['path'] for i in images) or '없음'}")
    print(f"[UTM] 소재 {len(rows)}개" + (f", 파일명 규칙 안 맞아 건너뜀: {', '.join(skipped)}" if skipped else ""))
    for r in rows:
        print(f"  {r['차수']} {r['채널']} {r['소재']}\n    광고 URL : {r['광고 URL']}")
    if not write:
        print("\n(미리보기만 했습니다. 반영하려면 --dry 없이 실행)")
        return
    CONTENT.mkdir(exist_ok=True)
    if src.exists():
        shutil.copyfile(src, CONTENT / "copy.csv")
    (CONTENT / "images.json").write_text(json.dumps(images, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    write_csv(ROOT / "06_ads_tracking/utm.csv", rows)
    write_csv(DRIVE / "광고소재/utm_목록.csv", rows)
    print("\n반영 완료: content/copy.csv, content/images.json, assets/*.webp, 06_ads_tracking/utm.csv, 드라이브 utm_목록.csv")
    print("다음: python3 tools/sync_landing.py build 로 확인 → git add 03_landing_page/content 03_landing_page/assets 06_ads_tracking/utm.csv → 커밋·푸시")


def main():
    argv = sys.argv[1:]
    cmd = argv[0] if argv and not argv[0].startswith("-") else ""
    if cmd == "build":
        cmd_build(argv)
    elif cmd == "pull":
        cmd_pull(argv)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
