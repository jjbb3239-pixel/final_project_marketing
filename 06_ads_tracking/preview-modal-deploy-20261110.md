# 무료 1강 프리뷰 모달 배포 기록 (2026-11-10)

## 무엇이 바뀌나
- 랜딩(`03_landing_page/wireframe/index.html`) 히어로에 무료 1강 프리뷰 모달 추가. 진입 0.8초 뒤 자동 노출, 방문당 1회, 음소거 자동재생.
- 영상: `wireframe/assets/hero-preview-20s.mp4`(0.9MB, 1280x720, 19.2초, 빠른 시작 형식), 포스터 `hero-preview-poster.jpg`.
- `layout_version`: `landing-20261106-v3` → **`landing-20261110-v4`** (모달 전후 구분 기준).
- 기존 코드 변경은 2줄뿐: 레이아웃 버전, 노출(`cta_view`) 추적에서 모달 CTA 제외 조건(`:not([data-exposure="off"])`).
- 우하단 "다시 열기" 버튼은 두지 않음(확정본에는 있었으나 제거 결정).
- 푸터 정리: 링크 없이 글자만 있던 이용약관·개인정보처리방침·수강·환불 안내와 사업자정보 확인 링크 삭제. 제공처는 "강의 제공처: 파이어클럽(FIREclub)"만 표기하고 LiveKlass 통신판매중개자 문장은 삭제. 추가 문구: "본 페이지는 방문 분석과 광고 성과 측정을 위해 Google 애널리틱스, Google Ads, Meta 픽셀을 사용합니다." 저작권·투자 유의·운영·문의 줄은 유지.
  - 한계: 개인정보처리방침 페이지와 거부 방법 안내는 없음. 법적 충분성은 확인하지 못했으며, 광고 규모를 키우기 전에 파이어클럽 담당자나 법무 확인 필요. "최종 업데이트: 2026년 11월 4일" 문구는 그대로.

## 이벤트 설계
| 이벤트 | 시점 | 값 |
|---|---|---|
| `cta_click` (기존) | 모달 "무료 1강 전체 보기" 클릭 | `cta_location=preview_modal`, `cta_id=landing_preview_modal`, `destination_type=free_lesson` — **광고 전환은 이 이벤트가 담당** |
| `preview_modal_open` (신규) | 모달 열림 | `page_type`, `layout_version` |
| `preview_cta_click` (신규) | 모달 CTA 클릭 | `preview_watched_pct`(시청률 0~100), `preview_video_ended` — 진단용, **전환·주요 이벤트로 지정 금지**(같은 클릭이 `cta_click`과 이중 집계됨) |
| `preview_modal_close` (신규) | 모달 닫힘 | `preview_close_reason`(`text_link`/`esc`/`back_button`), `preview_watched_pct` |

- 뺀 이벤트: `preview_progress`, `preview_complete`, `preview_unmute`, `preview_replay`.
- 광고 전환 태그(Meta Lead·CTA_FreeClass·CTA_ClassPage, Google Ads 전환)는 정확히 `cta_click`에만 연결돼 있고 `preview_*`에는 연결하지 않음(GTM 미리보기에서 확인).
- 모달이 열려 있는 동안 배경 스크롤이 잠겨 `scroll_depth`·`section_view`가 덜 찍힘. 전후 비교 때 감안.

## GTM
- 컨테이너 `GTM-PLPB9NFW`(계정 6402311479 / 컨테이너 285099722). 게시 후보 작업공간: **`preview-modal-events-min-20261110`**(변경 9건: 트리거 3, 변수 3, GA4 태그 3). 기존 항목 수정 0건.
- 가져오기 파일: `06_ads_tracking/gtm/petitrich_gtm_preview_modal.json`.
- 광고 태그를 일시중지한 임시 검증 작업공간은 모두 삭제함(게시 금지 대상이었음).

## 배포 순서
1. GA4 맞춤 측정기준(이벤트 범위) 3개 등록: `preview_close_reason`, `preview_watched_pct`, `preview_video_ended`. (선택: `preview_watched_pct`를 맞춤 측정항목으로도 등록하면 평균 시청률을 볼 수 있음)
2. **GTM 먼저 게시**(작업공간 `preview-modal-events-min-20261110` → 제출). 코드가 아직 없어서 `preview_*`는 발생하지 않고 기존 동작에 영향 없음.
3. 랜딩 코드 PR 머지 → Vercel 자동 배포. 광고 운영 중이므로 머지 전 팀 채팅에 한 줄 공지(README 규칙). **배포 시각 기록**(`landing-20261110-v4` 시작 시각).
4. 배포 직후 `qa_` UTM으로 확인(실제 소재 UTM 사용 금지). 모달 CTA를 누르면 광고 전환이 실제로 올라가므로 1회만.

## 배포 후 확인
- `qa_` 링크로 모달 노출, 영상 재생, 닫기, CTA 이동.
- GA4 DebugView/실시간: `preview_modal_open`, `preview_modal_close`, `preview_cta_click`, `cta_click`(`cta_location=preview_modal`) 도착. 한 번 클릭에 `cta_click` 1건·`preview_cta_click` 1건인지.
- 대시보드: 총 CTA 클릭에 모달 클릭이 포함되는지, `cta_location=preview_modal` 몫, `layout_version` v3/v4 전후.
- 영상 시작 속도(Vercel에서는 부분 요청 지원), 실제 폰·인스타 앱 안 브라우저 동작.

## 되돌리기
- 코드: PR 되돌리기(revert) → 자동 재배포. 모달만 사라지고 `cta_click`은 기존 그대로.
- GTM: 버전 탭에서 이전 버전을 게시.
- 되돌려도 GA4에 이미 쌓인 `preview_*` 데이터와 `layout_version=v4` 기록은 남음.

## 알려진 한계
- 모달이 클릭 수를 바꾸므로 1차(v3)와 2차(v4)는 같은 조건의 비교가 아님.
- `/wireframe/assets/` 아래 파일은 `vercel.json`의 캐시 규칙(`/assets/`)에 해당되지 않아 재방문 때마다 서버 확인이 한 번 일어남(기존 구조 그대로).
- 유입별 광고 태그 필터링(Meta 유입만 Meta로, 구글 유입만 구글로)은 이번 범위에 없음. 별도 작업.
