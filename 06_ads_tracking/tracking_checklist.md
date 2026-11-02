# 전환 추적 체크리스트

## 퍼널
광고 노출 → 광고 클릭 → 랜딩페이지 방문 → **CTA 클릭 (핵심 전환)** → 라이브클래스 상세페이지 이동

## 설치
- [ ] GTM 컨테이너 설치 (index.html의 GTM-XXXXXXX 교체)
- [ ] GA4 구성 태그 (GTM)
- [ ] 메타 픽셀 기본 코드 (GTM) — PageView
- [ ] CTA 클릭 트리거 (`#cta-main` / `.cta`) → GA4 이벤트 `cta_click` + 픽셀 이벤트
- [ ] GA4에서 `cta_click` 을 주요 이벤트(전환)로 표시

## 검증 (광고 집행 전)
- [ ] GTM 미리보기에서 CTA 클릭 태그 발동
- [ ] GA4 DebugView / 실시간에서 이벤트 확인
- [ ] Meta Pixel Helper / 이벤트 관리자에서 확인
- [ ] UTM 붙은 URL로 접속 시 GA4 소스/매체 정상 수집
- [ ] CTA 링크 정상 이동
