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
    with open('erro_template.txt', 'w', encoding='utf-8') as f:
        f.write(str(e))
    print("Erro salvo em erro_template.txt")
