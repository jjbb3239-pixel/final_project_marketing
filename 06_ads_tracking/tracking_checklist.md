# 전환 추적 체크리스트

## 퍼널
광고 노출 → 광고 클릭 → 랜딩페이지 방문 → **CTA 클릭 (핵심 전환)** → 라이브클래스 상세페이지 이동

## 설치
GTM 설정은 `gtm/petitrich_gtm_import.json`으로 가져오기(병합) 가능.
ID는 `03_landing_page/index.html` 상단 `window.TRACKING` 두 값만 바꾸면 됩니다. `XXX`가 남아 있으면 해당 태그는 로드되지 않습니다.
- [x] GTM 컨테이너 ID 입력 (`GTM_ID` = GTM-PLPB9NFW, 계정 "쁘띠리치")
- [x] 메타 픽셀 (ID 1664723555062468, "Final-project 픽셀") — **11/4부터 GTM에서 로드** (`Meta 픽셀 - 기본 코드(PageView)` 모든 페이지, `Meta 픽셀 - Lead (CTA 클릭)` cta_click 트리거, content_name=cta_{위치}). 랜딩 코드에서는 제거함 (`gtm/petitrich_gtm_meta_pixel.json`)
- [ ] ⚠️ 랜딩 코드에 메타 픽셀을 다시 넣지 않기 (GTM과 중복 집계)
- [x] GA4 구성 태그 (GTM) — `GA4 - Google 태그`, G-VJPV0LRV8K (스트림 PetitRich Landing Web). GTM 버전 2 게시 (11/4)
- [x] GTM 맞춤 이벤트 트리거 `cta_click` → GA4 이벤트 `cta_click` (매개변수 `cta_location`: header(PC 상단) / hero / apply / sticky(모바일 하단))
- [x] GTM 맞춤 이벤트 트리거 `section_view` → GA4 이벤트 `section_view` (매개변수 `section_name`) — 이탈 구간 분석용
- [ ] GA4에서 `cta_click` 을 주요 이벤트(전환)로 표시
- [ ] Microsoft Clarity(무료 히트맵·세션 녹화) 프로젝트 생성 → ID를 `index.html` 상단 `CLARITY_ID`에 입력. 소재별(`utm_content`)로 나눠 볼 수 있게 태그가 자동으로 붙음
- 픽셀 CTA 클릭 이벤트: 표준 이벤트 `Lead` (GTM에서 전송, 이전과 같은 이름·값) → Meta 광고 전환 최적화 이벤트로 선택

## 구글 애즈 전환 (계정 537-797-0294)
- [ ] GA4 속성 ↔ 구글 애즈 연결 (GA4 관리 > 제품 링크 > Google Ads 링크, 팀 GA4 편집자 권한 필요)
- [x] GTM에 `전환 링커` 태그 (모든 페이지) — 광고 클릭 ID(gclid) 저장
- [x] (11/4 생성: `CTA 클릭 (라이브클래스 이동)`, 카테고리 외부 클릭, 기본 액션, 1회, AW-18554881482 / 라벨 XIj3CO_42bEdEMqL1I9F) 구글 애즈 > 목표 > 전환 > 새 전환 액션 > 웹사이트 > 수동: 이름 `CTA 클릭`, 카테고리 `잠재고객 페이지 조회`(또는 기타), 횟수 `1회`
- [x] (GTM 버전 3 게시, `gtm/petitrich_gtm_ads_conversion.json`) GTM에 `Google Ads 전환 추적` 태그 (전환 ID·라벨은 위에서 받은 값) + 트리거: 맞춤 이벤트 `cta_click` (4개 CTA 모두 같은 이벤트라 CTA를 늘려도 그대로 잡힘)
- [ ] ⚠️ GA4 `cta_click`도 애즈로 가져오면 **보조** 전환으로 두기 (기본 전환 2개면 이중 집계)
- 광고 URL: `06_ads_tracking/utm.csv`의 Google 행 (`utm_term={keyword}`는 구글이 실제 키워드로 바꿔 줌). 랜딩 코드가 UTM을 CTA 링크로 넘겨 주므로 라이브클래스에도 google로 기록됨
- 자동 태그 추가(gclid)는 켜 둔 채로 유지

## 바이럴 (자체 운영 블로그·SNS)
링크는 `06_ads_tracking/utm.csv`의 `상시` 행 (설정: `tools/config.json` > `utm.viral`). 채널마다 고정 링크 1개, 글별 구분 없음.
`utm_medium=social`이라 GA4 기본 채널에서 **Organic Social**로 묶임 (`viral` 같은 임의 값은 Unassigned로 빠지므로 바꾸지 말 것).
- [ ] GA4 관리 > 맞춤 정의 > 맞춤 측정기준 만들기: 이름 `CTA 위치`, 범위 `이벤트`, 매개변수 `cta_location` (등록 이후 데이터부터 보임)
- [ ] GA4 관리 > 이벤트 > `cta_click` 주요 이벤트로 표시 (위 설치 항목과 같음)
- [ ] GA4 관리 > 데이터 스트림 > PetitRich Landing Web > 태그 설정 구성 > 내부 트래픽 정의: 팀 IP 등록 (`traffic_type=internal`)
- [ ] GA4 관리 > 데이터 필터 > Internal Traffic 필터를 `테스트` → 확인 후 `활성`으로 변경 (활성화 이후 데이터에만 적용, 되돌릴 수 없음)
- [ ] GA4 탐색 > 자유 형식 `바이럴 성과`: 측정기준 `세션 소스/매체`·`세션 캠페인`·`CTA 위치`, 측정항목 `활성 사용자`·`세션`·`이벤트 수`·`주요 이벤트`, 필터 `세션 캠페인 = organic_viral`. CTA만 볼 땐 `이벤트 이름 = cta_click` 필터 추가
- [ ] 바이럴 링크 4개로 직접 접속 → GA4 실시간에서 소스(naver_blog 등) 확인 (내부 트래픽 필터 활성 전에 테스트)

## 검증 (광고 집행 전)
- [ ] (11/4 테스트 클릭 시 googleadservices 전환 요청 200 확인. 애즈 화면 상태 변경은 수 시간 걸림) 구글 애즈 > 전환 액션 상태가 `기록 중` 또는 `최근 전환 없음`으로 바뀌는지 (GTM 게시 후 CTA 직접 클릭해 테스트)
- [ ] Google 광고 URL로 접속 → CTA 링크 주소에 `utm_source=google` 들어가는지
- [ ] GTM 미리보기에서 CTA 클릭 태그 발동
- [x] GA4 실시간에서 `cta_click` 수신 확인 (11/4, 테스트 UTM utm_source=test)
- [ ] Meta Pixel Helper / 이벤트 관리자에서 확인
- [x] UTM 붙은 URL로 접속 시 CTA 링크로 UTM 전달 확인 (11/4). GA4 소스/매체 보고서는 하루 뒤 확인 — GA4 소스/매체 정상 수집
- [ ] CTA 링크 정상 이동

## 11/10 추가 (랜딩·블로그 코드)
- UTM 없이 랜딩에 들어온 방문(블로그 경유·직접 방문)의 강의 CTA에는 `utm_source=landing&utm_medium=referral&utm_campaign=finalproject&utm_content=no_utm`이 붙음. 광고 UTM이나 gclid·fbclid가 있으면 붙이지 않음
- 블로그에서 강의 사이트로 가는 링크에는 `utm_source=petitrich_blog&utm_medium=referral&utm_campaign=finalproject&utm_content=blog_{글 이름}`이 붙음
- 랜딩의 네이버 카페·유튜브 카드 클릭은 dataLayer 이벤트 `landing_outbound_click`(`cta_location`: cafe / youtube)으로 기록. 전환(`cta_click`)에는 포함되지 않음
- [ ] GTM에 맞춤 이벤트 트리거 `landing_outbound_click` → GA4 이벤트 태그 추가 후 게시 (추가 전에는 GA4에 보이지 않음)
