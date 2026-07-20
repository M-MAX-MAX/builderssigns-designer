from django.urls import path

from . import views

app_name = 'designer'

urlpatterns = [
    path('', views.template_gallery, name='gallery'),
    path('select/<slug:slug>/', views.select_template, name='select_template'),
    path('details/', views.details, name='details'),
    path('logo/', views.logo, name='logo'),
    path('done/', views.done, name='done'),
]
