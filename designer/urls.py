from django.urls import path

from . import views

app_name = 'designer'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('select/<slug:slug>/', views.select_template, name='select_template'),
    path('details/', views.details, name='details'),
    path('upload-later/', views.upload_later, name='upload_later'),
    path('upload/<uuid:token>/', views.upload_page, name='upload_page'),
    path('upload/<uuid:token>/file/', views.upload_file, name='upload_file'),
    path('upload/<uuid:token>/submit/', views.upload_submit, name='upload_submit'),
    path('upload/<uuid:token>/thanks/', views.upload_thanks, name='upload_thanks'),
    # Catch-all product slug — must stay last so it doesn't shadow the fixed
    # paths above (e.g. a product could never be reached if this came first
    # and a product happened to be named "details").
    path('<slug:product_slug>/', views.template_gallery, name='gallery'),
]
