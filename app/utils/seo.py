# app/utils/seo.py
"""
Generación de sitemap.xml y robots.txt.
Extraído de main/routes.py para mantener las rutas declarativas.
"""
from flask import request, url_for, Response

from ..models import Category, Product
from .time import utc_now

# Páginas estáticas del sitio con su prioridad SEO
STATIC_PAGES = [
    {'url': '/', 'priority': '1.0', 'changefreq': 'daily'},
    {'url': '/tienda', 'priority': '0.9', 'changefreq': 'daily'},
    {'url': '/nosotros', 'priority': '0.5', 'changefreq': 'monthly'},
    {'url': '/envios', 'priority': '0.4', 'changefreq': 'monthly'},
    {'url': '/contacto', 'priority': '0.5', 'changefreq': 'monthly'},
]


def _build_pages() -> list[dict]:
    """Construye la lista de páginas del sitemap (estáticas + dinámicas)."""
    base_url = request.url_root.rstrip('/')
    today = utc_now().strftime('%Y-%m-%d')
    pages = []

    # Páginas estáticas
    for page in STATIC_PAGES:
        pages.append({
            'loc': f"{base_url}{page['url']}",
            'lastmod': today,
            'changefreq': page['changefreq'],
            'priority': page['priority'],
        })

    # Categorías activas
    for cat in Category.query.filter_by(active=True).all():
        pages.append({
            'loc': f"{base_url}/tienda?categoria={cat.slug}",
            'lastmod': today,
            'changefreq': 'weekly',
            'priority': '0.7',
        })

    # Productos activos
    for product in Product.query.filter_by(active=True).all():
        lastmod = product.created_at.strftime('%Y-%m-%d') if product.created_at else today
        pages.append({
            'loc': f"{base_url}/tienda/producto/{product.slug}",
            'lastmod': lastmod,
            'changefreq': 'weekly',
            'priority': '0.8',
        })

    return pages


def _pages_to_xml(pages: list[dict]) -> str:
    """Convierte la lista de páginas en XML de sitemap."""
    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for page in pages:
        xml.append('  <url>')
        xml.append(f'    <loc>{page["loc"]}</loc>')
        xml.append(f'    <lastmod>{page["lastmod"]}</lastmod>')
        xml.append(f'    <changefreq>{page["changefreq"]}</changefreq>')
        xml.append(f'    <priority>{page["priority"]}</priority>')
        xml.append('  </url>')
    xml.append('</urlset>')
    return '\n'.join(xml)


def sitemap_response() -> Response:
    """Respuesta HTTP del sitemap.xml dinámico."""
    return Response(_pages_to_xml(_build_pages()), mimetype='application/xml')


def robots_response() -> Response:
    """Respuesta HTTP del robots.txt."""
    sitemap_url = url_for('main.sitemap', _external=True)
    content = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /admin\n"
        "Disallow: /auth\n"
        "Disallow: /cuenta\n"
        "Disallow: /checkout\n"
        f"Sitemap: {sitemap_url}\n"
    )
    return Response(content, mimetype='text/plain')