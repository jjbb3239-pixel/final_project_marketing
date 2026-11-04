# 랜딩페이지

- **배포:** GitHub `main`에 푸시하면 Vercel(petitrich-landing)이 `python3 ../tools/sync_landing.py build`로 사이트를 만들어 자동 배포. 빌드가 실패하면 직전 사이트가 그대로 유지됨
- **팀원 커밋 배포:** 저장소가 공개(public)라서 팀원 Merge도 Vercel이 바로 배포함 (Vercel은 공개 저장소의 공동 작업을 무료 플랜에서도 허용. 비공개였을 때는 소유자 외 커밋이 "Deployment was blocked"로 막혔음). 예비 장치로 GitHub Actions(`.github/workflows/vercel-deploy-hook.yml`)가 팀원 커밋 때 배포 훅을 한 번 더 호출함 → 같은 커밋이 두 번 배포될 수 있으나 문제 없음. 반영이 안 보이면 Actions 탭 → "Vercel 배포 (팀원 커밋)" → **Run workflow** (쓰기 권한 있는 협업자 누구나 가능, 그 시점의 최신 main을 배포)
- **사이트 파일(`index.html`, `qa-preview.html`, `sitemap.xml`)은 Git에 올리지 않음.** 배포 때마다 `landing.template.html` + `content/`로 새로 만들어짐 (`dist/`, .gitignore)

## 여러 명이 동시에 작업할 때 (엉키지 않게)
**누가 무엇을 고치나**
| 고칠 것 | 파일 | 담당 |
|---|---|---|
| 문구·이미지 | 구글 드라이브 `랜딩소재/` → `pull`로 `content/`, `assets/` 갱신 | 드라이브 담당 1명만 `pull` 실행 |
| 디자인·구조·스크립트 | `landing.template.html` | 누구나 (아래 순서대로) |
| 와이어프레임·블로그 | `wireframe/` | 누구나 |
| 광고·추적 문서 | `06_ads_tracking/` | 누구나 |

**작업 순서 (매번)**
```bash
git switch main && git pull --rebase          # 1. 최신으로
git switch -c 이름-작업내용                     # 2. 내 브랜치 (예: dahun-faq-style)
# 3. 수정 → 확인
python3 tools/sync_landing.py build           #    03_landing_page/dist/index.html 을 브라우저로 열어 확인
git add -A && git commit -m "무엇을 왜 바꿨는지"
git push -u origin 이름-작업내용                # 4. 푸시 → Vercel 미리보기 주소 생성
```
5. GitHub에서 Pull Request 생성 → 미리보기 확인 → **Merge** (Merge 하는 순간 운영 사이트 배포)
- `main`에 직접 푸시하지 않기. 브랜치 → PR → Merge
- PR을 합치기 직전 다른 사람 PR이 먼저 합쳐졌으면, 내 브랜치에서 `git pull --rebase origin main` 후 다시 푸시
- 충돌이 나도 원본 파일끼리만 나므로 해당 줄만 고르면 됨 (자동 생성 파일 충돌은 더 이상 없음)
- 광고 운영 중(1차 11/6~10, 2차 11/10~13)에는 Merge 전에 팀 채팅에 한 줄 알리기

**드라이브 문구·이미지 반영 (담당 1명)**
```bash
python3 tools/sync_landing.py pull --dry   # 바뀔 내용 미리 보기
python3 tools/sync_landing.py pull         # content/, assets/, utm.csv 갱신
python3 tools/sync_landing.py build        # 확인
```
그다음 위 작업 순서대로 브랜치 → PR → Merge

- CTA → 선택한 라이브클래스 상품 상세페이지 연결
- 배포 URL:
- 최종 제출 시 URL + HTML 파일 모두 제출 (HTML 파일은 `python3 tools/sync_landing.py build` 후 `dist/index.html`)

## 구조 (와이어프레임 0~6)
1 히어로 `#hero` · 2 조급함의 정체 `#cause` · 3 실수 `#mistakes` · 4 강의 철학 `#philosophy` · 5 강사 `#instructor` · 6 FAQ+신청 `#apply`
- `class="ph"` = 소재 들어갈 자리(회색 점선). 실제 문구·이미지로 바꾸면 `ph` 제거
- CTA는 `class="cta"` + `data-cta-location` 필수 (추적용). 위치값: hero / apply / sticky(모바일 하단, 히어로를 지나면 나타나고 신청 섹션에서 사라짐)

## 로딩 속도 원칙 (광고 클릭 직후 이탈 방지)
- 외부 폰트·CSS 프레임워크·JS 라이브러리 쓰지 않기 (CSS는 `<style>` 안에)
- 이미지는 `assets/`에 WebP, 가로 1600px 이하, 장당 200KB 이하
- 히어로 이미지만 `fetchpriority="high"`, 나머지는 `loading="lazy"`, 모든 `<img>`에 width/height
- 영상은 직접 올리지 말고 썸네일 + 링크로

## 소재 채울 때 쓰는 스킬 (`~/.claude/skills`)
- `frontend-design` (anthropics/skills): 디자인 업데이트 시 색·서체·레이아웃 토큰을 먼저 정하고 템플릿 느낌 피하기
- `copywriting` (coreyhaines31/marketingskills): 섹션별 문구 작성
- `cro`: 광고 문구와 히어로 문구 일치(message match), 신뢰 요소는 CTA 근처, 버튼은 누르면 무슨 일이 생기는지 말하기
- `conversion-tracking`, `analytics`: GTM 태그 설정·검증
- `seo-page`, `seo-schema`, `seo-geo`, `seo-technical` (AgriciDaniel/claude-seo), `ai-seo`, `schema` (marketingskills): SEO·GEO·AEO 점검

## 디자인 (레퍼런스: Quanta, land-book)
- 무채색 다크, 좁은 자간 헤드라인(Pretendard), 흰 알약 CTA + 화살표, 왼쪽 라벨/오른쪽 내용 2단, 가는 구분선
- 색·폭: `<style>` 맨 위 `:root` 토큰만 바꾸면 전체 반영. 섹션별 스타일은 번호 주석 아래
- HTML 구조(섹션 id, `h1` 1개 + 섹션별 `h2`, `.cta` 버튼, `data-slot`)는 추적·SEO·드라이브 반영에 쓰이니 유지
- 인터랙션
  - 히어로 패널: 빛을 숫자 모자이크(shaders `Ascii`)로 렌더링, 마우스 주변 숫자가 밝아짐. 화면 밖이면 렌더링 멈춤
  - 4번 제목: 스크롤하면 단어 단위로 밝아짐 (동작 줄이기면 처음부터 다 보임)
  - 모바일 하단 CTA: 히어로 CTA를 지나면 나타나고 신청 섹션에서 사라짐
- 터치 기기·WebGPU 미지원·데이터 절약이면 셰이더 대신 CSS 숫자 패턴
- `qa-preview.html`: 샘플 문구로 채운 점검용 페이지 (추적·검색 노출 꺼 둠). 소재가 들어오면 삭제

## SEO / GEO / AEO
- `<head>`: title, description, canonical, OG, `Course` JSON-LD (가격·강의 수 바뀌면 같이 수정)
- 문구는 HTML에 직접 씀 (AI 크롤러는 JS를 실행하지 않음)
- FAQ 확정 후 `FAQPage` JSON-LD 추가, 공유 이미지 준비되면 `og:image` 주석 해제
- `robots.txt`(AI 검색 크롤러 허용), `sitemap.xml`. 업데이트 시 footer와 sitemap 날짜 갱신

## (이전) 빛 효과 시안 (`sian-light.html` → `/sian-light`) — 새 디자인으로 대체됨
- 라이브러리: [shaders](https://shaders.com) 4.0.4 (WebGPU), 무료 컴포넌트만 사용 (프리셋은 Pro라 참고만)
- 페이지 전체가 어두운 남색 톤이고, 빛은 화면에 고정된 배경 캔버스에 그림
- 레이어: `StudioBackground`(조명 바탕) → `Godrays`(빛줄기) → `Blur`로 감싼 `Fog`(마우스가 휘젓는 옅은 안개, 참고: Smokescreen) → `FilmGrain`
- 색은 `:root`의 `--fx-*`, 세기는 파일 하단 로더의 props에서 조절
- 속도: 라이브러리(gzip 약 700KB)는 페이지가 다 뜬 뒤 여유 시간에만 로드. WebGPU 미지원·데이터 절약·느린 회선이면 CSS 그라디언트만 보임
- 동작 줄이기 설정이면 움직임·마우스 반응 없이 멈춘 빛만 그림
- 터치 기기(모바일)는 셰이더를 불러오지 않고 화면 고정 CSS 빛 배경(`.page-bg`)만 보여 줌 (데이터·배터리 절약, iOS 고정 배경 문제 회피)
- 시안 페이지는 추적·검색 노출 꺼 둠. 채택하면 `landing.template.html`에 CSS·로더만 옮기기

## shaders MCP
- 레포 루트 `.mcp.json`에 등록됨 (`npx shaders@latest install-mcp`로 생성). 다음 Claude Code 세션에서 처음 연결할 때 shaders.com 무료 계정 로그인 필요
- 프리셋 검색은 무료, 프리셋 설치는 Pro. 이 프로젝트는 무료 컴포넌트만 씀
