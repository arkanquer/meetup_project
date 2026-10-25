from django.urls import path
from . import views

urlpatterns = [
    # Головна сторінка та профіль
    path('', views.home_page, name='home'),
    path('profile/', views.profile_view, name='profile'),

    # Авторизація та реєстрація
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Оголошення та зустрічі
    path('proposal/create/', views.create_proposal, name='create_proposal'),
    path('proposal/<int:pk>/', views.proposal_details, name='proposal_details'),
    path('proposal/<int:pk>/close/', views.close_proposal, name='close_proposal'),

    # Заявки на участь та модерація
    path('proposal/<int:pk>/apply/', views.send_application, name='send_application'),
    path('application/<int:pk>/accept/', views.accept_application, name='accept_application'),
    path('application/<int:pk>/reject/', views.reject_application, name='reject_application'),
    path('application/<int:pk>/remove/', views.remove_guest, name='remove_guest'),

    # Чат зустрічі
    path('proposal/<int:pk>/chat/', views.proposal_chat, name='proposal_chat'),

    # Рейтинги
    path('rate/<int:user_id>/', views.rate_user, name='rate_user'),
    path('top/', views.top_users, name='top_users'),

    # 🤝 СИСТЕМА ДРУЗІВ (Нові правильні маршрути)
    path('friend/send/<int:user_id>/', views.send_friend_request, name='send_friend_request'),
    path('friend/accept/<int:request_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('friend/reject/<int:request_id>/', views.reject_or_remove_friend, name='reject_or_remove_friend'),
]