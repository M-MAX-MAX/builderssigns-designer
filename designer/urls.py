from django.urls import path

from . import views

app_name = 'designer'

urlpatterns = [
    path('', views.template_gallery, name='gallery'),
    path('select/<slug:slug>/', views.select_template, name='select_template'),
    path('details/', views.details, name='details'),
    path('upload-later/', views.upload_later, name='upload_later'),
    path('upload/<uuid:token>/', views.upload_page, name='upload_page'),
    path('upload/<uuid:token>/file/', views.upload_file, name='upload_file'),
    path('upload/<uuid:token>/submit/', views.upload_submit, name='upload_submit'),
    path('upload/<uuid:token>/thanks/', views.upload_thanks, name='upload_thanks'),
]
