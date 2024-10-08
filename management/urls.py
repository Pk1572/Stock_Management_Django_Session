"""
URL configuration for management project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from product.views import home, register, login, Logout, ProductView, ProductStockView, HistoryView, profile, changepass, EditProfileView, Unit, ActivateProductView, DeactivateProductView, PDFCreateView, UpdatePDF,PDFView, SendPasswordResetEmailView, ResetPasswordView, BillingView

urlpatterns = [
    path('', home.as_view(), name='home'),
    path('admin/', admin.site.urls),

    path('register/', register.as_view(), name='register'),
    path('login/', login.as_view(), name='login'),
    path('logout/', Logout.as_view(), name='logout'),
    path('profile/', profile.as_view(), name='profile'),
    path('changepass/', changepass.as_view(), name='changepass'),
    path('edit_profile/', EditProfileView.as_view(), name='edit_profile'),

    path('send-password-reset/', SendPasswordResetEmailView.as_view(), name='send_password_reset'),
    path('reset-password-confirm/<uidb64>/<token>/', ResetPasswordView.as_view(), name='reset-password-confirm'),

    path('unit/', Unit.as_view(), name='unit'),

    path('products/', ProductView.as_view(), name='product'),
    path('product/<int:product_id>/', ProductView.as_view(), name='product_edit'),
    path('product/delete/<int:product_id>/', ProductView.as_view(), name='product_delete'),
    path('products/activate/<int:product_id>/', ActivateProductView.as_view(), name='activate_product'),
    path('products/deactivate/<int:product_id>/', DeactivateProductView.as_view(), name='deactivate_product'),
        
    path('product_stock/', ProductStockView.as_view(), name='product_stock'),

    path('history/', HistoryView.as_view(), name='history'),
    path('history/<int:history_id>/', HistoryView.as_view(), name='edit_history'),

    path('create_pdf/', PDFCreateView.as_view(), name='create_pdf'),
    path('pdfview/', PDFView.as_view(), name='pdfview'),
    path('update_pdf_title/', UpdatePDF.as_view(), name='update_pdf_title'),

    path('billing/', BillingView.as_view(), name='billing'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
