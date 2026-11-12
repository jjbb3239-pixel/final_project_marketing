# 2차 랜딩 개선 배포 기록 (2026-11-12)

## 무엇이 바뀌나
- **인트로 섹션**: 새 디자인(회색 배경, "김운아가 알려주는 삶이 흔들리지 않는 제테크", 저서 문구, 강사 사진). 4칸 정보 띠(VOD 7강 등)는 삭제. 웹(861px 이상)은 한 화면 높이, 모바일·태블릿은 화면의 약 52% 높이.
- **인트로 CTA 문구**: "ETF 성장주 확인하러 가기" → "재태크 성공 공식 알아보기". 도착 주소(무료 1강)와 `data-cta-location="intro"`는 그대로.
- **섹션 순서**: 히어로 → 탭 → 인트로 → 목차 → 가격·변화 → 후기 → 강의 소개 → 커뮤니티 → FAQ·신청. 탭 순서는 강의 소개 / 강의 후기 / 자주 묻는 질문(강의 소개 → #intro, 강의 후기 → #cause, 자주 묻는 질문 → #apply).
- **프리뷰 모달**: 제목을 "1강 성장주 투자, 어렵지 않습니다."로 변경, 우측 상단 X 버튼 추가, 모달 바깥(어두운 영역) 터치로 닫기 추가, 바깥 어둡기 완화(0.72 → 0.5), 소리 켜기/끄기 버튼을 영상 우측 상단으로 이동.
- `layout_version`: `landing-20261110-v4` → **`landing-20261112-v5`**.

## 이벤트 설계 (변경 없음 + 값 추가)
- 이벤트 이름, `data-track-section`, `data-cta-location`, CTA 도착 주소, `cta_click` 조건은 수정 전과 같음. 광고 전환 태그가 쓰는 `cta_click`은 바뀌지 않음.
- `preview_modal_close`의 `preview_close_reason`에 새 값 **`x_button`, `backdrop`** 추가. 기존 값(`text_link`, `esc`, `back_button`)은 그대로. GA4 맞춤 측정기준 `preview_close_reason`은 이미 등록돼 있음.
- GTM 변경 없음(게시 불필요).
- 로컬 검증(GTM 꺼진 복사본, `dataLayer` 확인): 섹션 9개 `section_view` 1회씩, `scroll_depth` 25/50/75/90, CTA별 `cta_click`/UTM 전달, 모달 닫기 5경로 각 1회, 모달 CTA `preview_cta_click` + `cta_click(landing_preview_modal)`. 수정 전 버전과 결과 동일.

## 분석할 때 주의
- 섹션 순서가 바뀌어 `section_view` 도달 비율은 v4와 같은 기준으로 비교되지 않음. `layout_version`(v4/v5)으로 나눠서 볼 것.
- 인트로 높이가 달라져 `section_view`(intro) 발생 시점이 이전과 다를 수 있음.

## 알려진 사항
- 디자인 이미지 문구 "제테크"/"재태크"를 그대로 반영함(사이트 다른 곳은 "재테크"). 오탈자로 확인되면 수정 필요.
- 탭 하이라이트: 후기 이후의 강의 소개·커뮤니티 구간은 "강의 후기" 탭이 켜짐.
- 실제 폰 인앱 브라우저에서의 바깥 터치·X 동작은 배포 후 확인 필요.

## 배포 후 확인
- `qa_` UTM 링크로 모달 열림/닫기(X, 바깥 터치), 섹션 순서, 인트로 CTA 이동. 모달 CTA나 인트로 CTA를 누르면 광고 전환이 올라가므로 꼭 필요할 때만 1회.
- GA4 실시간/DebugView에서 `layout_version=landing-20261112-v5`, `preview_close_reason` 새 값 도착.

## 되돌리기
- PR 되돌리기(revert) → 자동 재배포. 되돌려도 GA4에 쌓인 v5 기록과 새 `preview_close_reason` 값은 남음.
