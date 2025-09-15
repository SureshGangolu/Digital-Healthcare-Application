from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/doctor/', views.reg_doc, name='reg_doc'),
    path('register/patient/', views.reg_pat, name='reg_pat'),
    path('wait/', views.wait, name='wait'),
    path('login/', views.logn, name='logn'),
    path('dashboard/', views.dash, name='dash'),
    path('docdash/', views.docdash, name='docdash'),
    path('adminlogin/', views.adlog, name='adlog'),
    path('adminpanel/', views.adpanel, name='adpanel'),
    path('approve/<int:pid>/', views.toggleuser, name='approve'),
    path('patdash/', views.patdash, name='patdash'),
    path('logout/', views.log_out, name='logout'),
    path('chat/<int:bid>/', views.chat_view, name='chat'),
    path('upload-file/', views.upload_chat_file, name='upload_chat_file'),
    path('cancel-booking/<int:bid>/', views.cancel_booking, name='cancel-booking'),
    path('adminstats/', views.adminstats, name='adminstats'),
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='reset/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='reset/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='reset/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='reset/password_reset_complete.html'), name='password_reset_complete'),
    path('admin-appointments/', views.appointment_logs, name='admin_appointments'),
    path('reschedule/<int:bid>/', views.reschedule_booking, name='reschedule_booking'),
    path('delete/<int:pid>/', views.delete_user, name='delete_user'),
    path('chat/file/<int:mid>/', views.download_chat_file, name='download_chat_file'),
    path('cancel-patient/<int:bid>/', views.cancel_booking_patient, name='cancel-booking-patient'),
    path("panel/license/<int:pid>/preview/", views.panel_preview_license, name="panel_preview_license"),
    path("panel/license/<int:pid>/download/", views.panel_download_license, name="panel_download_license"),
    path("booking/<int:bid>/feedback/", views.add_feedback, name="add_feedback"),
    path('doctor-feedback/<int:doctor_id>/', views.doctor_feedback, name='doctor_feedback'),
    path('edit-user/<int:pid>/', views.edit_user, name='edit_user'),


   

]
