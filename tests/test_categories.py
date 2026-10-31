"""
CodeSphere - Question Category Management Automated Tests
---------------------------------------------------------
Validates category creation, slug uniqueness, editing, question reference counting,
and safe deletion prevention.
"""

from app.models.question import Category
from app.extensions import db


def test_admin_create_category(admin_client, app):
    """Verifies administrator can create a new category."""
    resp = admin_client.post('/admin/categories/create', data={
        'name': 'Bit Manipulation',
        'slug': 'bit-manipulation',
        'icon': 'bi-cpu',
        'description': 'Bitwise operations, XOR tricks, and binary representation.'
    }, follow_redirects=True)

    assert resp.status_code == 200
    with app.app_context():
        cat = Category.query.filter_by(slug='bit-manipulation').first()
        assert cat is not None
        assert cat.name == 'Bit Manipulation'


def test_admin_edit_category(admin_client, app):
    """Verifies category details can be updated."""
    with app.app_context():
        cat = Category.query.filter_by(slug='arrays').first()
        cat_id = cat.id

    resp = admin_client.post(f'/admin/categories/{cat_id}/edit', data={
        'name': 'Arrays & Two Pointers',
        'slug': 'arrays',
        'icon': 'bi-grid-3x3',
        'description': 'Updated description for arrays.'
    }, follow_redirects=True)

    assert resp.status_code == 200
    with app.app_context():
        cat = Category.query.get(cat_id)
        assert cat.name == 'Arrays & Two Pointers'


def test_category_with_questions_cannot_be_deleted(admin_client, app):
    """Ensures categories containing questions cannot be deleted (safe deletion)."""
    with app.app_context():
        cat = Category.query.filter_by(slug='arrays').first()
        assert cat.question_count > 0
        cat_id = cat.id

    resp = admin_client.post(f'/admin/categories/{cat_id}/delete', follow_redirects=True)
    assert b"Cannot delete category" in resp.data

    with app.app_context():
        cat = Category.query.get(cat_id)
        assert cat is not None  # Category must still exist


def test_empty_category_can_be_safely_deleted(admin_client, app):
    """Ensures empty categories without questions can be deleted safely."""
    with app.app_context():
        empty_cat = Category(name='Temporary Empty', slug='temp-empty', icon='bi-trash')
        db.session.add(empty_cat)
        db.session.commit()
        empty_id = empty_cat.id

    resp = admin_client.post(f'/admin/categories/{empty_id}/delete', follow_redirects=True)
    assert b"deleted successfully" in resp.data

    with app.app_context():
        assert Category.query.get(empty_id) is None
