# API 키 발급 가이드

Glow Trip에서 사용하는 외부 서비스별 API 키 발급 방법입니다.
소셜 로그인(Google/Apple/LINE)은 [social-login-setup.md](social-login-setup.md)를 참고하세요.

---

## 1. Gemini API Key (AI 번역)

고객의 외국어 요청사항을 한국어로 자동 번역하는 데 사용합니다.

| 항목 | 내용 |
|------|------|
| 서비스 | Google AI Studio (Gemini Flash) |
| 비용 | 무료 티어 제공 (분당 15회, 일 1,500회) |
| 환경변수 | `GEMINI_API_KEY` |

### 발급 절차

1. [Google AI Studio](https://aistudio.google.com/) 접속 후 Google 계정 로그인
2. 좌측 메뉴 **Get API key** 클릭
3. **Create API key** 클릭 > 기존 프로젝트 선택 또는 새 프로젝트 생성
4. 생성된 API 키 복사

### 환경변수 설정

```env
GEMINI_API_KEY=AIzaSy...your-key-here
```

### 확인

```bash
# API 키 없이도 예약은 성공하며, 번역만 None으로 처리됩니다 (graceful fallback)
curl -s http://localhost:5001/health
```

---

## 2. Stripe (결제)

예약 시 해외 신용카드 결제(Auth & Capture)를 처리합니다.

| 항목 | 내용 |
|------|------|
| 서비스 | Stripe |
| 비용 | 건당 2.9% + 30센트 (테스트 모드 무료) |
| 환경변수 | `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` |

### 발급 절차

#### 2-1. 계정 생성
1. [Stripe Dashboard](https://dashboard.stripe.com/) 접속 후 회원가입
2. 이메일 인증 완료

#### 2-2. Secret Key 발급
1. Dashboard > **Developers** (우측 상단) > **API keys**
2. **Test mode** 가 활성화된 상태인지 확인 (좌측 상단 토글)
3. **Secret key** 의 `sk_test_...` 값 복사
   - Publishable key (`pk_test_...`)는 프론트엔드에서 사용하지만 현재 환경변수에는 불필요

#### 2-3. Webhook Secret 발급
1. Dashboard > Developers > **Webhooks**
2. **Add endpoint** 클릭
3. Endpoint URL: `http://localhost:5001/api/payments/webhook`
   - 배포 시 실제 도메인으로 변경
4. Events to listen: `payment_intent.succeeded`, `payment_intent.payment_failed`
5. 생성 후 **Signing secret** (`whsec_...`) 복사

### 환경변수 설정

```env
STRIPE_SECRET_KEY=sk_test_51...your-secret-key
STRIPE_WEBHOOK_SECRET=whsec_...your-webhook-secret
```

### 테스트 카드 번호

| 카드 번호 | 결과 |
|-----------|------|
| `4242 4242 4242 4242` | 성공 |
| `4000 0000 0000 0002` | 거절 |
| `4000 0000 0000 3220` | 3D Secure 인증 필요 |

> 만료일: 미래 날짜 아무거나, CVC: 아무 3자리

---

## 3. Google Maps API Key (지도)

샵 상세 페이지 지도 표시, 샵 목록 지도 뷰에 사용합니다.

| 항목 | 내용 |
|------|------|
| 서비스 | Google Maps Platform |
| 비용 | 월 $200 무료 크레딧 (약 28,000회 로드) |
| 환경변수 | `GOOGLE_MAPS_API_KEY` |

### 발급 절차

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 프로젝트 선택 (소셜 로그인과 동일 프로젝트 사용 가능)
3. 좌측 메뉴 > **API 및 서비스** > **라이브러리**
4. **Maps JavaScript API** 검색 후 **사용** 클릭
5. 좌측 메뉴 > **API 및 서비스** > **사용자 인증 정보**
6. **사용자 인증 정보 만들기** > **API 키**
7. 생성된 키 복사

#### 키 제한 (권장)

1. 생성된 API 키 클릭 > **키 제한**
2. **애플리케이션 제한사항**: HTTP 리퍼러
3. 허용 리퍼러 추가:
   - `http://localhost:5001/*`
   - `https://yourdomain.com/*` (배포 시)
4. **API 제한사항**: Maps JavaScript API만 선택

### 환경변수 설정

```env
GOOGLE_MAPS_API_KEY=AIzaSy...your-maps-key-here
```

### 확인

```bash
# 키가 반환되면 프론트엔드에서 자동 로드
curl http://localhost:5001/api/config/maps-key
# {"key": "AIzaSy..."}
```

> 키가 없으면 지도가 표시되지 않지만 앱의 다른 기능은 정상 작동합니다.

---

## 4. SendGrid (이메일 알림)

예약 확정/취소/리마인더 등 8종 알림 이메일을 발송합니다.

| 항목 | 내용 |
|------|------|
| 서비스 | Twilio SendGrid |
| 비용 | 무료 티어 (일 100통) |
| 환경변수 | `SENDGRID_API_KEY`, `SENDGRID_FROM_EMAIL`, `SENDGRID_FROM_NAME` |

### 발급 절차

1. [SendGrid](https://signup.sendgrid.com/) 회원가입
2. 이메일 인증 + 계정 활성화 (Twilio 인증 필요할 수 있음)
3. 좌측 메뉴 > **Settings** > **API Keys**
4. **Create API Key** 클릭
5. 이름: `Glow Trip`, 권한: **Restricted Access** > Mail Send만 Full Access
6. 생성된 키 (`SG.xxx`) 복사 (이 화면에서만 볼 수 있음)

#### 발신자 인증 (필수)

1. Settings > **Sender Authentication**
2. **Single Sender Verification** > **Create a Sender**
3. From Email: `noreply@glowtrip.com` (또는 본인 이메일)
4. 인증 메일 확인 클릭

### 환경변수 설정

```env
SENDGRID_API_KEY=SG.xxxx...your-api-key
SENDGRID_FROM_EMAIL=noreply@glowtrip.com
SENDGRID_FROM_NAME=Glow Trip
```

### 확인

> API 키가 없으면 이메일 발송을 건너뛰며, 예약 등 핵심 기능은 정상 작동합니다.

---

## 5. FCM (푸시 알림)

모바일 앱 푸시 알림 발송에 사용합니다.

| 항목 | 내용 |
|------|------|
| 서비스 | Firebase Cloud Messaging |
| 비용 | 무료 |
| 환경변수 | `FCM_SERVER_KEY` |

### 발급 절차

1. [Firebase Console](https://console.firebase.google.com/) 접속
2. **프로젝트 추가** > 이름: `Glow Trip` > 만들기
3. 프로젝트 설정 (톱니바퀴) > **Cloud Messaging** 탭
4. **Cloud Messaging API (Legacy)** 가 **사용 설정됨** 인지 확인
   - 비활성화 시 **Google Cloud Console에서 관리** 링크 클릭 후 활성화
5. **서버 키** 복사

### 환경변수 설정

```env
FCM_SERVER_KEY=AAAA...your-server-key
```

> 현재 네이티브 앱 패키징(Phase 99) 전이므로, 설정하지 않아도 됩니다.

---

## 환경변수 전체 요약

| 환경변수 | 서비스 | 필수 | 미설정 시 동작 |
|----------|--------|------|----------------|
| `GEMINI_API_KEY` | AI 번역 | 선택 | 번역 건너뜀, 예약은 성공 |
| `STRIPE_SECRET_KEY` | 결제 | 선택 | 결제 API 503 반환 |
| `STRIPE_WEBHOOK_SECRET` | 결제 웹훅 | 선택 | 웹훅 검증 건너뜀 |
| `GOOGLE_MAPS_API_KEY` | 지도 | 선택 | 지도 미표시 |
| `SENDGRID_API_KEY` | 이메일 | 선택 | 알림 메일 발송 안 됨 |
| `SENDGRID_FROM_EMAIL` | 이메일 | 선택 | 기본값 `noreply@glowtrip.com` |
| `SENDGRID_FROM_NAME` | 이메일 | 선택 | 기본값 `Glow Trip` |
| `FCM_SERVER_KEY` | 푸시 알림 | 선택 | 푸시 발송 안 됨 |

> 모든 외부 서비스 키는 선택 사항입니다. 키 없이도 핵심 기능(회원가입, 샵 검색, 예약)은 정상 작동합니다.
