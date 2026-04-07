# Phase 16: 사용자 경험 개선 — 실행 플랜

> 프로필 수정, 즐겨찾기(관심 샵), 샵 필터/정렬 확장

---

## 16-A. 프로필 수정 API & UI

### Backend
1. **프로필 수정 API** — `PATCH /api/auth/me`
   - 수정 가능 필드: `name`, `phone`, `language`
   - `@login_required` 인증 필수
   - 유효성 검사 (name 최대 100자, phone 최대 30자, language는 ko/en/ja/zh만 허용)
   - 변경된 필드만 업데이트

2. **테스트** — `tests/test_auth.py`에 프로필 수정 테스트 추가
   - 정상 수정, 부분 수정, 잘못된 language 값, 미인증 요청

### Frontend
3. **마이페이지 프로필 수정 UI**
   - 현재 정보 표시 → "Edit" 버튼 클릭 시 편집 모드
   - 이름, 전화번호 입력 필드 + 언어 선택 드롭다운
   - Save / Cancel 버튼
   - 저장 성공 시 토스트 표시 + 표시 모드로 복귀

4. **i18n** — `lang.js`에 프로필 관련 키 추가 (4개 언어)
   - `editProfile`, `profileName`, `profilePhone`, `profileLang`, `profileSave`, `profileCancel`, `profileUpdated`

---

## 16-B. 즐겨찾기 (관심 샵) 백엔드 + UI 연결

### Backend
5. **favorites 테이블 생성** — 마이그레이션
   - `id` (UUID PK), `user_id` (FK→users), `shop_id` (FK→shops), `created_at`
   - unique constraint: (user_id, shop_id)

6. **즐겨찾기 API** 3개
   - `POST /api/favorites/<shop_id>` — 추가 (toggle: 이미 있으면 삭제)
   - `GET /api/favorites` — 내 즐겨찾기 목록 (샵 정보 포함)
   - `GET /api/favorites/check/<shop_id>` — 특정 샵 즐겨찾기 여부

7. **테스트** — `tests/test_favorites.py`
   - 추가/삭제 토글, 목록 조회, 중복 확인, 미인증 요청

### Frontend
8. **하트 버튼 백엔드 연결**
   - 현재 UI만 있는 `toggleFav()` → API 호출로 변경
   - 샵 상세 진입 시 즐겨찾기 여부 체크 → 하트 상태 반영
   - 샵 카드의 하트도 동일 연동

9. **마이페이지 — 즐겨찾기 섹션**
   - "My Favorites" 섹션 추가
   - 즐겨찾기 샵 카드 목록 표시 (기존 shop-v-card 재활용)
   - 비어있을 때 안내 메시지

10. **i18n** — 즐겨찾기 관련 키 추가
    - `myFavorites`, `noFavorites`, `favSection`

---

## 16-C. 샵 필터/정렬 확장

### Backend
11. **샵 목록 API 필터 확장** — `GET /api/shops`
    - `price_min` / `price_max` — 최저 메뉴 가격 기준 필터
    - `min_rating` — 최소 평점 필터
    - `sort=rating` — 평균 평점 높은 순 정렬
    - `sort=price` — 최저가 순 정렬
    - 기존 `sort=distance`, `sort=popular` 유지

12. **테스트** — `tests/test_shops.py`에 필터/정렬 테스트 추가

### Frontend
13. **샵 목록 필터 UI**
    - 필터 바 또는 필터 모달: 가격대 (min/max 입력), 최소 평점 (별 선택)
    - 정렬 드롭다운: 최신순 / 인기순 / 평점순 / 가격순 / 거리순
    - 필터 적용 시 API 재호출

14. **i18n** — 필터 관련 키 추가
    - `filterPrice`, `filterRating`, `sortNewest`, `sortPopular`, `sortRating`, `sortPrice`, `sortDistance`, `filterApply`, `filterReset`, `priceRange`, `minRating`

---

## 작업 순서

| 순서 | 작업 | 예상 범위 |
|------|------|-----------|
| 1 | 16-A: 프로필 수정 API + 테스트 | Backend |
| 2 | 16-A: 프로필 수정 UI + i18n | Frontend |
| 3 | 16-B: favorites 모델 + 마이그레이션 | Backend |
| 4 | 16-B: 즐겨찾기 API + 테스트 | Backend |
| 5 | 16-B: 하트 연동 + 마이페이지 즐겨찾기 UI + i18n | Frontend |
| 6 | 16-C: 샵 필터/정렬 API 확장 + 테스트 | Backend |
| 7 | 16-C: 필터 UI + i18n | Frontend |
| 8 | 전체 테스트 통과 확인 | QA |
| 9 | docs 업데이트 (todo.md, worklog) | Docs |

---

## 영향 파일

| 파일 | 변경 내용 |
|------|-----------|
| `backend/app/auth/routes.py` | PATCH /api/auth/me 추가 |
| `backend/app/models/favorite.py` | **신규** — Favorite 모델 |
| `backend/app/models/__init__.py` | Favorite import 추가 |
| `backend/app/api/favorites.py` | **신규** — 즐겨찾기 API Blueprint |
| `backend/app/__init__.py` | favorites Blueprint 등록 |
| `backend/app/api/shops.py` | 필터/정렬 파라미터 확장 |
| `backend/tests/test_auth.py` | 프로필 수정 테스트 |
| `backend/tests/test_favorites.py` | **신규** — 즐겨찾기 테스트 |
| `backend/tests/test_shops.py` | 필터/정렬 테스트 |
| `frontend/js/app.js` | 마이페이지 편집 UI, 즐겨찾기 연동, 필터 UI |
| `frontend/js/lang.js` | i18n 키 추가 |
| `frontend/css/style.css` | 프로필 편집, 필터 UI 스타일 |
