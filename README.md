# ✨ Glow Trip — 글로벌 에스테틱 예약 플랫폼

한국을 방문하는 외국인 관광객이 뷰티/에스테틱 샵을 검색·예약·결제할 수 있는 하이브리드 앱 플랫폼

---

## 프로젝트 구조

```
glow-trip/
├── .env                     # 로컬 환경변수 (git 제외)
├── README.md                # 프로젝트 소개 및 브릿지 (현재 파일)
├── docker-compose.yml       # Docker 개발 환경 (API/DB)
├── docs/
│   ├── CLAUDE.md            # 개발/테스트 가이드라인
│   ├── 기획서_시스템.md      # 비즈니스 전략, 기능 명세, DB 스키마
│   ├── 기획서_기획.md        # 화면 구성안, UI/UX 설계
│   ├── database-schema.md   # DB 스키마 정의서 (13 테이블, ER, 제약조건)
│   ├── api-keys-setup.md    # 외부 서비스 API 키 발급/설정 가이드
│   ├── social-login-setup.md # Google/Apple/LINE 설정 가이드
│   ├── mac-local-setup.md   # Mac 로컬(Non-Docker) 실행 가이드
│   ├── phase14-plan.md      # UI 리뉴얼 실행 계획
│   ├── phase16-plan.md      # 사용자 경험 개선 계획
│   ├── phase17-plan.md      # 소셜 로그인 구현 계획
│   ├── todo.md              # 해야 할 작업 목록 (순차 기록)
│   ├── worklog.md           # 작업 일지 인덱스
│   └── worklog/             # 주차별 작업 기록
├── backend/
│   ├── app/                 # Flask 앱 (팩토리 패턴)
│   │   ├── api/             # 비즈니스 API Blueprint
│   │   ├── auth/            # 인증/JWT/소셜 로그인
│   │   ├── models/          # SQLAlchemy 모델
│   │   ├── services/        # 외부 서비스 연동 (번역/결제/알림/푸시)
│   │   ├── templates/       # 이메일 템플릿
│   │   ├── config.py        # 환경설정
│   │   └── __init__.py      # create_app()
│   ├── migrations/          # Alembic 마이그레이션
│   ├── tests/               # pytest 테스트 코드
│   ├── run.py               # 로컬 실행 진입점
│   ├── seed.py              # 시드 데이터
│   ├── Dockerfile
│   └── requirements.txt
└── frontend/
    ├── index.html           # 고객용 모바일 웹 (SPA)
    ├── owner.html           # 상점 대시보드
    ├── admin.html           # Admin 관리 (4개 언어 i18n)
    ├── css/                 # 공통 스타일
    ├── js/                  # app.js, api.js, lang.js
    └── img/                 # 정적 이미지
```

## 기술 스택

| 영역 | 기술 |
|------|------|
| Frontend | HTML / CSS / Vanilla JS (WebView 하이브리드 앱) |
| Backend | Python Flask |
| Database | PostgreSQL (UUID PK) |
| AI 번역 | PydanticAI + Gemini Flash |
| 결제 | Stripe (PaymentIntent, Auth & Capture) |
| 알림 | SendGrid (이메일), FCM (푸시 - `FCM_SERVER_KEY` 설정 시 활성) |
| 지원 언어 | English, Japanese, Chinese, Korean |

## 주요 문서

| 문서 | 설명 |
|------|------|
| [기획서_시스템](docs/기획서_시스템.md) | 비즈니스 전략, 기능 명세, DB 스키마, 개발 스텝 |
| [기획서_기획](docs/기획서_기획.md) | 화면 구성안, UI/UX 설계 |
| [DB 스키마](docs/database-schema.md) | 13개 테이블 정의, ER 다이어그램, 제약조건, 마이그레이션 이력 |
| [API 키 발급 가이드](docs/api-keys-setup.md) | Gemini, Stripe, Google Maps, SendGrid, FCM 키 발급 방법 |
| [소셜 로그인 설정](docs/social-login-setup.md) | Google, Apple, LINE 소셜 로그인 환경변수 설정 가이드 |
| [Mac 로컬 실행 가이드](docs/mac-local-setup.md) | Docker 없이 macOS에서 DB/백엔드/테스트 실행 |
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

- **고객용 앱:** 소셜 로그인, 다국어 샵 검색(구글맵), 카테고리/가격/평점 필터, 선결제 예약, 예약 변경(Reschedule), 캘린더(ICS) 내보내기, 즐겨찾기, 최근 본 샵, 빠른 재예약, 프로필 수정
- **예약 안정성:** 타임슬롯 임시 홀드(10분 만료), 슬롯 중복/충돌 방지, 예외 스케줄(특정일 휴무/영업시간) 반영
- **상점 대시보드:** 예약 캘린더, 고객 요청사항 AI 번역, 주간 영업시간 + 특정일 예외 스케줄 관리, 정산 확인
- **Admin:** 입점 관리, 사용자/예약/정산 관리, 통계 대시보드 (4개 언어 i18n)
- **리뷰 신뢰성:** 완료 예약 기반 리뷰, 리뷰 신고 및 신고 누적 자동 숨김
- **알림:** 예약 생성/확정/취소/완료/노쇼/결제실패/환불/리마인더 이메일(4개 언어) + FCM 푸시(키 설정 시)
