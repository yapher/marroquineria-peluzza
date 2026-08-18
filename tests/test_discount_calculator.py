# tests/test_discount_calculator.py
"""
Tests de la calculadora de descuentos y costo de envío.

Cubre:
- Costo de envío (GRATIS desde $100 - FREE_SHIPPING_THRESHOLD)
- Cupones (porcentaje y monto fijo)
- Descuento por nivel de fidelización
- calculate_all_discounts (integración)
- validate_coupon
"""
from decimal import Decimal

from app.services.discount_calculator import (
    calculate_coupon_discount,
    calculate_level_discount,
    calculate_shipping_cost,
    calculate_all_discounts,
    validate_coupon,
)
from app.config.constants import DEFAULT_SHIPPING_COST, FREE_SHIPPING_THRESHOLD


# ============================================
# COSTO DE ENVÍO
# ============================================
class TestCalculateShippingCost:
    def test_below_threshold_charges_default(self):
        assert calculate_shipping_cost(Decimal('50')) == DEFAULT_SHIPPING_COST

    def test_just_below_threshold_charges(self):
        assert calculate_shipping_cost(Decimal('99.99')) == DEFAULT_SHIPPING_COST

    def test_at_threshold_is_free(self):
        assert calculate_shipping_cost(FREE_SHIPPING_THRESHOLD) == Decimal('0')

    def test_above_threshold_is_free(self):
        assert calculate_shipping_cost(Decimal('500')) == Decimal('0')

    def test_zero_subtotal_charges_default(self):
        assert calculate_shipping_cost(Decimal('0')) == DEFAULT_SHIPPING_COST


# ============================================
# CUPONES
# ============================================
class TestCalculateCouponDiscount:
    def test_no_coupon_returns_zero(self):
        assert calculate_coupon_discount(Decimal('100'), None) == Decimal('0')
        assert calculate_coupon_discount(Decimal('100'), '') == Decimal('0')

    def test_nonexistent_coupon_returns_zero(self, db):
        assert calculate_coupon_discount(Decimal('100'), 'NOEXISTE') == Decimal('0')

    def test_inactive_coupon_returns_zero(self, db, coupon):
        coupon.active = False
        db.session.commit()
        assert calculate_coupon_discount(Decimal('100'), 'TEST10') == Decimal('0')

    def test_coupon_below_min_purchase_returns_zero(self, db, coupon_fixed):
        # FIXED5 exige compra mínima de $20
        assert calculate_coupon_discount(Decimal('10'), 'FIXED5') == Decimal('0')

    def test_valid_percentage_coupon(self, db, coupon):
        # TEST10 = 10% de descuento
        assert calculate_coupon_discount(Decimal('200'), 'TEST10') == Decimal('20')

    def test_valid_fixed_coupon(self, db, coupon_fixed):
        # FIXED5 = $5 de descuento (compra >= $20)
        assert calculate_coupon_discount(Decimal('50'), 'FIXED5') == Decimal('5.00')


# ============================================
# NIVEL DE FIDELIZACIÓN
# ============================================
class TestCalculateLevelDiscount:
    def test_no_user_returns_zero(self):
        assert calculate_level_discount(Decimal('100'), None) == Decimal('0')

    def test_bronze_user_returns_zero(self, db, user):
        assert calculate_level_discount(Decimal('100'), user) == Decimal('0')

    def test_silver_user_gets_5_percent(self, db, user):
        user.loyalty_level = 'silver'
        db.session.commit()
        assert calculate_level_discount(Decimal('200'), user) == Decimal('10')

    def test_gold_user_gets_10_percent(self, db, user):
        user.loyalty_level = 'gold'
        db.session.commit()
        assert calculate_level_discount(Decimal('100'), user) == Decimal('10')

    def test_platinum_user_gets_15_percent(self, db, user):
        user.loyalty_level = 'platinum'
        db.session.commit()
        assert calculate_level_discount(Decimal('100'), user) == Decimal('15')


# ============================================
# CÁLCULO INTEGRADO
# ============================================
class TestCalculateAllDiscounts:
    def test_no_discounts_below_threshold(self, db):
        result = calculate_all_discounts(Decimal('50'), None, None)
        assert result['coupon_discount'] == Decimal('0')
        assert result['level_discount'] == Decimal('0')
        assert result['shipping_cost'] == DEFAULT_SHIPPING_COST
        assert result['final_total'] == Decimal('50') + DEFAULT_SHIPPING_COST

    def test_free_shipping_above_threshold(self, db):
        """✅ Envío GRATIS con subtotal >= $100."""
        result = calculate_all_discounts(Decimal('120'), None, None)
        assert result['shipping_cost'] == Decimal('0')
        assert result['final_total'] == Decimal('120')

    def test_full_calculation(self, db, coupon, user):
        """Cupón 10% + nivel plata 5% + envío gratis."""
        user.loyalty_level = 'silver'
        db.session.commit()
        result = calculate_all_discounts(
            subtotal=Decimal('200'),
            coupon_code='TEST10',
            user=user,
        )
        assert result['coupon_discount'] == Decimal('20')   # 10% de 200
        assert result['level_discount'] == Decimal('9')     # 5% de (200-20)=180
        assert result['shipping_cost'] == Decimal('0')      # gratis (>= $100)
        assert result['total_discount'] == Decimal('29')
        assert result['final_total'] == Decimal('171')      # 200 - 29 + 0


# ============================================
# VALIDACIÓN DE CUPONES
# ============================================
class TestValidateCoupon:
    def test_empty_code(self, db):
        valid, msg = validate_coupon('', Decimal('100'))
        assert valid is False

    def test_nonexistent_code(self, db):
        valid, msg = validate_coupon('NOEXISTE', Decimal('100'))
        assert valid is False
        assert 'encontrado' in msg

    def test_valid_code(self, db, coupon):
        valid, msg = validate_coupon('TEST10', Decimal('100'))
        assert valid is True
        assert msg == ''

    def test_code_below_min_purchase(self, db, coupon_fixed):
        valid, msg = validate_coupon('FIXED5', Decimal('10'))
        assert valid is False
        assert 'mínima' in msg