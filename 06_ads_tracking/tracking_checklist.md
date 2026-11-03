# 전환 추적 체크리스트

## 퍼널
광고 노출 → 광고 클릭 → 랜딩페이지 방문 → **CTA 클릭 (핵심 전환)** → 라이브클래스 상세페이지 이동

## 설치
ID는 `03_landing_page/index.html` 상단 `window.TRACKING` 두 값만 바꾸면 됩니다. `XXX`가 남아 있으면 해당 태그는 로드되지 않습니다.
- [ ] GTM 컨테이너 ID 입력 (`GTM_ID`)
- [x] 메타 픽셀 ID 입력 (`META_PIXEL_ID` = 1664723555062468, "Final-project 픽셀") — 페이지에 직접 설치됨, PageView 자동
- [ ] ⚠️ GTM 안에 메타 픽셀 태그를 또 만들지 않기 (중복 집계)
- [ ] GA4 구성 태그 (GTM)
- [ ] GTM 맞춤 이벤트 트리거 `cta_click` → GA4 이벤트 `cta_click` (매개변수 `cta_location`: header(PC 상단) / hero / floating(PC 좌측 하단) / apply / sticky(모바일 하단))
- [ ] GTM 맞춤 이벤트 트리거 `section_view` → GA4 이벤트 `section_view` (매개변수 `section_name`) — 이탈 구간 분석용
- [ ] GA4에서 `cta_click` 을 주요 이벤트(전환)로 표시
- [ ] Microsoft Clarity(무료 히트맵·세션 녹화) 프로젝트 생성 → ID를 `index.html` 상단 `CLARITY_ID`에 입력. 소재별(`utm_content`)로 나눠 볼 수 있게 태그가 자동으로 붙음
- 픽셀 CTA 클릭 이벤트: 표준 이벤트 `Lead` (페이지 코드에서 자동 전송) → Meta 광고 전환 최적화 이벤트로 선택

## 검증 (광고 집행 전)
- [ ] GTM 미리보기에서 CTA 클릭 태그 발동
- [ ] GA4 DebugView / 실시간에서 이벤트 확인
- [ ] Meta Pixel Helper / 이벤트 관리자에서 확인
- [ ] UTM 붙은 URL로 접속 시 GA4 소스/매체 정상 수집
- [ ] CTA 링크 정상 이동
