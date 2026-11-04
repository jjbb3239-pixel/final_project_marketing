# 전환 추적 체크리스트

## 퍼널
광고 노출 → 광고 클릭 → 랜딩페이지 방문 → **CTA 클릭 (핵심 전환)** → 라이브클래스 상세페이지 이동

## 설치
ID는 `03_landing_page/index.html` 상단 `window.TRACKING` 두 값만 바꾸면 됩니다. `XXX`가 남아 있으면 해당 태그는 로드되지 않습니다.
- [x] GTM 컨테이너 ID 입력 (`GTM_ID` = GTM-PLPB9NFW, 계정 "쁘띠리치")
- [x] 메타 픽셀 ID 입력 (`META_PIXEL_ID` = 1664723555062468, "Final-project 픽셀") — 페이지에 직접 설치됨, PageView 자동
- [ ] ⚠️ GTM 안에 메타 픽셀 태그를 또 만들지 않기 (중복 집계)
- [ ] GA4 구성 태그 (GTM)
- [ ] GTM 맞춤 이벤트 트리거 `cta_click` → GA4 이벤트 `cta_click` (매개변수 `cta_location`: header(PC 상단) / hero / apply / sticky(모바일 하단))
- [ ] GTM 맞춤 이벤트 트리거 `section_view` → GA4 이벤트 `section_view` (매개변수 `section_name`) — 이탈 구간 분석용
- [ ] GA4에서 `cta_click` 을 주요 이벤트(전환)로 표시
- [ ] Microsoft Clarity(무료 히트맵·세션 녹화) 프로젝트 생성 → ID를 `index.html` 상단 `CLARITY_ID`에 입력. 소재별(`utm_content`)로 나눠 볼 수 있게 태그가 자동으로 붙음
- 픽셀 CTA 클릭 이벤트: 표준 이벤트 `Lead` (페이지 코드에서 자동 전송) → Meta 광고 전환 최적화 이벤트로 선택

## 구글 애즈 전환 (계정 537-797-0294)
- [ ] GA4 속성 ↔ 구글 애즈 연결 (GA4 관리 > 제품 링크 > Google Ads 링크, 팀 GA4 편집자 권한 필요)
- [ ] GTM에 `전환 링커` 태그 (모든 페이지) — 광고 클릭 ID(gclid) 저장
- [ ] 구글 애즈 > 목표 > 전환 > 새 전환 액션 > 웹사이트 > 수동: 이름 `CTA 클릭`, 카테고리 `잠재고객 페이지 조회`(또는 기타), 횟수 `1회`
- [ ] GTM에 `Google Ads 전환 추적` 태그 (전환 ID·라벨은 위에서 받은 값) + 트리거: 맞춤 이벤트 `cta_click` (4개 CTA 모두 같은 이벤트라 CTA를 늘려도 그대로 잡힘)
- [ ] ⚠️ GA4 `cta_click`도 애즈로 가져오면 **보조** 전환으로 두기 (기본 전환 2개면 이중 집계)
- 광고 URL: `06_ads_tracking/utm.csv`의 Google 행 (`utm_term={keyword}`는 구글이 실제 키워드로 바꿔 줌). 랜딩 코드가 UTM을 CTA 링크로 넘겨 주므로 라이브클래스에도 google로 기록됨
- 자동 태그 추가(gclid)는 켜 둔 채로 유지

## 검증 (광고 집행 전)
- [ ] 구글 애즈 > 전환 액션 상태가 `기록 중` 또는 `최근 전환 없음`으로 바뀌는지 (GTM 게시 후 CTA 직접 클릭해 테스트)
- [ ] Google 광고 URL로 접속 → CTA 링크 주소에 `utm_source=google` 들어가는지
- [ ] GTM 미리보기에서 CTA 클릭 태그 발동
- [ ] GA4 DebugView / 실시간에서 이벤트 확인
- [ ] Meta Pixel Helper / 이벤트 관리자에서 확인
- [ ] UTM 붙은 URL로 접속 시 GA4 소스/매체 정상 수집
- [ ] CTA 링크 정상 이동
