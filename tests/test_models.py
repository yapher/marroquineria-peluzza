# tests/test_models.py
"""
Tests de modelos: User, Product, Category, Coupon, Review, Wishlist.
"""
from decimal import Decimal
from app.models import User, Category, Product, Coupon, Review, Wishlist


class TestUserModel:
    def test_create_user(self, db):
        u = User(email="a@b.com", first_name="Ana", last_name="Lopez")
        u.set_password("secret")
        db.session.add(u)
        db.session.commit()

        assert u.id is not None
        assert u.email == "a@b.com"
        assert u.full_name == "Ana Lopez"
        assert u.is_admin is False
        assert u.loyalty_points == 0
        assert u.loyalty_level == "bronze"

    def test_password_hash(self, db):
        u = User(email="x@y.com", first_name="X", last_name="Y")
        u.set_password("mypassword")
        assert u.password_hash != "mypassword"
        assert u.check_password("mypassword") is True
        assert u.check_password("wrongpass") is False

    def test_loyalty_level_display(self, user):
        assert "Bronce" in user.loyalty_level_display

    def test_add_points(self, db, user):
        leveled_up = user.add_points(500, "Test points")
        db.session.commit()

        assert user.loyalty_points == 500
        assert user.loyalty_level == "bronze"
        assert leveled_up is False

    def test_add_points_level_up(self, db, user):
        leveled_up = user.add_points(1000, "Big purchase")
        db.session.commit()

        assert user.loyalty_points == 1000
        assert user.loyalty_level == "silver"
        assert leveled_up is True
        assert user.loyalty_discount == 5

    def test_points_to_next_level(self, db, user):
        user.add_points(500, "Partial")
        db.session.commit()
        assert user.points_to_next_level == 500  # 1000 - 500


class TestCategoryModel:
    def test_create_category(self, db):
        cat = Category(name="Bolsos", slug="bolsos", active=True)
        db.session.add(cat)
        db.session.commit()
        assert cat.id is not None
        assert cat.name == "Bolsos"

    def test_category_repr(self, category):
        assert "Billeteras" in repr(category)


class TestProductModel:
    def test_create_product(self, product):
        assert product.id is not None
        assert product.name == "Billetera Clásica"
        assert product.price == Decimal("45.00")
        assert product.in_stock is True

    def test_product_slug_auto(self, db, category):
        p = Product(
            name="Cinturón Rústico",
            description="Cuero grueso",
            price=Decimal("35"),
            stock=5,
            sku="CIN-001",
            category_id=category.id
        )
        db.session.add(p)
        db.session.commit()
        assert p.slug == "cinturon-rustico"

    def test_discount_percent(self, db, category):
        p = Product(
            name="Oferta",
            slug="oferta",
            description="Test",
            price=Decimal("70"),
            compare_at_price=Decimal("100"),
            stock=5,
            sku="OFF-001",
            category_id=category.id
        )
        db.session.add(p)
        db.session.commit()
        assert p.discount_percent == 30

    def test_no_discount(self, product):
        assert product.discount_percent == 0

    def test_out_of_stock(self, product_out_of_stock):
        assert product_out_of_stock.in_stock is False


class TestCouponModel:
    def test_coupon_valid(self, coupon):
        assert coupon.is_valid is True
        assert coupon.discount_display == "10%"

    def test_coupon_apply_percentage(self, coupon):
        discount = coupon.apply_discount(Decimal("100"))
        assert discount == Decimal("10")

    def test_coupon_apply_fixed(self, coupon_fixed):
        discount = coupon_fixed.apply_discount(Decimal("50"))
        assert discount == Decimal("5.00")

    def test_coupon_min_purchase(self, coupon_fixed):
        discount = coupon_fixed.apply_discount(Decimal("10"))
        assert discount == Decimal("0")

    def test_coupon_inactive(self, db, coupon):
        coupon.active = False
        db.session.commit()
        assert coupon.is_valid is False


class TestWishlistModel:
    def test_add_wishlist(self, db, user, product):
        w = Wishlist(user_id=user.id, product_id=product.id)
        db.session.add(w)
        db.session.commit()
        assert w.id is not None
        assert user.is_in_wishlist(product.id) is True

    def test_wishlist_count(self, db, user, product):
        w = Wishlist(user_id=user.id, product_id=product.id)
        db.session.add(w)
        db.session.commit()
        assert user.wishlist_count == 1


class TestReviewModel:
    def test_create_review(self, db, user, product):
        r = Review(
            user_id=user.id,
            product_id=product.id,
            rating=5,
            comment="Excelente",
            approved=False
        )
        db.session.add(r)
        db.session.commit()
        assert r.id is not None
        assert product.has_user_reviewed(user.id) is True

    def test_average_rating(self, db, user, product):
        r = Review(
            user_id=user.id,
            product_id=product.id,
            rating=4,
            approved=True
        )
        db.session.add(r)
        db.session.commit()
        assert product.average_rating == 4.0
        assert product.review_count == 1