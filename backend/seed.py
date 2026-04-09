"""테스트용 시드 데이터 삽입 스크립트"""

import bcrypt
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv

load_dotenv()

from app import create_app, db
from app.models import User, Shop, Menu, Booking, Payment, BusinessHour, Favorite, Review, Notification

DEFAULT_PW = bcrypt.hashpw("Glow2026!".encode(), bcrypt.gensalt()).decode()

app = create_app()

with app.app_context():
    # 기존 데이터 초기화
    Notification.query.delete()
    Favorite.query.delete()
    Review.query.delete()
    Payment.query.delete()
    Booking.query.delete()
    BusinessHour.query.delete()
    Menu.query.delete()
    Shop.query.delete()
    User.query.delete()
    db.session.commit()

    # --- Users ---
    owner1 = User(
        email="owner1@glowtrip.com",
        password_hash=DEFAULT_PW,
        name="김원장",
        auth_provider="email",
        role="owner",
        language="ko",
    )
    owner2 = User(
        email="owner2@glowtrip.com",
        password_hash=DEFAULT_PW,
        name="박원장",
        auth_provider="email",
        role="owner",
        language="ko",
    )
    customer1 = User(
        email="sakura@example.com",
        password_hash=DEFAULT_PW,
        name="Sakura Tanaka",
        auth_provider="email",
        role="customer",
        language="ja",
    )
    customer2 = User(
        email="emma@example.com",
        password_hash=DEFAULT_PW,
        name="Emma Wilson",
        auth_provider="email",
        role="customer",
        language="en",
    )
    customer3 = User(
        email="xiaoming@example.com",
        password_hash=DEFAULT_PW,
        name="李小明",
        auth_provider="email",
        role="customer",
        language="zh",
    )
    admin = User(
        email="admin@glowtrip.com",
        password_hash=DEFAULT_PW,
        name="관리자",
        auth_provider="email",
        role="admin",
        language="ko",
    )
    db.session.add_all([owner1, owner2, customer1, customer2, customer3, admin])
    db.session.flush()

    # --- Shops ---
    shop1 = Shop(
        owner_id=owner1.id,
        name="글로우 스킨케어",
        description="강남역 도보 3분, 프리미엄 피부관리 전문점",
        address="서울 강남구 강남대로 123",
        latitude=37.4979,
        longitude=127.0276,
        phone="02-1234-5678",
        category="skincare",
        region="seoul",
    )
    shop2 = Shop(
        owner_id=owner2.id,
        name="뷰티랩 에스테틱",
        description="홍대입구역 근처, 합리적인 가격의 피부관리",
        address="서울 마포구 양화로 456",
        latitude=37.5563,
        longitude=126.9236,
        phone="02-9876-5432",
        category="facial",
        region="seoul",
    )
    db.session.add_all([shop1, shop2])
    db.session.flush()

    # --- Business Hours ---
    from datetime import time as dt_time
    for shop in [shop1, shop2]:
        for dow in range(7):
            bh = BusinessHour(
                shop_id=shop.id,
                day_of_week=dow,
                open_time=dt_time(10, 0),
                close_time=dt_time(20, 0),
                is_closed=(dow == 6),  # Sunday closed
            )
            db.session.add(bh)
    db.session.flush()

    # --- Menus ---
    menus = [
        Menu(shop_id=shop1.id, title="수분 광채 관리", price=80000, duration=60,
             description="건조한 피부에 깊은 수분을 공급하는 프리미엄 케어"),
        Menu(shop_id=shop1.id, title="모공 딥클렌징", price=60000, duration=45,
             description="블랙헤드·피지 집중 케어"),
        Menu(shop_id=shop1.id, title="리프팅 스페셜", price=120000, duration=90,
             description="탄력 개선 집중 안티에이징 관리"),
        Menu(shop_id=shop2.id, title="기본 피부관리", price=50000, duration=50,
             description="클렌징부터 마무리까지 기본 풀코스"),
        Menu(shop_id=shop2.id, title="여드름 집중 케어", price=70000, duration=60,
             description="트러블 피부 진정 및 관리"),
    ]
    db.session.add_all(menus)
    db.session.flush()

    # --- Bookings ---
    now = datetime.now(timezone.utc)
    booking1 = Booking(
        user_id=customer1.id,
        shop_id=shop1.id,
        menu_id=menus[0].id,
        booking_time=now + timedelta(days=3),
        status="confirmed",
        request_original="敏感肌なので、優しい製品を使ってください。",
        request_translated="민감성 피부이므로 순한 제품을 사용해 주세요.",
    )
    booking2 = Booking(
        user_id=customer2.id,
        shop_id=shop2.id,
        menu_id=menus[3].id,
        booking_time=now + timedelta(days=5),
        status="pending",
        request_original="I have sensitive skin around my eyes, please be careful.",
        request_translated="눈 주위 피부가 민감하니 조심해 주세요.",
    )
    booking3 = Booking(
        user_id=customer3.id,
        shop_id=shop1.id,
        menu_id=menus[2].id,
        booking_time=now + timedelta(days=7),
        status="pending",
        request_original="我的皮肤比较干燥，希望用保湿效果好的产品。",
        request_translated="피부가 비교적 건조하니 보습 효과가 좋은 제품을 사용해 주세요.",
    )
    db.session.add_all([booking1, booking2, booking3])
    db.session.flush()

    # --- Payments ---
    payment1 = Payment(
        booking_id=booking1.id,
        amount=80000,
        currency="KRW",
        pg_tid="EXM_TEST_001",
        payment_status="captured",
        paid_at=now,
    )
    payment2 = Payment(
        booking_id=booking2.id,
        amount=50000,
        currency="KRW",
        payment_status="pending",
    )
    payment3 = Payment(
        booking_id=booking3.id,
        amount=120000,
        currency="KRW",
        payment_status="pending",
    )
    db.session.add_all([payment1, payment2, payment3])
    db.session.commit()

    print("Seed data inserted successfully!")
    print(f"  Users: {User.query.count()}")
    print(f"  Shops: {Shop.query.count()}")
    print(f"  Menus: {Menu.query.count()}")
    print(f"  Bookings: {Booking.query.count()}")
    print(f"  Payments: {Payment.query.count()}")
