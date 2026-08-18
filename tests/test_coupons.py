# tests/test_coupons.py
"""
Tests de cupones de descuento (rutas admin + validación).
"""
from decimal import Decimal
from app.models import Coupon
from app.extensions import db

class TestCouponCreation:
    def test_create_coupon_admin(self, admin_client, db):
        resp = admin_client.post('/admin/cupones/nuevo', data={
            'code': 'NUEVO20',
            'discount_type': 'percentage',
            'discount_value': '20',
            'min_purchase': '0',
            'max_uses': '0',
            'active': 'y'
        }, follow_redirects=True)

        assert resp.status_code == 200
        c = Coupon.query.filter_by(code='NUEVO20').first()
        assert c is not None
        assert c.discount_type == 'percentage'

    def test_duplicate_coupon_rejected(self, admin_client, db, coupon):
        resp = admin_client.post('/admin/cupones/nuevo', data={
            'code': 'TEST10',
            'discount_type': 'percentage',
            'discount_value': '15',
            'min_purchase': '0',
            'max_uses': '0',
            'active': 'y'
        }, follow_redirects=True)

        assert resp.status_code == 200
        assert Coupon.query.filter_by(code='TEST10').count() == 1


class TestCouponEdit:
    def test_edit_coupon(self, admin_client, db, coupon):
        resp = admin_client.post(
            f'/admin/cupones/{coupon.id}/editar',
            data={
                'code': 'TEST20',
                'discount_type': 'percentage',
                'discount_value': '20',
                'min_purchase': '0',
                'max_uses': '0',
                'active': 'y'
            },
            follow_redirects=True
        )
        assert resp.status_code == 200

        updated = db.session.get(Coupon, coupon.id)
        assert updated.code == 'TEST20'
        assert updated.discount_value == Decimal("20")


class TestCouponDelete:
    def test_delete_coupon(self, admin_client, db, coupon):
        resp = admin_client.post(
            f'/admin/cupones/{coupon.id}/eliminar',
            follow_redirects=True
        )
        assert resp.status_code == 200
        assert db.session.get(Coupon, coupon.id) is None