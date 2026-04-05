# TODO — 작업 목록

> 순차적으로 진행할 작업을 기록합니다. 완료 시 체크 표시합니다.

---

## Phase 1: 개발 환경 구축

- [x] Docker + docker-compose.yml 작성 (Flask + PostgreSQL)
- [x] Flask 프로젝트 초기 구조 생성 (app factory, config, run.py, requirements.txt)
- [x] PostgreSQL 컨테이너 연결 확인 (`/health` 엔드포인트 OK)

## Phase 2: 데이터베이스

- [x] 5대 핵심 테이블 모델 정의 (users, shops, menus, bookings, payments)
- [x] Flask-Migrate 초기화 및 마이그레이션 실행
- [x] 시드 데이터 작성 및 적용 (users 5, shops 2, menus 5, bookings 2, payments 2)

## Phase 3: 인증 API

- [x] 이메일 회원가입 / 로그인 API (JWT 발급)
- [x] 소셜 로그인 연동 (Google, Apple, LINE)
- [x] 토큰 갱신 및 인증 미들웨어 구현 (@login_required, @role_required)

## Phase 4: 핵심 비즈니스 API

- [x] 샵 목록 조회 / 상세 조회 API (키워드 검색, 페이지네이션)
- [x] 메뉴 조회 API (샵 상세에 포함 + 별도 엔드포인트)
- [x] 예약 생성 / 조회 / 취소 API (고객용)
- [x] 상점용 예약 관리 API (캘린더, 날짜필터, 상태변경: 확정/완료/노쇼)

## Phase 5: AI 번역 연동

- [x] PydanticAI + Gemini Flash 번역 파이프라인 구현 (run_sync, 시스템 프롬프트)
- [x] 예약 생성 시 request_original → request_translated 자동 번역
- [x] 번역 실패 시 fallback 처리 (예약은 성공, 번역만 None)

## Phase 6: 결제 연동

- [x] Stripe PaymentIntent 연동 (Auth & Capture, manual capture)
- [x] 결제 시작/상태조회/환불 API + Webhook 수신
- [x] 정산 조회 API (수수료 10% 공제, 원장용)

## Phase 7: 프론트엔드 / 웹뷰

- [x] 고객용 모바일 웹 UI — SPA (검색, 상세, 예약, 취소, 마이페이지)
- [x] 상점용 웹 대시보드 — 예약 캘린더, AI 번역 확인, 정산 조회
- [x] Admin 관리 화면 — 샵/예약 목록, 통계
- [x] 중국어(zh) 언어 지원 추가
- [ ] Android / iOS WebView 네이티브 패키징 (추후)

## Phase 8: 상점 관리 (샵 수정 + 메뉴 CRUD)

- [x] 샵 수정 API (PATCH /api/owner/shops/:id — 상호명, 주소, 전화번호, 설명)
- [x] 메뉴 추가 API (POST /api/owner/shops/:id/menus)
- [x] 메뉴 수정 API (PATCH /api/owner/menus/:id)
- [x] 메뉴 삭제 API (DELETE /api/owner/menus/:id)
- [x] 상점 대시보드 — 샵 정보 수정 UI
- [x] 상점 대시보드 — 메뉴 관리 UI (추가/수정/삭제)
- [x] 상점 대시보드 — 로그아웃 버튼 추가

## Phase 9: 이미지 업로드

- [x] 이미지 업로드 API (POST /api/upload — 로컬 저장, 5MB 제한)
- [x] 샵 대표 이미지 업로드/표시
- [x] 메뉴별 이미지 업로드/표시
- [x] 고객앱 — 샵 카드/상세에 실제 이미지 표시

## Phase 10: 결제 UI (Stripe.js)

- [x] 프론트엔드 Stripe.js 로드 및 카드 입력 UI
- [x] 예약 → 결제 → 완료 플로우 연결
- [x] 상점 대시보드 — 환불 처리 버튼 추가

## Phase 11: 구글맵 연동

- [x] Google Maps API 키 설정 및 연동
- [x] 샵 상세 — 지도에 위치 표시
- [x] 샵 목록 — 지도 뷰 모드 추가
- [x] 거리순 정렬/필터

## Phase 12: 리뷰/평점 시스템

- [x] reviews 테이블 생성 (user_id, shop_id, booking_id, rating, comment)
- [x] 리뷰 작성 API (POST /api/reviews — 완료된 예약만)
- [x] 리뷰 조회 API (GET /api/shops/:id/reviews)
- [x] 샵 상세 — 평점/리뷰 표시
- [x] 샵 목록 — 평균 평점 표시

## Phase 13: 관리자 기능 확장

- [x] 사용자 관리 API 및 UI (목록, 역할 변경, 검색/필터)
- [x] 샵 승인/관리 API 및 UI (활성/비활성 토글, 검색/필터)
- [x] 전체 예약 관리 (목록 조회, 상태 필터, 강제 취소/환불)
- [x] 전체 정산 관리 (샵별 정산 현황, 수수료 합계)
- [x] 통계 대시보드 (매출 합계, 예약 추이 차트, 인기 샵 Top5)

## Phase 14: 알림 시스템

- [ ] 이메일 발송 연동 (SendGrid 또는 SMTP)
- [ ] 예약 확정/취소 알림 메일
- [ ] 예약 리마인더 메일
- [ ] 푸시 알림 연동 (FCM)

## Phase 15: 사용자 경험 개선

- [ ] 프로필 수정 API 및 UI (이름, 전화번호, 언어)
- [ ] 영업시간/예약 슬롯 관리 (요일별 영업시간, 시간대 차단)
- [ ] 예약 가능 시간 캘린더 표시
- [ ] 즐겨찾기 (관심 샵 저장)
- [ ] 샵 필터/정렬 (가격대, 평점순, 거리순)

## Phase 16: 네이티브 앱 패키징

- [ ] Android WebView 앱 빌드
- [ ] iOS WebView 앱 빌드
- [ ] 딥링크 처리
- [ ] 앱스토어/플레이스토어 배포 준비

---

> 작업 추가 시 해당 Phase 하단에 기록. 새 Phase 필요 시 번호 이어서 추가.
