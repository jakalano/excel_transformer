from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.main_page, name='main_page'),
    
    path('summary/', views.summary, name='summary'),
    path('edit_data/', views.edit_data, name='edit_data'),
    path('edit_columns/', views.edit_columns, name='edit_columns'),
    path('undo/', views.undo_last_action, name='undo_last_action'),
    path('download/', views.download, name='download'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
]

