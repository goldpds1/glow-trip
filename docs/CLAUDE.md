# AI Agent Guidelines for Glow Trip

## Project Overview
한국 방문 외국인 대상 에스테틱 예약 플랫폼 (하이브리드 앱)

## Tech Stack
- **Web Framework**: Flask 3.x (동기식, App Factory 패턴)
- **Database**: PostgreSQL 16 (UUID PK)
- **ORM**: SQLAlchemy + Flask-Migrate (Alembic)
- **Auth**: PyJWT + bcrypt (Access/Refresh Token)
- **AI Translation**: PydanticAI + Gemini Flash (`run_sync()`)
- **Payment**: Stripe (PaymentIntent, Auth & Capture)
- **Notification**: SendGrid (email), FCM push (`FCM_SERVER_KEY` 설정 시 활성)
- **Frontend**: Vanilla JS SPA (프레임워크 없음)
- **Infra**: Docker + docker-compose
- **Ports**: API `5001` (Docker) / `5000` (로컬), DB `5433`

## Coding Conventions (CRITICAL)

1. **Flask 동기식**: 이 프로젝트는 Flask(동기)를 사용합니다. `async def`를 사용하지 마세요.
2. **No Blocking 주의사항**: AI 번역(`run_sync`)과 Stripe 호출은 동기식으로 허용됩니다. 단, 불필요한 `time.sleep()` 등은 금지합니다.
3. **App Factory**: `create_app()` 패턴을 따르세요. Blueprint로 기능을 분리합니다.
4. **UUID PK**: 모든 모델의 기본키는 `uuid.uuid4`를 사용합니다.
5. **인증 데코레이터**: `@login_required`, `@role_required('owner')` 등을 사용하세요.
6. **번역 fallback**: AI 번역 실패 시 예약은 성공, `request_translated`만 `None`으로 처리합니다.
7. **다국어**: UI 텍스트는 `lang.js`의 `t()` 함수를 사용하세요. HTML에는 `data-i18n` 속성을 사용합니다.
8. **SPA 라우팅**: History API (`pushState`)를 사용합니다. Flask에 catch-all fallback 라우트가 있습니다.

## Project Structure

```
glow-trip/
├── backend/
│   ├── app/
│   │   ├── __init__.py        # App Factory (create_app)
│   │   ├── config.py          # 환경변수 기반 설정
│   │   ├── models/            # SQLAlchemy 모델 (user, shop, menu, booking, payment, review, business_hour, notification, favorite, slot_hold, special_schedule, review_report, user_device)
│   │   ├── auth/              # 인증 (routes, social, jwt_utils, decorators)
│   │   ├── api/               # 비즈니스 API (shops, bookings, owner, payments, favorites, admin)
│   │   └── services/          # 외부 서비스 (translator, payment, email, notification, push)
│   ├── seed.py                # 시드 데이터
│   ├── run.py                 # 로컬 실행 진입점
│   └── requirements.txt
├── frontend/
│   ├── index.html             # 고객용 SPA
│   ├── owner.html             # 상점 대시보드
│   ├── admin.html             # Admin 관리
│   ├── css/style.css
│   └── js/
│       ├── api.js             # API 헬퍼 (토큰 관리, get/post/patch)
│       ├── app.js             # SPA 라우터, 페이지 로직
│       └── lang.js            # 다국어 partial (I18N, t(), applyI18n, renderLangSelector)
├── docker-compose.yml
└── docs/
    ├── CLAUDE.md              # AI Agent 가이드라인 (현재 파일)
    ├── todo.md                # 작업 목록 (Phase 1~19)
    └── worklog/               # 주차별 작업 기록
```

## Build & Run Commands

```bash
# Docker 전체 실행
docker-compose up --build -d
curl http://localhost:5001/health

# Docker 재시작 (Flask 라우트 변경 시)
docker-compose restart api

# 로컬 실행 (DB만 Docker)
docker-compose up db -d
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py

# DB 마이그레이션
docker exec glow-trip-api-1 flask db migrate -m "설명"
docker exec glow-trip-api-1 flask db upgrade

# 시드 데이터
docker exec glow-trip-api-1 python seed.py
```

## Build & Test Commands

```bash
# 테스트 실행 (Docker 컨테이너 내부)
docker exec -e TEST_DATABASE_URL="postgresql://glowtrip:glowtrip@db:5432/glowtrip_test" \
  glow-trip-api-1 bash -c "cd /app && python -m pytest tests/ -v"

# 커버리지 포함 테스트
docker exec -e TEST_DATABASE_URL="postgresql://glowtrip:glowtrip@db:5432/glowtrip_test" \
  glow-trip-api-1 bash -c "cd /app && python -m pytest tests/ -v --cov=app --cov-report=term-missing"
```

## Test Infrastructure

- **Framework**: pytest
- **Test DB**: PostgreSQL (`glowtrip_test` 데이터베이스, 테스트별 create/drop)
- **Fixtures**: `tests/conftest.py`에 정의
  - `app` — 테스트 설정 적용된 Flask 앱
  - `client` — Flask test client
  - `customer`, `owner`, `admin` — 역할별 유저 fixture
  - `customer_headers`, `owner_headers`, `admin_headers` — JWT 인증 헤더
  - `shop`, `menu` — 테스트용 샵/메뉴 데이터
- **주의**: UUID PK 때문에 SQLite 사용 불가, 반드시 PostgreSQL 테스트 DB 사용

## Work Loop (CRITICAL — 하네스)

1. 코드를 작성/수정하기 전에 기존 라우트, DB 모델, 프론트엔드 구조를 확인하세요.
2. **Backend API를 추가/수정한 후에는 반드시 관련 테스트 코드를 작성하세요.**
   - 새 API 엔드포인트 → `tests/test_*.py`에 해당 테스트 추가
   - 정상 케이스 + 에러 케이스(인증 없음, 권한 부족, 잘못된 입력) 모두 작성
3. **테스트를 실행하고, 실패하면 코드를 수정하고 다시 테스트하세요. 모든 테스트가 통과하기 전까지 작업을 완료하지 마세요.**
   ```bash
   docker exec -e TEST_DATABASE_URL="postgresql://glowtrip:glowtrip@db:5432/glowtrip_test" \
     glow-trip-api-1 bash -c "cd /app && python -m pytest tests/ -v"
   ```
4. DB 스키마 변경 시 반드시 Flask-Migrate로 마이그레이션을 생성/적용하세요.
5. Frontend 변경은 Docker 볼륨 마운트로 즉시 반영됩니다.
6. 새 기능 완료 후 `docs/todo.md`에서 해당 항목을 체크하세요.
7. 작업 완료 후 `docs/worklog/` 해당 주차 파일에 작업 내용을 기록하세요.

## Key Conventions

- **API 응답**: JSON 형식, 에러 시 `{"error": "메시지"}` + 적절한 HTTP 상태 코드
- **프론트엔드 텍스트**: 하드코딩 금지. `lang.js`의 `I18N` 객체에 4개 언어(ko/en/ja/zh) 모두 추가
- **Blueprint URL prefix**: `/api/auth`, `/api/auth/social`, `/api/shops`, `/api/bookings`, `/api/owner`, `/api/payments`, `/api/favorites`, `/api/admin`, `/api/reviews`, `/api/upload`
- **Config API**: `/api/config/maps-key`, `/api/config/social` (client_id만 노출, secret 미포함)
- **결제**: Stripe 키 없으면 503 반환, 번역 키 없으면 fallback
- **CSS**: `style.css`에 변수(`--primary`, `--border` 등) 사용, 모바일 퍼스트 반응형
- **문서**: README.md는 브릿지 역할, 상세 내용은 기획서.md 참고
