"""URL configuration for savings_tracker project."""
from django.contrib import admin
from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from accounts.views import home, EditAccountsView, AddTransactionView, RegisterView, myaccounts, reset_account, delete_account, set_currency, profile, export_csv, rename_account
from accounts import views
from django.conf.urls.i18n import set_language

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('edit-accounts/', EditAccountsView.as_view(), name='edit_accounts'),
    path('add-transaction/', AddTransactionView.as_view(), name='add_transaction'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),
    path('myaccounts/', myaccounts, name='myaccounts'),
    path('reset_account/<int:account_id>/', reset_account, name='reset_account'),
    path('delete_account/<int:account_id>/', delete_account, name='delete_account'),
    path('set_currency/', set_currency, name='set_currency'),
    path('set-language/', set_language, name='set_language'),
    path('update_account_currency/<int:account_id>/', views.update_account_currency, name='update_account_currency'),
    path('account/<int:account_id>/', views.account_detail, name='account_detail'),
    path('delete_transaction/<int:tx_id>/', views.delete_transaction, name='delete_transaction'),
    path('profile/', views.profile, name='profile'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    path('export-csv/', views.export_csv, name='export_csv'),
    path('import-csv/', views.import_csv, name='import_csv'),
    path('rename_account/<int:account_id>/', views.rename_account, name='rename_account'),
    path('reorder_accounts/', views.reorder_accounts, name='reorder_accounts'),
    path('account/<int:account_id>/', views.account_detail, name='account_detail'),
    path('delete_transaction/<int:tx_id>/', views.delete_transaction, name='delete_transaction'),
    path('profile/', views.profile, name='profile'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    path('export-csv/', views.export_csv, name='export_csv'),
    path('import-csv/', views.import_csv, name='import_csv'),
    path('rename_account/<int:account_id>/', views.rename_account, name='rename_account'),
    path('reorder_accounts/', views.reorder_accounts, name='reorder_accounts'),
]
