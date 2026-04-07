# Glow Trip Database Schema

> PostgreSQL 16 / SQLAlchemy ORM / UUID Primary Keys / UTC Timestamps

---

## ER Diagram (Text)

```
users ──< shops ──< menus
  │         │         │
  │         │         │
  ├──< bookings >──┘
  │         │
  │         ├──── payments (1:1)
  │         ├──── reviews (1:1)
  │         └──< notifications
  │                   │
  └───────────────────┘ (recipient)

shops ──< business_hours

users ──< favorites >── shops
```

---

## 1. users

사용자 (고객 / 원장 / 관리자)

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | UUID | NO | uuid4() | **PK** |
| email | String(255) | NO | - | **UNIQUE** |
| password_hash | String(255) | YES | - | - |
| auth_provider | String(50) | NO | `"email"` | email / google / apple / line |
| provider_id | String(255) | YES | - | 소셜 로그인 ID |
| name | String(100) | YES | - | - |
| phone | String(30) | YES | - | - |
| language | String(10) | NO | `"en"` | ko / en / ja / zh |
| role | String(20) | NO | `"customer"` | customer / owner / admin |
| created_at | DateTime(tz) | NO | now(UTC) | - |

**Relationships:** shops (1:N), bookings (1:N)

---

## 2. shops

에스테틱 샵

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | UUID | NO | uuid4() | **PK** |
| owner_id | UUID | NO | - | **FK** → users.id |
| name | String(200) | NO | - | - |
| description | Text | YES | - | - |
| address | String(300) | YES | - | - |
| latitude | Float | YES | - | Google Maps 연동 |
| longitude | Float | YES | - | Google Maps 연동 |
| phone | String(30) | YES | - | - |
| category | String(50) | YES | - | skincare / massage / facial / waxing / body |
| image_url | String(500) | YES | - | 대표 이미지 |
| is_active | Boolean | NO | `True` | 관리자 활성/비활성 |
| created_at | DateTime(tz) | NO | now(UTC) | - |

**Relationships:** owner (N:1 → users), menus (1:N), bookings (1:N), business_hours (1:N)

---

## 3. menus

시술 메뉴

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | UUID | NO | uuid4() | **PK** |
| shop_id | UUID | NO | - | **FK** → shops.id |
| title | String(200) | NO | - | - |
| description | Text | YES | - | - |
| price | Integer | NO | - | 원(KRW) 단위 |
| duration | Integer | NO | - | 분 단위 |
| image_url | String(500) | YES | - | 메뉴 이미지 |
| is_active | Boolean | NO | `True` | - |
| created_at | DateTime(tz) | NO | now(UTC) | - |

**Relationships:** shop (N:1 → shops)

---

## 4. bookings

예약

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | UUID | NO | uuid4() | **PK** |
| user_id | UUID | NO | - | **FK** → users.id |
| shop_id | UUID | NO | - | **FK** → shops.id |
| menu_id | UUID | NO | - | **FK** → menus.id |
| booking_time | DateTime(tz) | NO | - | 예약 일시 |
| status | String(20) | NO | `"pending"` | 아래 상태 전이 참고 |
| request_original | Text | YES | - | 고객 요청사항 원문 |
| request_translated | Text | YES | - | AI 한국어 번역본 |
| created_at | DateTime(tz) | NO | now(UTC) | - |

**Status 전이:**
```
pending ─→ confirmed ─→ completed
   │            │
   │            ├─→ noshow
   │            │
   │            └─→ cancelled
   │
   └─→ cancelled
```

**Relationships:** user (N:1), shop (N:1), menu (N:1), payment (1:1), notifications (1:N)

---

## 5. payments

결제 (Stripe PaymentIntent)

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | UUID | NO | uuid4() | **PK** |
| booking_id | UUID | NO | - | **FK** → bookings.id, **UNIQUE** |
| amount | Integer | NO | - | 원(KRW) 단위 |
| currency | String(3) | NO | `"KRW"` | - |
| pg_tid | String(200) | YES | - | Stripe PaymentIntent ID |
| payment_status | String(20) | NO | `"pending"` | 아래 상태 참고 |
| paid_at | DateTime(tz) | YES | - | 매입 확정 시점 |
| created_at | DateTime(tz) | NO | now(UTC) | - |

**Payment Status 전이:**
```
pending ─→ authorized ─→ captured ─→ refunded
   │                         │
   └─→ failed           refunded
```

**Relationships:** booking (1:1 → bookings)

---

## 6. reviews

리뷰/평점

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | UUID | NO | uuid4() | **PK** |
| user_id | UUID | NO | - | **FK** → users.id |
| shop_id | UUID | NO | - | **FK** → shops.id |
| booking_id | UUID | NO | - | **FK** → bookings.id, **UNIQUE** |
| rating | Integer | NO | - | 1~5 |
| comment | Text | YES | - | - |
| created_at | DateTime(tz) | NO | now(UTC) | - |

**비즈니스 규칙:** completed 상태 예약에만 작성 가능, 예약당 1개

**Relationships:** user (N:1), shop (N:1), booking (1:1)

---

## 7. business_hours

영업시간 (요일별)

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | UUID | NO | uuid4() | **PK** |
| shop_id | UUID | NO | - | **FK** → shops.id |
| day_of_week | Integer | NO | - | 0=월 ~ 6=일 |
| open_time | Time | NO | - | 오픈 시간 |
| close_time | Time | NO | - | 마감 시간 |
| is_closed | Boolean | NO | `False` | 휴무일 여부 |

**Unique Constraint:** `uq_shop_day` (shop_id, day_of_week)

**비즈니스 규칙:** 미설정 시 기본 10:00~20:00 적용 (API 레벨)

---

## 8. notifications

알림 발송 이력

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | UUID | NO | uuid4() | **PK** |
| booking_id | UUID | NO | - | **FK** → bookings.id |
| recipient_id | UUID | NO | - | **FK** → users.id |
| channel | String(20) | NO | - | email / push |
| notification_type | String(50) | NO | - | 아래 타입 참고 |
| status | String(20) | NO | `"pending"` | pending / sent / failed |
| error_message | Text | YES | - | 실패 시 에러 메시지 |
| created_at | DateTime(tz) | NO | now(UTC) | - |
| sent_at | DateTime(tz) | YES | - | 발송 성공 시점 |

**Notification Types:**
`booking_created`, `booking_confirmed`, `booking_cancelled`, `booking_completed`, `booking_noshow`, `payment_failed`, `payment_refunded`, `booking_reminder`

**Relationships:** booking (N:1), recipient (N:1 → users)

---

## 9. favorites

즐겨찾기 (관심 샵)

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | UUID | NO | uuid4() | **PK** |
| user_id | UUID | NO | - | **FK** → users.id |
| shop_id | UUID | NO | - | **FK** → shops.id |
| created_at | DateTime(tz) | NO | now(UTC) | - |

**Unique Constraint:** `uq_user_shop_favorite` (user_id, shop_id)

**Relationships:** user (N:1 → users), shop (N:1 → shops)

---

## Migration History

| # | Migration ID | Description |
|---|-------------|-------------|
| 1 | `04e99f5375c2` | 초기 테이블 생성 (users, shops, menus, bookings, payments) |
| 2 | `e9f809bd1cd0` | menus.image_url 추가 |
| 3 | `6494764af96f` | reviews 테이블 생성 |
| 4 | `9f0e296755a1` | shops.category 추가 |
| 5 | `855a2844e713` | business_hours 테이블 생성 |
| 6 | `f0b7cac65f31` | notifications 테이블 생성 |
| 7 | `8c7e7373e48d` | favorites 테이블 생성 |

---

## Key Constraints Summary

| Constraint | Table | Columns |
|-----------|-------|---------|
| UNIQUE | users | email |
| UNIQUE | payments | booking_id |
| UNIQUE | reviews | booking_id |
| UNIQUE | business_hours | (shop_id, day_of_week) |
| FK | shops | owner_id → users.id |
| FK | menus | shop_id → shops.id |
| FK | bookings | user_id → users.id |
| FK | bookings | shop_id → shops.id |
| FK | bookings | menu_id → menus.id |
| FK | payments | booking_id → bookings.id |
| FK | reviews | user_id → users.id |
| FK | reviews | shop_id → shops.id |
| FK | reviews | booking_id → bookings.id |
| FK | business_hours | shop_id → shops.id |
| FK | notifications | booking_id → bookings.id |
| FK | notifications | recipient_id → users.id |
| UNIQUE | favorites | (user_id, shop_id) |
| FK | favorites | user_id → users.id |
| FK | favorites | shop_id → shops.id |
