# Phase 17: 소셜 로그인 구현 플랜

## Context
소셜 로그인(Google, Apple, LINE) 백엔드 코드(`social.py`)와 프론트엔드 UI 버튼은 이미 존재하지만, SDK 스크립트가 로드되지 않고 client_id가 비어있어 실제 동작하지 않는다. 이 Phase에서 완전히 동작하는 소셜 로그인을 구현한다.

## 현재 상태 분석

### 이미 있는 것
| 구분 | 파일 | 상태 |
|------|------|------|
| Google/Apple/LINE 백엔드 | `backend/app/auth/social.py` | 토큰 검증 로직 완성 |
| User 모델 | `auth_provider`, `provider_id` 필드 | 존재 |
| Config | `GOOGLE_CLIENT_ID`, `APPLE_CLIENT_ID`, `LINE_CHANNEL_ID/SECRET` | 환경변수 로드 O, 값 비어있음 |
| 프론트엔드 버튼 | `index.html` 로그인/회원가입 화면 | 6개 버튼 존재 |
| 프론트엔드 로직 | `app.js socialLogin()` | 빈 client_id, SDK 미로드 |

### 누락된 것
1. **SDK 스크립트 태그**: Google GSI, Apple JS SDK가 `index.html`에 없음
2. **Config API**: 프론트엔드가 client_id를 동적으로 받을 엔드포인트 없음
3. **LINE code→token 교환**: 프론트엔드가 OAuth redirect의 `code`를 받지만, 이를 `access_token`으로 교환하는 로직 없음 (백엔드는 `access_token`만 기대)
4. **LINE 콜백 핸들러**: 리디렉트 후 URL의 `code` 파라미터를 처리하는 코드 없음
5. **계정 병합**: 동일 이메일 소셜→기존 계정 연결 시 `provider_id` 업데이트 안 됨
6. **테스트**: 소셜 로그인 관련 테스트 없음

---

## Step 1: Config API — 프론트엔드에 client_id 제공

**수정: `backend/app/__init__.py`**

`/api/config/social` 엔드포인트 추가:
```python
@app.route("/api/config/social")
def social_config():
    return jsonify(
        google_client_id=app.config.get("GOOGLE_CLIENT_ID", ""),
        apple_client_id=app.config.get("APPLE_CLIENT_ID", ""),
        line_channel_id=app.config.get("LINE_CHANNEL_ID", ""),
    ), 200
```

> client_secret은 절대 노출하지 않음. client_id만 반환.

## Step 2: LINE code→token 교환 엔드포인트

**수정: `backend/app/auth/social.py`**

새 엔드포인트 `POST /api/auth/social/line/exchange` 추가:
- 프론트엔드에서 `code` + `redirect_uri`를 받음
- 백엔드에서 LINE token API 호출하여 `access_token` 획득
- 기존 `_find_or_create_user()` → JWT 발급

```python
@social_bp.route("/line/exchange", methods=["POST"])
def line_exchange():
    data = request.get_json() or {}
    code = data.get("code", "")
    redirect_uri = data.get("redirect_uri", "")
    if not code:
        return jsonify(error="code is required"), 400

    # code → access_token 교환
    resp = requests.post("https://api.line.me/oauth2/v2.1/token", data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": current_app.config["LINE_CHANNEL_ID"],
        "client_secret": current_app.config["LINE_CHANNEL_SECRET"],
    }, timeout=10)
    if resp.status_code != 200:
        return jsonify(error="LINE token exchange failed"), 401

    token_data = resp.json()
    access_token = token_data.get("access_token", "")

    # 프로필 조회 (기존 로직 재사용)
    profile_resp = requests.get(
        "https://api.line.me/v2/profile",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=5,
    )
    if profile_resp.status_code != 200:
        return jsonify(error="Failed to fetch LINE profile"), 401

    profile = profile_resp.json()
    line_user_id = profile.get("userId", "")
    # id_token에서 이메일 추출 시도 (LINE은 이메일 제공이 선택적)
    email = data.get("email") or f"{line_user_id}@line.placeholder"

    user = _find_or_create_user(
        email=email, provider="line", provider_id=line_user_id,
        name=profile.get("displayName"), language=data.get("language", "ja"),
    )
    tokens = create_tokens(user.id)
    return jsonify(user_id=str(user.id), **tokens), 200
```

## Step 3: 계정 병합 로직 개선

**수정: `backend/app/auth/social.py`** — `_find_or_create_user()` 수정

현재: 동일 이메일 기존 유저 발견 시 그냥 반환 → 소셜 provider_id가 저장 안 됨
개선: 기존 유저의 `provider_id`가 비어있으면 업데이트 (향후 재로그인 시 provider_id로 매칭)

```python
def _find_or_create_user(email, provider, provider_id, name=None, language="en"):
    # 1) provider+provider_id로 먼저 검색
    user = User.query.filter_by(auth_provider=provider, provider_id=provider_id).first()
    if user:
        return user

    # 2) 같은 이메일로 이미 가입된 경우 → 계정 연결
    user = User.query.filter_by(email=email).first()
    if user:
        # 이메일 계정이 소셜 정보 미보유 시 연결 (email auth → social로 전환하지는 않음)
        if user.auth_provider == "email" and not user.provider_id:
            user.auth_provider = provider
            user.provider_id = provider_id
            db.session.commit()
        return user

    # 3) 신규 생성
    user = User(
        email=email, auth_provider=provider, provider_id=provider_id,
        name=name, language=language, role="customer",
    )
    db.session.add(user)
    db.session.commit()
    return user
```

## Step 4: 프론트엔드 — SDK 로드 + Config API 연동

### 4-A. SDK 스크립트 태그 (`index.html`)

```html
<!-- Google GSI -->
<script src="https://accounts.google.com/gsi/client" async defer></script>
<!-- Apple Sign-In JS -->
<script src="https://appleid.cdn-apple.com/appleauth/static/jsapi/appleid/1/en_US/appleid.auth.js" async defer></script>
```

> LINE은 OAuth redirect 방식이므로 별도 SDK 불필요.

### 4-B. Config 로드 + socialLogin() 수정 (`app.js`)

앱 초기화 시 `/api/config/social` 호출하여 client_id를 전역 변수에 저장:

```javascript
let socialConfig = { google_client_id: '', apple_client_id: '', line_channel_id: '' };

async function loadSocialConfig() {
  try {
    const res = await fetch(API + '/config/social');
    if (res.ok) socialConfig = await res.json();
  } catch (e) { /* silent — social login just won't be available */ }
}
```

`socialLogin()` 수정:
- Google: `client_id: socialConfig.google_client_id`
- Apple: `AppleID.auth.init({ clientId: socialConfig.apple_client_id, ... })`
- LINE: `client_id=${socialConfig.line_channel_id}`

### 4-C. LINE 콜백 핸들러

SPA 라우터(`handleRoute()`)에서 URL에 `code` + `state` 파라미터가 있으면 LINE 콜백 처리:

```javascript
async function handleLineCallback() {
  const params = new URLSearchParams(window.location.search);
  const code = params.get('code');
  const state = params.get('state');
  const savedState = sessionStorage.getItem('line_state');

  if (!code || state !== savedState) {
    showAuthError('LINE login failed: invalid state');
    return;
  }
  sessionStorage.removeItem('line_state');

  const res = await fetch(API + '/auth/social/line/exchange', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      code,
      redirect_uri: window.location.origin + '/',
      language: getLang(),
    }),
  });
  const data = await res.json();
  if (!res.ok) return showAuthError(data.error || t('socialFailed'));
  setTokens(data);
  // URL에서 code 파라미터 제거
  history.replaceState(null, '', '/');
  navigate('shops');
}
```

`handleRoute()` 상단에:
```javascript
if (new URLSearchParams(window.location.search).has('code')) {
  return handleLineCallback();
}
```

## Step 5: Apple Sign-In 초기화

Apple Sign-In은 `signIn()` 호출 전 `init()` 필요:

```javascript
if (provider === 'apple') {
  if (!window.AppleID) return showAuthError('Apple' + t('socialUnavailable'));
  AppleID.auth.init({
    clientId: socialConfig.apple_client_id,
    scope: 'email name',
    redirectURI: window.location.origin + '/',
    usePopup: true,
  });
  const appleResp = await AppleID.auth.signIn();
  // ... (기존 로직)
}
```

## Step 6: 소셜 로그인 버튼 비활성화 (client_id 미설정 시)

Config API에서 받은 client_id가 비어있으면 해당 소셜 버튼을 비활성화:

```javascript
function updateSocialButtons() {
  document.querySelectorAll('.btn-google').forEach(btn => {
    btn.disabled = !socialConfig.google_client_id;
  });
  document.querySelectorAll('.btn-apple').forEach(btn => {
    btn.disabled = !socialConfig.apple_client_id;
  });
  document.querySelectorAll('.btn-line').forEach(btn => {
    btn.disabled = !socialConfig.line_channel_id;
  });
}
```

## Step 7: 테스트 작성

**새 파일: `backend/tests/test_social.py`** (~15개 테스트)

| # | 테스트 | 분류 |
|---|--------|------|
| 1 | Google login — valid token → 200 + JWT | unit (mock requests) |
| 2 | Google login — missing id_token → 400 | unit |
| 3 | Google login — invalid token → 401 | unit (mock) |
| 4 | Google login — audience mismatch → 401 | unit (mock) |
| 5 | Apple login — valid token → 200 + JWT | unit (mock pyjwt) |
| 6 | Apple login — missing id_token → 400 | unit |
| 7 | Apple login — invalid token → 401 | unit (mock) |
| 8 | LINE login — valid access_token → 200 | unit (mock) |
| 9 | LINE login — missing token → 400 | unit |
| 10 | LINE exchange — valid code → 200 + JWT | unit (mock) |
| 11 | LINE exchange — missing code → 400 | unit |
| 12 | LINE exchange — token exchange failure → 401 | unit (mock) |
| 13 | Account merge — same email, email user → updates provider | integration |
| 14 | Account merge — same email, different social → returns existing | integration |
| 15 | Social config API — returns client IDs | integration |
| 16 | New user creation via social → role=customer | integration |

**Mock 전략**: `unittest.mock.patch('app.auth.social.requests.get')` / `.post()` 로 외부 API 호출 모킹

## Step 8: 환경변수 문서 업데이트

**수정: `backend/.env.example`** (또는 README):
```
# Social Login
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
APPLE_CLIENT_ID=com.yourcompany.glowtrip
LINE_CHANNEL_ID=your-line-channel-id
LINE_CHANNEL_SECRET=your-line-channel-secret
```

## Step 9: i18n 추가

**수정: `frontend/js/lang.js`** — 새 키 추가:
- `socialUnavailable`: " 로그인을 사용할 수 없습니다" (4개 언어)
- `socialFailed`: "소셜 로그인에 실패했습니다" (이미 존재하면 확인)
- `lineLoginFailed`: "LINE 로그인에 실패했습니다" (4개 언어)

## Step 10: 문서 업데이트

- `docs/todo.md` — Phase 17 항목 체크
- `docs/worklog/2026.04.W1.md` — 작업 기록
- `docs/CLAUDE.md` — 소셜 로그인 관련 설정 메모

---

## 생성/수정 파일 목록

| 구분 | 파일 |
|------|------|
| MODIFY | `backend/app/__init__.py` — `/api/config/social` 엔드포인트 |
| MODIFY | `backend/app/auth/social.py` — LINE exchange + 계정 병합 개선 |
| MODIFY | `frontend/index.html` — Google GSI / Apple SDK 스크립트 태그 |
| MODIFY | `frontend/js/app.js` — config 로드, socialLogin() 수정, LINE 콜백 |
| MODIFY | `frontend/js/lang.js` — i18n 키 추가 |
| NEW | `backend/tests/test_social.py` — ~16개 테스트 |
| MODIFY | `docs/todo.md`, `docs/worklog/2026.04.W1.md` |

## 검증 방법

1. 기존 테스트 전체 통과 (128개)
2. 새 소셜 로그인 테스트 ~16개 통과 (외부 API는 mock)
3. client_id 미설정 시: 소셜 버튼 disabled, 에러 없음 (graceful)
4. client_id 설정 시: Google → GSI 팝업, Apple → 팝업, LINE → 리디렉트 → 콜백 처리
5. 동일 이메일 계정 병합: 기존 email 유저 → 소셜 로그인 시 provider_id 연결

## 주의사항

- **보안**: client_secret은 절대 프론트엔드에 노출하지 않음 (LINE secret은 백엔드에서만 사용)
- **CORS**: 소셜 SDK는 프론트엔드에서 직접 호출 (CORS 이슈 없음), LINE code→token은 백엔드에서 교환
- **테스트 환경**: 실제 소셜 API 호출 없이 mock으로 테스트
- **Graceful degradation**: 환경변수 미설정 시 소셜 로그인 비활성, 에러 발생 안 함
