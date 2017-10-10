from django.conf.urls import url

from .views import run_queries

app_name = 'middleware'

urlpatterns = [
    url(r'^$', run_queries, name='run_queries')
]