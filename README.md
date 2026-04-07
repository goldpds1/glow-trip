# ✨ Glow Trip — 글로벌 에스테틱 예약 플랫폼

한국을 방문하는 외국인 관광객이 뷰티/에스테틱 샵을 검색·예약·결제할 수 있는 하이브리드 앱 플랫폼

---

## 프로젝트 구조

```
glow-trip/
├── README.md                # 프로젝트 소개 및 브릿지 (현재 파일)
├── docker-compose.yml       # Docker 개발 환경
├── docs/
│   ├── 기획서_시스템.md      # 비즈니스 전략, 기능 명세, DB 스키마
│   ├── 기획서_기획.md        # 화면 구성안, UI/UX 설계
│   ├── database-schema.md   # DB 스키마 정의서 (9 테이블, ER, 제약조건)
│   ├── todo.md              # 해야 할 작업 목록 (순차 기록)
│   ├── worklog.md           # 작업 일지 인덱스
│   └── worklog/             # 주차별 작업 기록
├── backend/
│   ├── app/                 # Flask 앱 (팩토리 패턴)
│   ├── run.py               # 로컬 실행 진입점
│   ├── Dockerfile
│   └── requirements.txt
└── frontend/
    ├── index.html           # 고객용 모바일 웹 (SPA)
    ├── owner.html           # 상점 대시보드
    ├── admin.html           # Admin 관리 (4개 언어 i18n)
    ├── css/style.css
    └── js/                  # api.js, app.js, lang.js
```

## 기술 스택

| 영역 | 기술 |
|------|------|
| Frontend | HTML / CSS / Vanilla JS (WebView 하이브리드 앱) |
| Backend | Python Flask |
| Database | PostgreSQL (UUID PK) |
| AI 번역 | PydanticAI + Gemini Flash |
| 결제 | Stripe (PaymentIntent, Auth & Capture) |
| 알림 | SendGrid (이메일), FCM (푸시 - stub) |
| 지원 언어 | English, Japanese, Chinese, Korean |

## 주요 문서

| 문서 | 설명 |
|------|------|
| [기획서_시스템](docs/기획서_시스템.md) | 비즈니스 전략, 기능 명세, DB 스키마, 개발 스텝 |
| [기획서_기획](docs/기획서_기획.md) | 화면 구성안, UI/UX 설계 |
| [DB 스키마](docs/database-schema.md) | 9개 테이블 정의, ER 다이어그램, 제약조건, 마이그레이션 이력 |
| [소셜 로그인 설정](docs/social-login-setup.md) | Google, Apple, LINE 소셜 로그인 환경변수 설정 가이드 |
| [TODO](docs/todo.md) | 해야 할 작업 순차 목록 |
| [작업일지](docs/worklog.md) | 월-주차별 작업 기록 |

## 실행 방법

### Docker 전체 실행
```bash
docker-compose up --build -d
curl http://localhost:5001/health
```

### 로컬 실행 (DB만 Docker)
```bash
docker-compose up db -d
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
curl http://localhost:5000/health
```

> 포트: API `5001` (Docker) / `5000` (로컬), DB `5433`

## 핵심 기능

- **고객용 앱:** 소셜 로그인, 다국어 샵 검색(구글맵), 카테고리/가격/평점 필터, 선결제 예약, 즐겨찾기, 프로필 수정
- **상점 대시보드:** 예약 캘린더, 고객 요청사항 AI 번역, 스케줄 관리, 정산 확인
- **Admin:** 입점 관리, 사용자/예약/정산 관리, 통계 대시보드 (4개 언어 i18n)
- **알림:** 예약 생성/확정/취소/완료/노쇼/결제실패/환불/리마인더 이메일 (4개 언어)
