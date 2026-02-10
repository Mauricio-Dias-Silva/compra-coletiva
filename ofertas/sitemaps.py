# ofertas/sitemaps.py — SEO Sitemap for Google

from django.contrib.sitemaps import Sitemap
from .models import Oferta, Categoria


class OfertaSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.9

    def items(self):
        return Oferta.objects.filter(publicada=True, status='ativa')

    def lastmod(self, obj):
        return obj.data_atualizacao

    def location(self, obj):
        return obj.get_absolute_url()


class CategoriaSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return Categoria.objects.filter(ativa=True)

    def location(self, obj):
        return f'/ofertas/categoria/{obj.slug}/'


class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'monthly'

    def items(self):
        return ['ofertas:lista_ofertas', 'ofertas:compre_junto']

    def location(self, item):
        from django.urls import reverse
        return reverse(item)