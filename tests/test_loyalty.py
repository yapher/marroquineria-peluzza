# tests/test_loyalty.py
"""
Tests del sistema de fidelización: constantes, niveles, puntos y transacciones.
"""
from app.models import LoyaltyTransaction
from app.services.loyalty_service import calculate_points_from_order
from app.config.constants import LOYALTY_LEVELS, LoyaltyLevel, get_next_loyalty_level


class TestLoyaltyConstants:
    def test_levels_defined(self):
        assert LoyaltyLevel.BRONZE in LOYALTY_LEVELS
        assert LoyaltyLevel.SILVER in LOYALTY_LEVELS
        assert LoyaltyLevel.GOLD in LOYALTY_LEVELS
        assert LoyaltyLevel.PLATINUM in LOYALTY_LEVELS

    def test_thresholds(self):
        assert LOYALTY_LEVELS[LoyaltyLevel.BRONZE]["threshold"] == 0
        assert LOYALTY_LEVELS[LoyaltyLevel.SILVER]["threshold"] == 1000
        assert LOYALTY_LEVELS[LoyaltyLevel.GOLD]["threshold"] == 5000
        assert LOYALTY_LEVELS[LoyaltyLevel.PLATINUM]["threshold"] == 10000

    def test_discounts(self):
        assert LOYALTY_LEVELS[LoyaltyLevel.BRONZE]["discount"] == 0
        assert LOYALTY_LEVELS[LoyaltyLevel.SILVER]["discount"] == 5
        assert LOYALTY_LEVELS[LoyaltyLevel.GOLD]["discount"] == 10
        assert LOYALTY_LEVELS[LoyaltyLevel.PLATINUM]["discount"] == 15


class TestNextLevel:
    def test_bronze_next_is_silver(self):
        result = get_next_loyalty_level(LoyaltyLevel.BRONZE)
        assert result["points"] == 1000

    def test_platinum_is_max(self):
        result = get_next_loyalty_level(LoyaltyLevel.PLATINUM)
        assert result["points"] is None
        assert result["name"] == "Máximo"


class TestUserLoyalty:
    def test_initial_state(self, db, regular_user):
        assert regular_user.loyalty_points == 0
        assert regular_user.loyalty_level == LoyaltyLevel.BRONZE
        assert regular_user.loyalty_discount == 0

    def test_add_points(self, db, regular_user):
        leveled_up = regular_user.add_points(500, "Test points")
        db.session.commit()
        assert regular_user.loyalty_points == 500
        assert regular_user.loyalty_level == LoyaltyLevel.BRONZE
        assert leveled_up is False

    def test_add_points_level_up_to_silver(self, db, regular_user):
        leveled_up = regular_user.add_points(1000, "Big purchase")
        db.session.commit()
        assert regular_user.loyalty_level == LoyaltyLevel.SILVER
        assert regular_user.loyalty_discount == 5
        assert leveled_up is True

    def test_add_points_level_up_to_gold(self, db, regular_user):
        regular_user.add_points(5000, "Huge purchase")
        db.session.commit()
        assert regular_user.loyalty_level == LoyaltyLevel.GOLD
        assert regular_user.loyalty_discount == 10

    def test_add_points_level_up_to_platinum(self, db, regular_user):
        regular_user.add_points(10000, "Legendary purchase")
        db.session.commit()
        assert regular_user.loyalty_level == LoyaltyLevel.PLATINUM
        assert regular_user.loyalty_discount == 15

    def test_transaction_recorded(self, db, regular_user):
        regular_user.add_points(100, "Test transaction")
        db.session.commit()
        tx = LoyaltyTransaction.query.filter_by(user_id=regular_user.id).first()
        assert tx is not None
        assert tx.points == 100
        assert tx.balance_after == 100
        assert tx.reason == "Test transaction"

    def test_points_to_next_level(self, db, regular_user):
        regular_user.add_points(500, "Partial")
        db.session.commit()
        assert regular_user.points_to_next_level == 500

    def test_level_progress_halfway(self, db, regular_user):
        regular_user.add_points(500, "Halfway")
        db.session.commit()
        assert regular_user.level_progress == 50.0


class TestLoyaltyService:
    def test_calculate_points_from_order(self):
        class MockOrder:
            total = 150.0

        # 1 punto por cada $10 → $150 → 15 puntos
        assert calculate_points_from_order(MockOrder()) == 15

    def test_calculate_points_small_order(self):
        class MockOrder:
            total = 5.0

        # No redondea hacia arriba
        assert calculate_points_from_order(MockOrder()) == 0