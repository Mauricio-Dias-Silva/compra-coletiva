import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projeto_compra_coletiva.settings')
django.setup()

from django.test import Client

try:
    c = Client()
    r = c.get('/')
    print(r.status_code)
except Exception as e:
    print("ERRO COMPLETO:")
    print(type(e))
    print(str(e))
