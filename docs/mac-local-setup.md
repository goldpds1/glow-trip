# Mac 로컬 개발 가이드 (Non-Docker)

> Docker 없이 macOS에서 Glow Trip 백엔드/테스트를 실행하는 방법

---

## 1) 사전 준비

- Python 3.12
- PostgreSQL 16+
- (선택) `pyenv`, `venv`

---

## 2) PostgreSQL DB 생성

아래 2개 DB를 만듭니다.

- `glowtrip` (개발용)
- `glowtrip_test` (테스트용)

예시:
```bash
createdb glowtrip
createdb glowtrip_test
```

---

## 3) 백엔드 설치

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 4) 환경변수 설정

프로젝트 루트 `.env` 또는 셸 환경변수에 설정:

```bash
export DATABASE_URL="postgresql://<user>:<password>@localhost:5432/glowtrip"
export TEST_DATABASE_URL="postgresql://<user>:<password>@localhost:5432/glowtrip_test"
export SECRET_KEY="dev-secret-key"
```

선택(기능 활성화 시):

- `GEMINI_API_KEY`
- `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`
- `GOOGLE_MAPS_API_KEY`
- `GOOGLE_CLIENT_ID`, `APPLE_CLIENT_ID`, `LINE_CHANNEL_ID`, `LINE_CHANNEL_SECRET`
- `SENDGRID_API_KEY`
- `FCM_SERVER_KEY`

---

## 5) 마이그레이션 + 시드

```bash
cd backend
source .venv/bin/activate
flask db upgrade
python seed.py
```

---

## 6) 로컬 실행

```bash
cd backend
source .venv/bin/activate
python run.py
```

- API: `http://localhost:5000`
- 헬스체크: `http://localhost:5000/health`

---

## 7) 테스트 실행 (Docker 없이)

```bash
cd backend
source .venv/bin/activate
python -m pytest tests/ -v
```

커버리지:
```bash
python -m pytest tests/ -v --cov=app --cov-report=term-missing
```

---

## 트러블슈팅

- `relation does not exist`:
  - `flask db upgrade` 재실행
- `role/database does not exist`:
  - PostgreSQL 사용자/DB 생성 여부 확인
- 소셜/결제 버튼 비활성:
  - 해당 `*_CLIENT_ID` 또는 키 환경변수 설정 확인

