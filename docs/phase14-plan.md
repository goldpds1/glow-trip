# Phase 14 구현 플랜 — UI 리뉴얼 (디자인 목업 적용)

> 디자인 시안 4개 화면 (Home / Clinic List / Shop Detail / Booking) 기준
> 현재 CSS: 퍼플(#7C5CFC) → 목표: 베이지/크림 + 세이지 그린

---

## 실행 순서 총괄

```
14-A (CSS 기반)  ─→  14-B (홈+목록)  ─→  14-C (상세)  ─→  14-D (예약+백엔드)  ─→  14-E (i18n+테스트)
     ↓                   ↓                  ↓                  ↓
  style.css          shops API           app.js            모델+마이그레이션
  index.html         app.js              index.html        owner.html
  lang.js            lang.js                               테스트
```

---

## 14-A. CSS + 레이아웃 리뉴얼

### 변경 파일: `frontend/css/style.css`

**1) 컬러 시스템 교체**

| 변수 | 현재 | 변경 | 목업 근거 |
|------|------|------|----------|
| `--primary` | `#7C5CFC` (퍼플) | `#6B8F71` (세이지 그린) | Book Now 버튼, 선택된 날짜 |
| `--primary-light` | `#A78BFA` | `#8BAF92` | 호버/라이트 |
| `--bg` | `#F9FAFB` | `#FAF8F5` | 전체 배경 (웜 톤) |
| `--card` | `#FFFFFF` | `#FFFFFF` | 유지 |
| `--text` | `#1F2937` | `#2D2D2D` | 약간 소프트 |
| `--text-light` | `#6B7280` | `#8E8E8E` | 서브텍스트 |
| `--border` | `#E5E7EB` | `#E8E4DF` | 웜 보더 |
| `--shadow` | 현재 | `0 2px 8px rgba(0,0,0,.06)` | 더 부드러운 그림자 |
| 추가: `--accent-bg` | - | `#F5F0EB` | 카테고리 태그, 선택되지 않은 슬롯 배경 |
| 추가: `--primary-bg` | - | `#EDF5EE` | 선택된 항목 배경 |

**2) 타이포그래피**

```css
body { font-family: 'Pretendard', -apple-system, ..., sans-serif; }
```
- Google Fonts 또는 CDN으로 Pretendard 로드 (한글+영문 조합 우수)
- 대안: 현재 시스템 폰트 유지하되 weight/size만 조정

**3) 헤더 리뉴얼**

현재: `Glow Trip | [lang selector]`
목표: `← Clinic List ≡` (중앙 타이틀 + 좌측 뒤로가기 + 우측 액션)

```
변경사항:
- .header { justify-content: center; position: relative; }
- .header h1 { font-size: 17px; font-weight: 600; text-align: center; }
- .back-btn { position: absolute; left: 16px; }
- #headerRight { position: absolute; right: 16px; }
```

**4) 하단 네비게이션**

현재: 이모지 아이콘 + 텍스트 (Shops/Bookings/My)
목표: SVG 아이콘 + 텍스트 (Home/Shops/Profile)

```
변경사항 (index.html):
- nav-shops → nav-home (홈 화면으로 변경)
- nav-bookings → nav-shops (샵 목록)
- nav-mypage → nav-profile (프로필)
- 이모지 → SVG 아이콘 (home, building, user)
```

> **주의**: 라우팅 구조 변경 — Home(홈)과 Shops(샵 목록)를 분리

**5) 시작 화면 (Splash/Auth)**

현재: 바로 로그인 폼
목표: 로고 + 한 줄 소개 → 로그인/회원가입 버튼 → 탭 전환

```
변경사항 (index.html):
- #page-auth에 스플래시 섹션 추가
  - Glow Trip 로고 (텍스트 또는 SVG)
  - "Find your beauty in Korea" 한 줄 소개
  - [Login] [Sign Up] 버튼 2개
  - 하단 언어 선택
- 버튼 클릭 시 로그인/회원가입 폼 표시 (기존 구조 활용)
```

### 변경 파일 요약 (14-A)

| 파일 | 변경 내용 |
|------|----------|
| `style.css` | CSS 변수 12개 교체, 헤더/네비/카드/버튼 스타일 전면 변경 |
| `index.html` | 헤더 구조, 하단 네비 아이콘, Auth 스플래시 섹션 |
| `app.js` | 네비게이션 라우트맵 수정 (home/shops 분리) |

---

## 14-B. 홈 + 샵 목록 리뉴얼

### 백엔드 변경

**1) Shop 모델에 category 추가**

```python
# backend/app/models/shop.py
category = db.Column(db.String(50), nullable=True)  # skincare, massage, waxing, facial, body, etc.
```

마이그레이션: `flask db migrate -m "add_shop_category"`

**2) Shops API 수정** (`backend/app/api/shops.py`)

```python
# 쿼리 파라미터 추가
category = request.args.get("category")
if category:
    q = q.filter_by(category=category)

# 응답에 min_price 추가 (서브쿼리)
min_price = db.session.query(db.func.min(Menu.price)).filter(
    Menu.shop_id == shop.id, Menu.is_active == True
).scalar()

# 응답에 review_count 추가
```

**3) 인기 샵 API** (`backend/app/api/shops.py`)

```python
# GET /api/shops/popular — 예약 수 기준 Top 10
@shops_bp.route("/popular", methods=["GET"])
def popular_shops():
    ...
```

### 프론트엔드 변경

**4) 홈 화면 (신규 page-home)**

```
┌─────────────────────────┐
│  🔍 Select a location ▾  │ ← 검색바 + 지역 드롭다운
├─────────────────────────┤
│ [Hydra facial] [Massage] │ ← 카테고리 태그 (가로 스크롤)
│ [Waxing] [Skincare]      │
├─────────────────────────┤
│ 관심 시술로 검색하기       │ ← 섹션 헤더
│ ┌────┐ ┌────┐            │
│ │img │ │img │            │ ← 카드 2열 그리드
│ │name│ │name│            │
│ │★4.8│ │★4.7│            │
│ └────┘ └────┘            │
├─────────────────────────┤
│ Popular Clinics  더보기 > │ ← 섹션 헤더
│ ┌────┐ ┌────┐            │
│ │img │ │img │            │ ← 가로 스크롤 카드
│ │name│ │name│            │
│ │from│ │from│            │
│ └────┘ └────┘            │
└─────────────────────────┘
```

변경 파일:
- `index.html` — `<div id="page-home">` 신규 섹션 추가
- `app.js` — `loadHome()`, `loadPopularShops()`, `filterByCategory()` 함수 추가
- `style.css` — `.category-tag`, `.home-section`, `.horizontal-scroll` 추가

**5) 샵 목록 (page-shops 리뉴얼)**

현재: 단순 카드 리스트
목표: 목업의 Clinic List 화면

```
┌─────────────────────────┐
│ ← Clinic List         ≡ │
├─────────────────────────┤
│ 📍Seoul ▾ [Skincare][..] │ ← 위치+카테고리 필터
├─────────────────────────┤
│ ┌──────────────────────┐│
│ │ [     shop image    ]││
│ │ Gangnam Glow Aesthe. ││
│ │ ★4.9 ★★★★☆ (105)    ││
│ │ 120,000 KRW~  [Book] ││
│ └──────────────────────┘│
│ ┌──────────────────────┐│
│ │ [     shop image    ]││
│ │ Seoul Beauty Therapy ││
│ │ 100,000 KRW~ [Book]  ││
│ └──────────────────────┘│
└─────────────────────────┘
```

변경:
- 카드 레이아웃: 가로형(현재) → 세로형 (이미지 위, 정보 아래)
- `min_price` 표시: "120,000 KRW~"
- `review_count` 표시: "(105 reviews)"
- Book Now 버튼 인라인 배치

### 변경 파일 요약 (14-B)

| 파일 | 변경 내용 |
|------|----------|
| `models/shop.py` | `category` 필드 추가 |
| `api/shops.py` | category 필터, min_price, review_count, popular 엔드포인트 |
| `index.html` | page-home 신규, page-shops 카드 구조 변경 |
| `app.js` | loadHome, loadPopularShops, filterByCategory, 라우팅 변경 |
| `style.css` | 카테고리 태그, 세로 카드, 가로 스크롤 스타일 |
| 마이그레이션 | `add_shop_category.py` |
| `seed.py` | 기존 샵에 category 데이터 추가 |

### 테스트 추가

```python
# tests/test_shops.py 에 추가
def test_shops_filter_by_category(...)
def test_shops_response_has_min_price(...)
def test_shops_response_has_review_count(...)
def test_popular_shops(...)
```

---

## 14-C. 샵 상세 리뉴얼

### 프론트엔드 변경만 (백엔드 변경 없음)

**현재 openShop() 렌더링:**
```
[이미지] (margin 있음)
[카드: 이름+설명+주소+전화]
[지도]
[카드: 메뉴 목록]
[카드: 리뷰]
```

**목업 기준 변경:**
```
┌─────────────────────────┐
│ [   히어로 이미지 전폭   ] │ ← 상단 전폭, 높이 250px
│  ←              ♡  🔖   │ ← 오버레이 아이콘
├─────────────────────────┤
│ Gangnam Glow Aesthetic   │ ← 이름 (20px, bold)
│ ★4.9 ★★★★☆ (105 reviews)│ ← 별점+리뷰수
│ 📍 Location: Gangnam, .. │ ← 위치 배지
├─────────────────────────┤
│ About Us                 │
│ Premium skincare and...  │ ← description
├─────────────────────────┤
│ Services                 │
│ ┌──────────────────────┐│
│ │ [img] Crystal Bright. ││ ← 이미지+제목+가격+시간
│ │       150,000 KRW/60m ││
│ └──────────────────────┘│
│ ┌──────────────────────┐│
│ │ [img] Aroma Body      ││
│ │       90,000 KRW/50m  ││
│ └──────────────────────┘│
├─────────────────────────┤
│ Reviews                  │
│ ★4.9 (105 reviews)      │
│ [개별 리뷰 리스트]        │
├─────────────────────────┤
│         [  Book Now  ]   │ ← 하단 고정 버튼 (sticky)
└─────────────────────────┘
```

### 변경 상세

**`app.js` — openShop() 재작성**
- 히어로 이미지: `width:100%; height:250px; object-fit:cover` (margin 없이 전폭)
- 뒤로가기: 이미지 위 absolute 배치, 반투명 원형 배경
- 하트/북마크: 이미지 우상단 absolute (기능은 UI만, onclick은 빈 함수)
- 메뉴 카드: 이미지+텍스트 가로 배치, 가격과 시간을 한 줄에 "150,000 KRW / 60 min"
- Book Now: 하단 고정 (`position:sticky; bottom:0`)
- 메뉴 클릭 → 선택 표시 (체크마크/하이라이트) → Book Now로 예약 진행

**`style.css` 추가**
```css
.hero-image { width:100%; height:250px; object-fit:cover; }
.hero-overlay { position:absolute; top:16px; display:flex; justify-content:space-between; width:100%; padding:0 16px; }
.hero-back, .hero-action { width:36px; height:36px; border-radius:50%; background:rgba(255,255,255,.8); display:flex; align-items:center; justify-content:center; }
.sticky-book-btn { position:sticky; bottom:0; padding:16px; background:var(--card); border-top:1px solid var(--border); }
.service-card { display:flex; gap:12px; padding:14px 0; border-bottom:1px solid var(--border); }
.service-image { width:64px; height:64px; border-radius:8px; object-fit:cover; }
```

### 변경 파일 요약 (14-C)

| 파일 | 변경 내용 |
|------|----------|
| `app.js` | `openShop()` HTML 템플릿 전면 재작성 |
| `style.css` | 히어로, 오버레이, 서비스 카드, sticky 버튼 스타일 |
| `index.html` | page-shop-detail 구조 미세 조정 (sticky 버튼 영역) |

---

## 14-D. 예약 화면 리뉴얼 + 타임슬롯

### 백엔드 변경 (가장 큰 변경)

**1) BusinessHour 모델 신규 생성**

```python
# backend/app/models/business_hour.py
class BusinessHour(db.Model):
    __tablename__ = "business_hours"
    id = db.Column(db.UUID, primary_key=True, default=uuid.uuid4)
    shop_id = db.Column(db.UUID, db.ForeignKey("shops.id"), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Mon ~ 6=Sun
    open_time = db.Column(db.Time, nullable=False)        # e.g. 10:00
    close_time = db.Column(db.Time, nullable=False)       # e.g. 20:00
    is_closed = db.Column(db.Boolean, default=False)       # 휴무일
```

마이그레이션: `flask db migrate -m "add_business_hours"`

**2) 타임슬롯 API**

```python
# backend/app/api/shops.py
@shops_bp.route("/<shop_id>/slots", methods=["GET"])
def available_slots(shop_id):
    """
    GET /api/shops/:id/slots?date=2026-04-10&menu_id=xxx

    로직:
    1. 해당 요일의 BusinessHour 조회 (open_time ~ close_time)
    2. duration(분) 단위로 30분 간격 슬롯 생성
    3. 이미 예약된 시간대 제외 (Booking 테이블 조회)
    4. 과거 시간 제외

    응답:
    {
      "date": "2026-04-10",
      "day_of_week": 4,
      "is_closed": false,
      "open_time": "10:00",
      "close_time": "20:00",
      "slots": [
        {"time": "10:00", "available": true},
        {"time": "10:30", "available": true},
        {"time": "11:00", "available": false},  // 이미 예약됨
        ...
      ]
    }
    """
```

**3) 원장님 영업시간 관리 API**

```python
# backend/app/api/owner.py 에 추가
@owner_bp.route("/shops/<shop_id>/hours", methods=["GET"])
# 현재 영업시간 조회

@owner_bp.route("/shops/<shop_id>/hours", methods=["PUT"])
# 영업시간 일괄 저장 (7일치)
```

### 프론트엔드 변경

**4) 예약 화면 (page-booking 재작성)**

현재: `<input type="datetime-local">`
목표: 날짜 피커 + 타임슬롯 그리드

```
┌─────────────────────────┐
│ ←      Booking          │
├─────────────────────────┤
│ Select Date              │
│ [26][27][28][29][●30][31]│ ← 가로 스크롤 날짜 (2주)
│                    [1May]│
├─────────────────────────┤
│ Select Time              │
│ [10:00] [●11:00] [2:00] │ ← 타임슬롯 그리드
│ [ 3:00] [ 3:30 ] [4:00] │   (비활성=회색, 선택=그린)
├─────────────────────────┤
│ Special Requests         │
│ ┌──────────────────────┐│
│ │ Please enter your... ││ ← 텍스트영역
│ └──────────────────────┘│
├─────────────────────────┤
│ Crystal Brightening      │ ← 선택된 메뉴 요약
│ 150,000 KRW / 60 min    │
├─────────────────────────┤
│  [ Next ]  [ Pay Now ]   │ ← 2단계 버튼
└─────────────────────────┘
```

**`app.js` 추가 함수:**
```javascript
function renderDatePicker(shopId)     // 오늘~14일 후 가로 스크롤 날짜
function selectDate(date)              // 날짜 선택 → loadSlots 호출
async function loadSlots(shopId, date, menuId)  // API 호출 → 슬롯 렌더
function selectSlot(time)              // 슬롯 선택 → 하이라이트
function goToPayment()                 // Next 버튼 → 결제 화면
```

**`index.html` page-booking 구조:**
```html
<div id="page-booking" class="page">
  <div class="px-16 mt-16">
    <h3>Select Date</h3>
    <div id="datePicker" class="date-scroll"></div>
    <h3 class="mt-16">Select Time</h3>
    <div id="timeSlots" class="slot-grid"></div>
    <h3 class="mt-16">Special Requests</h3>
    <textarea class="form-input" id="bookingRequest" ...></textarea>
    <div id="bookingSummary" class="mt-16"></div>
    <div id="bookingError" class="hidden" ...></div>
    <div class="booking-actions mt-16">
      <button class="btn btn-outline" onclick="createBooking()">Next</button>
      <button class="btn btn-primary" onclick="createBookingAndPay()">Pay Now</button>
    </div>
  </div>
</div>
```

**`style.css` 추가:**
```css
.date-scroll { display:flex; gap:8px; overflow-x:auto; padding:8px 0; }
.date-item { min-width:48px; text-align:center; padding:10px 8px; border-radius:12px; border:1px solid var(--border); cursor:pointer; }
.date-item.selected { background:var(--primary); color:#fff; border-color:var(--primary); }
.date-item.today { font-weight:700; }

.slot-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:8px; }
.slot-item { padding:10px; text-align:center; border-radius:8px; border:1px solid var(--border); cursor:pointer; font-size:14px; }
.slot-item.selected { background:var(--primary); color:#fff; }
.slot-item.unavailable { background:var(--accent-bg); color:var(--text-light); cursor:not-allowed; opacity:.5; }

.booking-actions { display:flex; gap:12px; }
.booking-actions .btn { flex:1; }
```

**5) 예약 완료 화면 (page-booking-complete 신규)**

```
┌─────────────────────────┐
│       ✓ Booking          │
│       Complete!          │
├─────────────────────────┤
│ Gangnam Glow Aesthetic   │
│ Crystal Brightening      │
│ 2026-04-10 (Thu) 11:00  │
│ 150,000 KRW              │
├─────────────────────────┤
│    [ View Bookings ]     │
│    [ Back to Home  ]     │
└─────────────────────────┘
```

**6) 결제 화면 — 환불 규정 추가**

```html
<!-- page-payment에 추가 -->
<div class="refund-policy">
  <h4 data-i18n="refundPolicy"></h4>
  <ul>
    <li data-i18n="refundRule1"></li>  <!-- 24시간 전: 전액 환불 -->
    <li data-i18n="refundRule2"></li>  <!-- 24시간 이내: 환불 불가 -->
  </ul>
</div>
```

**7) 원장님 대시보드 — 스케줄 관리 탭**

`owner.html`에 5번째 탭 "Schedule" 추가:

```
┌─────────────────────────┐
│ 월 [10:00] ~ [20:00] ☑  │
│ 화 [10:00] ~ [20:00] ☑  │
│ 수 [10:00] ~ [20:00] ☑  │
│ 목 [10:00] ~ [20:00] ☑  │
│ 금 [10:00] ~ [20:00] ☑  │
│ 토 [11:00] ~ [18:00] ☑  │
│ 일 [  휴무  ]         ☐  │
│                          │
│       [ Save ]           │
└─────────────────────────┘
```

### 변경 파일 요약 (14-D)

| 파일 | 변경 내용 |
|------|----------|
| `models/business_hour.py` | **신규** — BusinessHour 모델 |
| `models/__init__.py` | BusinessHour import 추가 |
| `api/shops.py` | `GET /shops/:id/slots` 타임슬롯 API |
| `api/owner.py` | `GET/PUT /owner/shops/:id/hours` 영업시간 관리 |
| `api/bookings.py` | 예약 시 슬롯 유효성 검증 추가 |
| `index.html` | page-booking 재작성, page-booking-complete 신규 |
| `app.js` | 날짜 피커, 슬롯 로딩, 선택 로직, 완료 화면 |
| `owner.html` | Schedule 탭 + 영업시간 CRUD UI |
| `style.css` | 날짜 스크롤, 슬롯 그리드, 완료 화면, 환불 규정 |
| 마이그레이션 | `add_business_hours.py` |

### 테스트 추가

```python
# tests/test_timeslots.py (신규)
def test_get_slots_normal_day(...)         # 정상 영업일 슬롯 반환
def test_get_slots_closed_day(...)         # 휴무일 빈 슬롯
def test_get_slots_excludes_booked(...)    # 예약된 시간 제외
def test_get_slots_excludes_past(...)      # 과거 시간 제외
def test_get_slots_no_hours_set(...)       # 영업시간 미설정 시 기본값

# tests/test_business_hours.py (신규)
def test_owner_get_hours(...)              # 영업시간 조회
def test_owner_set_hours(...)              # 영업시간 저장
def test_owner_set_hours_not_owner(...)    # 권한 검증
def test_owner_set_closed_day(...)         # 휴무일 설정
```

---

## 14-E. i18n + 마무리

### `frontend/js/lang.js` 추가 키

```javascript
// 14-A: 시작 화면
findBeauty: 'Find your beauty in Korea',

// 14-B: 홈/목록
home: '홈',
popularClinics: '인기 클리닉',
viewMore: '더보기',
fromPrice: '~부터',
allCategories: '전체',

// 14-C: 샵 상세
aboutUs: '소개',
services: '시술 목록',
bookNowFixed: '예약하기',

// 14-D: 예약
selectDate: '날짜 선택',
selectTime: '시간 선택',
specialRequests: '요청사항',
next: '다음',
payNow: '결제하기',
bookingComplete: '예약이 완료되었습니다!',
viewBookings: '예약 내역 보기',
backToHome: '홈으로 돌아가기',
refundPolicy: '취소/환불 규정',
refundRule1: '24시간 전 취소: 전액 환불',
refundRule2: '24시간 이내 취소: 환불 불가',
closed: '휴무',

// 14-D: 원장님
schedule: '스케줄',
openTime: '오픈',
closeTime: '마감',
```

4개 언어 (ko/en/ja/zh) 모두 추가.

### 카테고리 다국어

```javascript
const CATEGORIES = {
  skincare: { ko: '스킨케어', en: 'Skincare', ja: 'スキンケア', zh: '护肤' },
  massage:  { ko: '마사지',   en: 'Massage',  ja: 'マッサージ', zh: '按摩' },
  facial:   { ko: '페이셜',   en: 'Facial',   ja: 'フェイシャル', zh: '面部护理' },
  waxing:   { ko: '왁싱',     en: 'Waxing',   ja: 'ワキシング', zh: '脱毛' },
  body:     { ko: '바디',     en: 'Body',     ja: 'ボディ',     zh: '身体护理' },
};
```

### 전체 테스트 실행

```bash
docker compose exec api bash -c \
  "TEST_DATABASE_URL=postgresql://glowtrip:glowtrip@db:5432/glowtrip_test \
   python -m pytest tests/ -v"
```

목표: **전체 100개+ 테스트 통과**

---

## 작업량 예측 + 의존성

| 서브페이즈 | 파일 변경 수 | 신규 파일 | 핵심 난이도 |
|-----------|------------|----------|-----------|
| 14-A | 3 (css, html, js) | 0 | 낮음 — CSS 변수 교체 + 레이아웃 조정 |
| 14-B | 6 + 마이그레이션 | 0 | 중간 — 홈 화면 신규, API 응답 확장 |
| 14-C | 3 (js, css, html) | 0 | 낮음 — openShop() 템플릿 재작성 |
| 14-D | 8 + 마이그레이션 | 2 (모델, 테스트) | **높음** — 타임슬롯 로직, 새 모델 |
| 14-E | 1 (lang.js) | 0 | 낮음 — 번역 키 추가 |

**의존성 체인**: A → B (CSS 기반 필요) → C (카드 스타일 필요) → D (독립적이지만 CSS 활용) → E (모든 텍스트 수집 후)

---

## 리스크 & 대응

| 리스크 | 대응 |
|--------|------|
| 홈/샵 목록 라우팅 분리 시 기존 딥링크 깨짐 | ROUTE_MAP에 `/` → home, `/shops` → shops 매핑 추가 |
| 타임슬롯 계산 복잡도 (시간대, 메뉴 duration 고려) | 1차는 30분 고정 간격으로 단순화, 이후 메뉴별 duration 반영 |
| 영업시간 미설정 샵 | 기본값 10:00~20:00, 월~토 영업 적용 |
| 목업과 100% 동일한 비주얼 달성 어려움 | 레이아웃+색감+비율 우선, 픽셀 퍼펙트보다 느낌 일치에 집중 |
