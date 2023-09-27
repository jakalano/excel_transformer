from django.urls import path
from . import views

urlpatterns = [
    path('', views.main_page, name='main_page'),
    
    path('summary/', views.summary, name='summary'),
    path('edit_data/', views.edit_data, name='edit_data'),
    path('edit_columns/', views.edit_columns, name='edit_columns'),
    path('download/', views.download, name='download'),
    path('failed/', views.failed, name='failed'),
]

