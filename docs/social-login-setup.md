# 소셜 로그인 환경변수 설정 가이드

Glow Trip은 Google, Apple, LINE 소셜 로그인을 지원합니다.
각 서비스에서 client_id를 발급받아 환경변수에 설정하면 자동으로 활성화됩니다.

---

## 환경변수 목록

| 변수명 | 설명 | 예시 |
|--------|------|------|
| `GOOGLE_CLIENT_ID` | Google OAuth 클라이언트 ID | `123456789-xxx.apps.googleusercontent.com` |
| `APPLE_CLIENT_ID` | Apple Services ID | `com.glowtrip.web` |
| `LINE_CHANNEL_ID` | LINE Login 채널 ID | `1234567890` |
| `LINE_CHANNEL_SECRET` | LINE Login 채널 시크릿 | `abcdef1234567890` |

> client_id가 비어있는 서비스는 프론트엔드에서 해당 버튼이 자동으로 비활성화됩니다.

---

## 1. Google Sign-In

**비용:** 무료 / **난이도:** 쉬움

### 1-1. Google Cloud Console 접속
- https://console.cloud.google.com/ 로그인

### 1-2. 프로젝트 생성
- 상단 프로젝트 선택 > "새 프로젝트" > 이름: `Glow Trip` > 만들기

### 1-3. OAuth 동의 화면 설정
- 왼쪽 메뉴: API 및 서비스 > OAuth 동의 화면
- User Type: **외부** 선택
- 앱 이름: `Glow Trip`, 지원 이메일 입력
- 범위 추가: `email`, `profile`, `openid`
- 테스트 사용자에 본인 이메일 추가 (배포 전까지 테스트 사용자만 로그인 가능)

### 1-4. 사용자 인증 정보 만들기
- API 및 서비스 > 사용자 인증 정보 > "사용자 인증 정보 만들기" > **OAuth 클라이언트 ID**
- 애플리케이션 유형: **웹 애플리케이션**
- 이름: `Glow Trip Web`
- 승인된 JavaScript 원본: `http://localhost:5001`
- 승인된 리디렉션 URI: `http://localhost:5001/`
- 만들기 > **클라이언트 ID** 복사

### 1-5. 환경변수
```
GOOGLE_CLIENT_ID=123456789-abcdef.apps.googleusercontent.com
```

---

## 2. Apple Sign-In

**비용:** Apple Developer 계정 필요 ($99/년) / **난이도:** 보통

### 2-1. Apple Developer 접속
- https://developer.apple.com/account 로그인

### 2-2. App ID 등록
- Certificates, Identifiers & Profiles > Identifiers > "+" 클릭
- **App IDs** 선택 > App > Bundle ID: `com.glowtrip.app`
- Capabilities에서 **Sign In with Apple** 체크

### 2-3. Services ID 생성 (웹용)
- Identifiers > "+" > **Services IDs** 선택
- Identifier: `com.glowtrip.web`, Description: `Glow Trip Web`
- **Sign In with Apple** 체크 > Configure
  - Primary App ID: 위에서 만든 App ID 선택
  - Domains: `localhost`
  - Return URLs: `http://localhost:5001/`

### 2-4. 환경변수
```
APPLE_CLIENT_ID=com.glowtrip.web
```

---

## 3. LINE Login

**비용:** 무료 / **난이도:** 쉬움

### 3-1. LINE Developers 접속
- https://developers.line.biz/ 로그인 (LINE 계정 필요)

### 3-2. Provider 생성
- Console > "Create a new provider" > 이름: `Glow Trip`

### 3-3. LINE Login 채널 생성
- Provider 선택 > "Create a LINE Login channel"
- Channel name: `Glow Trip`
- Channel description: 입력
- App types: **Web app** 체크
- 만들기

### 3-4. 채널 설정
- Basic settings 탭:
  - **Channel ID** 복사
  - **Channel secret** 복사
- LINE Login 탭:
  - Callback URL: `http://localhost:5001/`

### 3-5. 환경변수
```
LINE_CHANNEL_ID=1234567890
LINE_CHANNEL_SECRET=abcdef1234567890abcdef1234567890
```

---

## 적용 방법

### 방법 A: 프로젝트 루트 `.env` 파일 (권장)

프로젝트 루트(`E:\glow-trip\.env`)에 파일 생성:

```env
GOOGLE_CLIENT_ID=123456789-xxx.apps.googleusercontent.com
APPLE_CLIENT_ID=com.glowtrip.web
LINE_CHANNEL_ID=1234567890
LINE_CHANNEL_SECRET=abcdef1234567890
```

docker-compose가 자동으로 같은 디렉토리의 `.env`를 읽어서 컨테이너에 전달합니다.

### 방법 B: docker-compose.yml에 직접 입력

`docker-compose.yml`의 `${변수:-}` 부분을 실제 값으로 교체합니다.
단, git에 커밋되지 않도록 주의하세요.

### 적용 (재시작)

```bash
docker-compose down && docker-compose up --build -d
```

재시작 후 `/api/config/social`에서 client_id가 반환되고, 해당 소셜 버튼이 활성화됩니다.

---

## 동작 확인

```bash
# client_id 반환 확인
curl http://localhost:5001/api/config/social
```

응답 예시:
```json
{
  "google_client_id": "123456789-xxx.apps.googleusercontent.com",
  "apple_client_id": "com.glowtrip.web",
  "line_channel_id": "1234567890"
}
```

> 값이 비어있으면 해당 서비스 버튼이 비활성화(반투명)됩니다. 하나만 설정해도 해당 서비스만 활성화됩니다.
