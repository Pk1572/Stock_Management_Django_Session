from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib import messages
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import CustomUser, Product, ProductStock, History, Units
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.db.models import Max
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models.functions import TruncDate
from datetime import timedelta
from django.template.loader import get_template
from xhtml2pdf import pisa
import json
from django.core.files.storage import default_storage
from django.utils.timezone import now
import os
from django.conf import settings
import qrcode
import base64
from io import BytesIO
from decimal import Decimal
from num2words import num2words

class home(LoginRequiredMixin, View):
    def get(self, request):
        low_stock_threshold = request.session.get('low_stock_threshold', 100)
        product_data = Product.objects.all()
        stock_data_all = ProductStock.objects.filter(product_quantity__lt=low_stock_threshold)

        today = timezone.now().date()
        start_date = today - timedelta(days=7)

        buy_transactions_today = History.objects.filter(transaction_type='Buy', updated_date__date=today)
        sell_transactions_today = History.objects.filter(transaction_type='Sell', updated_date__date=today)

        sales_data = History.objects.filter(transaction_type='Sell').annotate(
            date=TruncDate('updated_date')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
    
        date_range = [start_date + timedelta(days=i) for i in range(8)]
        labels = [date.strftime('%Y-%m-%d') for date in date_range]
        data = [0] * len(date_range)

        for sale in sales_data:
            sale_date = sale['date']
            if start_date <= sale_date <= today:
                index = (sale_date - start_date).days
                data[index] = sale['count']

        buy_data = History.objects.filter(transaction_type='Buy').annotate(
            date=TruncDate('updated_date')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')

        buy_chart_data = [0] * len(date_range)
        buy_chart_labels = labels  

        for buy in buy_data:
            buy_date = buy['date']
            if start_date <= buy_date <= today:
                index = (buy_date - start_date).days
                buy_chart_data[index] = buy['count']

        # Pie chart data
        product_stock_data = []
        for product in product_data:
            stock = ProductStock.objects.filter(product_id=product).aggregate(
                total_stock=Sum('product_quantity')
            )['total_stock'] or 0
            product_stock_data.append((product.product_name, stock))

        product_stock_data.sort(key=lambda x: x[1], reverse=True)
        top_products = product_stock_data[:7]
        other_stock = sum(stock for name, stock in product_stock_data[7:])
        top_products.append(("Other", other_stock))

        pie_chart_labels = [name for name, stock in top_products]
        pie_chart_data = [stock for name, stock in top_products]

        # Low stock bar chart data
        low_stock_product_data = []
        for product in product_data:
            stock = ProductStock.objects.filter(product_id=product).aggregate(
                total_stock=Sum('product_quantity')
            )['total_stock'] or 0
            if stock < low_stock_threshold:
                low_stock_product_data.append((product.product_name, stock))

        low_stock_product_data.sort(key=lambda x: x[1])
        low_stock_labels = [name for name, stock in low_stock_product_data]
        low_stock_data = [stock for name, stock in low_stock_product_data]  

        # this code for unit stock chart 
        #unit_data = Product.objects.values('unit__unit_name').annotate(product_count=Count('id')).order_by('unit__unit_name')
        #pie_chart_labels = []
        #pie_chart_data = []
        #for unit in unit_data:
        #    pie_chart_labels.append(unit['unit__unit_name'])
        #    pie_chart_data.append(unit['product_count'])

        # this code for product type chart
        product_type_data = Product.objects.values('product_type').annotate(
            product_count=Count('id')
        ).order_by('product_type')

        polar_chart_labels = [entry['product_type'] for entry in product_type_data]
        polar_chart_data = [entry['product_count'] for entry in product_type_data]

        return render(request, 'home.html', {
            'stock_data_all': stock_data_all,
            'product_data': product_data,
            'buy_transactions_today': buy_transactions_today,
            'sell_transactions_today': sell_transactions_today,
            'buy_chart_labels': buy_chart_labels,
            'buy_chart_data': buy_chart_data,
            'chart_labels': labels,
            'chart_data': data,
            'low_stock_threshold': low_stock_threshold,
            'pie_chart_labels': pie_chart_labels,
            'pie_chart_data': pie_chart_data,
            'low_stock_labels': low_stock_labels,
            'low_stock_data': low_stock_data,
            'polar_chart_labels': polar_chart_labels,
            'polar_chart_data': polar_chart_data,
        })

    def post(self, request):
        if 'low_stock_threshold' in request.POST:
            low_stock_threshold = float(request.POST.get('low_stock_threshold', 50))
            request.session['low_stock_threshold'] = low_stock_threshold 
        return redirect('home')

class register(View):
    def get(self, request):
        if():
            return redirect('product')
        else:
            return render(request,'register.html')

    def post(self, request):
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        role = request.POST.get('role')
        password = request.POST.get('password')

        email_check = CustomUser.objects.filter(email=email).exists()
        
        if email_check:
            messages.error(request, "Your Email Already Exists")
            return redirect('register')
        else:
            user = CustomUser.objects.create_user(username=username, email=email, password=password, role=role, phone_number=phone_number)
            user.save()
            messages.success(request, "Your Account Successfully Created")
            return redirect('login')

class login(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        return render(request, 'login.html')

    def post(self, request):
        email_or_phone = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=email_or_phone, password=password)
        
        if user is not None:
            auth_login(request, user)
            return redirect(reverse('home'))
        else:
            messages.info(request, "Your Data Is Invalid")
            return redirect(reverse('login'))

User = get_user_model()

class SendPasswordResetEmailView(View):
    def post(self, request):
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            link = f"{request.build_absolute_uri('/reset-password-confirm/')}{uid}/{token}/"
            subject = "Password Reset Requested"
            message = render_to_string('password_reset_email.html', {
                'user': user,
                'link': link,
            })
            print(link)
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

            messages.success(request, "Password reset email has been sent.")
        except User.DoesNotExist:
            messages.error(request, "No user found with that email address.")

        return redirect('login')

class ResetPasswordView(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = get_object_or_404(User, pk=uid)
            if not default_token_generator.check_token(user, token):
                messages.error(request, "Password reset link is invalid or has expired.")
                return redirect('login')
            print(uid,token)
            return render(request, 'reset_password.html', {'uid': uid, 'token': token})
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            messages.error(request, "Invalid password reset link.")
            return redirect('login')

    def post(self, request, uidb64, token):
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect(request.path)  # Redirect to the same page

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = get_object_or_404(User, pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, "Your password has been reset successfully.")
            return redirect('login')
        except Exception as e:
            messages.error(request, "An error occurred while resetting your password.")
            return redirect('login')

class Logout(View):
    def get(self, request):
        auth_logout(request)
        messages.success(request, "Logout Successfully")
        return redirect('login')

class profile(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'profile.html')

class changepass(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'profile.html')

    def post(self, request):
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if old_password and new_password and confirm_password:
            user = authenticate(username=request.user.email, password=old_password)
            if user is not None:
                if new_password == confirm_password:
                    user = request.user
                    user.set_password(new_password)
                    user.save()
                    messages.success(request, 'Your password was updated successfully!')
                    return redirect('login') 
                else:
                    messages.error(request, 'New passwords do not match.')
            else:
                messages.error(request, 'Old password is incorrect.')
        else:
            messages.error(request, 'All fields are required.')

        return render(request, 'profile.html')

class EditProfileView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return render(request, 'profile.html', {
            'user': request.user
        })

    def post(self, request, *args, **kwargs):
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')

        user = request.user
        user.username = full_name
        user.email = email
        user.phone_number = phone_number

        user.save()
        
        messages.success(request, "Profile updated successfully")
        return redirect('edit_profile')

class Unit(LoginRequiredMixin, View):
    def get(self, request):
        unit_data_all = Units.objects.all()
        return render(request, 'unit.html', {'units': unit_data_all})

    def post(self, request):
        unit_name = request.POST.get('unit_name')

        if not unit_name:
            messages.error(request, "Unit name is required.")
            return redirect('unit')

        if Units.objects.filter(unit_name__iexact=unit_name).exists():
            messages.error(request, "A unit with this name already exists.")
            return redirect('unit')

        Units.objects.create(unit_name=unit_name)
        messages.success(request, "Unit added successfully.")
        return redirect('unit')

class ActivateProductView(LoginRequiredMixin, View):
    def post(self, request, product_id):
        product = get_object_or_404(Product, product_id=product_id)
        product.is_active = True
        product.save()
        messages.success(request, "Product activated successfully.")
        return redirect('product')

class DeactivateProductView(LoginRequiredMixin, View):
    def post(self, request, product_id):
        product = get_object_or_404(Product, product_id=product_id)
        product.is_active = False
        product.save()
        messages.success(request, "Product deactivated successfully.")
        return redirect('product')

class ProductView(LoginRequiredMixin, View):
    def get(self, request):
        query = request.GET.get('q', '')
        units = Units.objects.all()

        if query:
            # Try to filter by product_id if the query is numeric
            if query.isdigit():
                products = Product.objects.filter(product_id=query)
            else:
                products = Product.objects.filter(product_name__icontains=query)
            no_results = not products.exists()
        else:
            products = Product.objects.all()
            no_results = False
        
        paginator = Paginator(products, 10)  
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'products': page_obj,
            'query': query,
            'no_results': no_results,
            'units': units,
        }
        return render(request, 'product.html', context)

    def post(self, request, product_id=None):
        product_name = request.POST.get('product_name')
        product_type = request.POST.get('product_type')
        product_quantity = request.POST.get('product_quantity')
        unit_id = request.POST.get('unit_id')
        price = request.POST.get('price')  # New price field
        transaction_type = 'Buy'

        if not product_name or not product_type or not product_quantity or not price:
            messages.error(request, "Product name, product type, quantity, and price are required.")
            return HttpResponseRedirect(reverse('product'))

        # Convert price to a decimal type
        try:
            price = float(price)
        except ValueError:
            messages.error(request, "Invalid price value.")
            return HttpResponseRedirect(reverse('product'))

        if product_id:
            try:
                product = get_object_or_404(Product, product_id=product_id)
                product.product_name = product_name
                product.product_type = product_type
                product.product_quantity = product_quantity
                product.unit = get_object_or_404(Units, id=unit_id)
                product.price = price  # Update price
                product.transaction_type = transaction_type
                product.save()
                messages.success(request, "Product record updated successfully.")
            except Product.DoesNotExist:
                messages.error(request, "Product does not exist in the table")
        else:
            existing_product = Product.objects.filter(product_name__iexact=product_name).first()
            if existing_product:
                messages.error(request, "A product with this name already exists.")
                return HttpResponseRedirect(reverse('product'))

            product_id = self.get_next_product_id()
            product = Product(
                product_id=product_id,
                product_name=product_name,
                product_type=product_type,
                product_quantity=product_quantity,
                price=price,  # Set price
                transaction_type=transaction_type,
                unit=get_object_or_404(Units, id=unit_id),
            )
            product.save()

            stock, created = ProductStock.objects.get_or_create(product_id=product, defaults={'product_quantity': float(product_quantity)})

            self.create_history_record(product, product_quantity, transaction_type)
            messages.success(request, "Product created successfully.")

        return HttpResponseRedirect(reverse('product'))

    def get_next_product_id(self):
        max_id = Product.objects.aggregate(Max('product_id'))['product_id__max']
        return max_id + 1 if max_id is not None else 1

    def create_history_record(self, product, product_quantity, transaction_type):
        History.objects.create(
            product_id=product,
            product_quantity=product_quantity,
            transaction_type=transaction_type, 
        )

    def update_product_stock(self, product, product_quantity, transaction_type):
        stock, created = ProductStock.objects.get_or_create(product_id=product)

        if transaction_type == 'Buy':
            stock.product_quantity += float(product_quantity)
        elif transaction_type == 'Sell':
            stock.product_quantity -= float(product_quantity)
        stock.save()

class ProductStockView(LoginRequiredMixin, View):
    def get(self, request):
        query = request.GET.get('q', '')
        sort_by = request.GET.get('sort', 'product_id')
        sort_order = request.GET.get('order', 'asc')
        units = Units.objects.all()
        stock_data_all = ProductStock.objects.all()

        product_data_all = Product.objects.filter(is_active=True)

        low_stock_threshold = request.session.get('low_stock_threshold', 100)

        valid_sort_fields = ['product_id', 'product_name', 'product_quantity', 'updated_date']
        if sort_by not in valid_sort_fields:
            sort_by = 'product_id'

        if sort_order == 'desc':
            sort_by = '-' + sort_by

        if query:
            # Try to filter by product_id or product_name
            try:
                product_id = int(query)
                products = Product.objects.filter(product_id=product_id)
            except ValueError:
                products = Product.objects.filter(product_name__icontains=query)
            stock_data = ProductStock.objects.filter(product_id__in=products)
            no_results = not stock_data.exists()
        else:
            stock_data = ProductStock.objects.all()
            no_results = False

        stock_data = stock_data.order_by(sort_by)

        paginator = Paginator(stock_data, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'stock_data': page_obj,
            'query': query,
            'sort_by': sort_by,
            'sort_order': sort_order,
            'no_results': no_results,
            'low_stock_threshold': low_stock_threshold,
            'units': units,
            'product_data_all': product_data_all, 
            'stock_data_all': stock_data_all
        }
        return render(request, 'productstock.html', context)

    def post(self, request, stock_id=None):
        product_id = request.POST.get('product_id')
        product_quantity = request.POST.get('product_quantity')
        transaction_type = request.POST.get('transaction_type')

        if not product_id or not product_quantity or not transaction_type:
            messages.error(request, "Product ID, Quantity, and Transaction Type are required.")
            return redirect('product_stock')

        try:
            product_id = int(product_id)
            product = get_object_or_404(Product, product_id=product_id, is_active=True)
        except ValueError:
            messages.error(request, "Your product ID is not in the table")
            return redirect('product_stock')

        try:
            product_quantity = float(product_quantity)
        except ValueError:
            messages.error(request, "Invalid quantity.")
            return redirect('product_stock')

        productstock, created = ProductStock.objects.get_or_create(product_id=product)

        if transaction_type == 'Buy':
            productstock.product_quantity += product_quantity
        elif transaction_type == 'Sell':
            if productstock.product_quantity < product_quantity:
                messages.error(request, "Please enter proper Sell Quantity")
                return redirect('product_stock')
            productstock.product_quantity -= product_quantity
        else:
            messages.error(request, "Invalid transaction type.")
            return redirect('product_stock')

        productstock.save()

        History.objects.create(
            product_id=product, 
            product_quantity=product_quantity,
            transaction_type=transaction_type,
        )

        messages.success(request, f"Stock {'updated' if not created else 'created'} successfully.")
        return redirect('product_stock')

class HistoryView(LoginRequiredMixin, View):
    def get(self, request, history_id=None):
        units = Units.objects.all()
        query = request.GET.get('q', '')
        sort_by = request.GET.get('sort', 'id') 
        sort_order = request.GET.get('order', 'desc') 
        selected_product_id = request.GET.get('product', '')

        valid_sort_fields = ['id', 'product_id', 'product_name', 'product_quantity', 'updated_date']
        all_products = Product.objects.filter(is_active=True)

        if sort_by not in valid_sort_fields:
            sort_by = 'id'

        if sort_order == 'desc':
            sort_by = '-' + sort_by

        if history_id:
            history_record = get_object_or_404(History, id=history_id)
            history_data = History.objects.all().order_by('-id')
            context = {
                'history_data': history_data,
                'edit_record': history_record,
                'action': 'edit',
                'query': query,
                'product_data_all': all_products,
            }
        else:   
            if selected_product_id:
                try:
                    product_id = int(selected_product_id)
                    history_data = History.objects.filter(product_id=product_id)
                except ValueError:
                    history_data = History.objects.none()
            elif query:
                products = Product.objects.filter(product_name__icontains=query)
                history_data = History.objects.filter(product_id__in=products)
            else:
                history_data = History.objects.all()

            history_data = history_data.order_by(sort_by)
            paginator = Paginator(history_data, 10)
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)

            context = {
                'history_data': page_obj,
                'action': 'create',
                'query': query,
                'paginator': paginator,
                'page_obj': page_obj,
                'sort_by': sort_by,
                'sort_order': sort_order,
                'no_results': not history_data.exists(),
                'all_products': all_products,
            }

        return render(request, 'history.html', context)

    def post(self, request, history_id=None):
        product_id = request.POST.get('product_id')
        product_quantity = request.POST.get('product_quantity')
        transaction_type = request.POST.get('transaction_type')

        if history_id:
            history_record = get_object_or_404(History, id=history_id)
            old_quantity = history_record.product_quantity
            old_transaction_type = history_record.transaction_type

            if product_quantity:
                history_record.product_quantity = product_quantity
                history_record.save()

                self.stock_update_hist(history_record.product_id, old_quantity, old_transaction_type, product_quantity, old_transaction_type)
                messages.success(request, "History record updated successfully.")
            else:
                messages.error(request, "Product Quantity is required.")
        else:
            if not product_id or not product_quantity or not transaction_type:
                messages.error(request, "Product ID, Quantity, and Transaction Type are required.")
                return HttpResponseRedirect(reverse('history'))

            product = get_object_or_404(Product, id=product_id, is_active=True)

            History.objects.create(
                product_id=product,
                product_quantity=product_quantity,
                transaction_type=transaction_type,
            )
            self.stock_update_hist(product, 0, '', product_quantity, transaction_type)
            messages.success(request, "History record created successfully.")

        return HttpResponseRedirect(reverse('history'))

    def stock_update_hist(self, product, old_quantity, old_transaction_type, new_quantity, new_transaction_type):
        stock, created = ProductStock.objects.get_or_create(product_id=product)

        if old_transaction_type == 'Buy':
            stock.product_quantity -= old_quantity
        elif old_transaction_type == 'Sell':
            stock.product_quantity += old_quantity

        if new_transaction_type == 'Buy':
            stock.product_quantity += float(new_quantity)
        elif new_transaction_type == 'Sell':
            stock.product_quantity -= float(new_quantity)

        stock.save()

class PDFView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        # Extract search parameters from the GET request
        selected_products = request.GET.get('selectedProducts', '[]')
        query = request.GET.get('q', '')
        product_filter = request.GET.get('product', '')

        selected_products = json.loads(selected_products)
        
        # Filter history data based on search parameters
        if selected_products:
            history_data = History.objects.filter(product_id__in=selected_products)
        elif product_filter:
            products = Product.objects.filter(id=product_filter)
            history_data = History.objects.filter(product_id__in=products)
        elif query:
            products = Product.objects.filter(product_name__icontains=query)
            history_data = History.objects.filter(product_id__in=products)
        else:
            history_data = History.objects.all()

        current_datetime = now().strftime('%d-%m-%Y %H:%M:%S')
        pdf_company = request.session.get('pdf_company', None)
        centered_title = request.session.get('centered_title', 'Product History Report')
        company_logo_path = request.session.get('company_logo', None)
        columns = request.session.get('columns', [])

        if not columns:
            columns = ['product_name']

        if company_logo_path:
            company_logo_url = request.build_absolute_uri(company_logo_path)
        else:
            company_logo_url = None

        context = {
            'history_data': history_data,
            'current_datetime': current_datetime,
            'pdf_company': pdf_company,
            'centered_title': centered_title,
            'company_logo': company_logo_url,
            'columns': columns,
        }

        # Render the template to HTML
        template_path = 'pdf.html'
        template = get_template(template_path)
        html = template.render(context, request)

        return HttpResponse(html)

class PDFCreateView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        # Extract search parameters from the GET request
        selected_products = request.GET.get('selectedProducts', '[]')
        query = request.GET.get('q', '')
        product_filter = request.GET.get('product', '')

        selected_products = json.loads(selected_products)
        
        # Filter history data based on search parameters
        if selected_products:
            history_data = History.objects.filter(product_id__in=selected_products)
        elif product_filter:
            products = Product.objects.filter(id=product_filter)  # Adjust this line based on your exact filtering logic
            history_data = History.objects.filter(product_id__in=products)
        elif query:
            products = Product.objects.filter(product_name__icontains=query)
            history_data = History.objects.filter(product_id__in=products)
        else:
            history_data = History.objects.all()

        current_datetime = now().strftime('%d-%m-%Y %H:%M:%S')
        pdf_company = request.session.get('pdf_company', None)
        centered_title = request.session.get('centered_title', 'Product History Report')
        company_logo_path = request.session.get('company_logo', None)
        columns = request.session.get('columns', [])

        if not columns:
            columns = ['product_name']

        # Ensure the company_logo_path is an absolute URL
        if company_logo_path:
            company_logo_url = request.build_absolute_uri(company_logo_path)
        else:
            company_logo_url = None

        template_path = 'pdf.html'
        context = {
            'history_data': history_data,
            'current_datetime': current_datetime,
            'pdf_company': pdf_company,
            'centered_title': centered_title,
            'company_logo': company_logo_url,
            'columns': columns,
        }

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="Product_History_Report.pdf"'

        template = get_template(template_path)
        html = template.render(context, request)

        pisa_status = pisa.CreatePDF(html, dest=response)

        if pisa_status.err:
            return HttpResponse('We had some errors <pre>' + html + '</pre>')

        return response

class UpdatePDF(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        pdf_company = request.POST.get('pdf_company')
        centered_title = request.POST.get('centered_title')
        company_logo = request.FILES.get('company_logo')
        include_option = request.POST.get('include_option')
        columns = request.POST.getlist('columns')

        if pdf_company:
            request.session['pdf_company'] = pdf_company
        if centered_title:
            request.session['centered_title'] = centered_title

        if company_logo:
            logo_folder = 'company_logos'
            logo_path = os.path.join(logo_folder, company_logo.name)

            # Save the uploaded file to the media directory
            with default_storage.open(logo_path, 'wb+') as destination:
                for chunk in company_logo.chunks():
                    destination.write(chunk)

            # Construct the URL for accessing the logo
            logo_url = os.path.join(settings.MEDIA_URL, logo_path).replace('\\', '/')
            request.session['company_logo'] = logo_url

        if include_option in ['pdf_company', 'company_logo']:
            request.session['include_option'] = include_option
        else:
            request.session['include_option'] = 'none'

        # Save selected columns
        if not columns:
            columns = ['product_id', 'product_name']
        request.session['columns'] = columns 

        messages.success(request, 'PDF updated successfully!')
        return redirect('unit')


from django.contrib import messages
from django.shortcuts import redirect
from django.views import View
from .models import Product, ProductStock, History
from decimal import Decimal
from num2words import num2words
import qrcode
import base64
from io import BytesIO
from django.template.loader import render_to_string
from django.http import HttpResponse
from xhtml2pdf import pisa
from django.utils.timezone import now

def convert_to_words(amount):
    return num2words(amount, lang='en')

class BillingView(LoginRequiredMixin, View):
    def get(self, request):
        # Only get active products
        products = Product.objects.filter(is_active=True)
        return render(request, 'billing.html', {'products': products})

    def post(self, request):
        # Collect customer details
        customer_name = request.POST.get('customer_name')
        customer_address = request.POST.get('customer_address')
        customer_contact = request.POST.get('customer_contact')
        company_name = request.POST.get('company_name')  
        selected_products = request.POST.getlist('product_id')
        quantities = request.POST.getlist('quantity')
        prices = request.POST.getlist('price')

        current_datetime = now().strftime('%d-%m-%Y %H:%M:%S')
        items = []
        total_amount = Decimal('0.00')
        total_quantity = 0  

        for product_id, quantity, price in zip(selected_products, quantities, prices):
            if quantity.isdigit() and int(quantity) > 0:
                product = get_object_or_404(Product, id=product_id, is_active=True)  # Ensure product is active
                quantity = int(quantity)

                if price and price.replace('.', '', 1).isdigit():
                    amount = Decimal(price) * quantity
                    actual_price = Decimal(price)
                else:
                    amount = product.price * quantity
                    actual_price = product.price

                stock = ProductStock.objects.filter(product_id=product_id).first()
                if stock and stock.product_quantity < quantity:
                    messages.error(request, f"Not enough stock for {product.product_name}.")
                    return redirect('billing')

                sgst_rate = Decimal('0.09')  # 9%
                cgst_rate = Decimal('0.09')  # 9%
                sgst_value = amount * sgst_rate
                cgst_value = amount * cgst_rate

                total_amount += amount
                total_quantity += quantity
                items.append({
                    'product': product,
                    'quantity': quantity,
                    'price': actual_price,
                    'amount': amount,
                    'sgst_value': sgst_value,
                    'cgst_value': cgst_value,
                })

                # Deduct stock after confirming the items are added
                stock.product_quantity -= quantity
                stock.save()  # Save the updated stock

                # Create history record
                self.create_history_record(product, quantity, 'Sell')

        if not items:
            messages.error(request, "No items selected.")
            return redirect('billing')

        grand_total = total_amount + sum(item['sgst_value'] for item in items) + sum(item['cgst_value'] for item in items)
        
        # Convert total amount to words
        total_amount_words = convert_to_words(grand_total)

        # Generate QR Code for GPay with amount
        qr_data = f"upi://pay?pa=kalolaparam234@oksbi&pn=Param%20Kalola&mc=YOUR_MERCHANT_CODE&tid=INVOICE_ID&am={grand_total}&cu=INR&tn=Payment%20for%20Invoice"
        qr_img = qrcode.make(qr_data)
        buffered = BytesIO()
        qr_img.save(buffered, format="PNG")
        qr_code_base64 = base64.b64encode(buffered.getvalue()).decode()

        context = {
            'items': items,
            'total_amount': total_amount,
            'total_quantity': total_quantity,
            'company_name': company_name,
            'customer_name': customer_name,
            'customer_address': customer_address,
            'customer_contact': customer_contact,
            'sgst_amount': sum(item['sgst_value'] for item in items),
            'cgst_amount': sum(item['cgst_value'] for item in items),
            'grand_total': grand_total,
            'grand_total_words': total_amount_words,
            'current_datetime': current_datetime,
            'qr_code': qr_code_base64,
        }

        html_string = render_to_string('invoice.html', context)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="invoice.pdf"'

        pisa_status = pisa.CreatePDF(html_string, dest=response)

        if pisa_status.err:
            messages.error(request, "Error generating PDF.")
            return redirect('billing')

        return response

    def create_history_record(self, product, product_quantity, transaction_type):
        History.objects.create(
            product_id=product,
            product_quantity=product_quantity,
            transaction_type=transaction_type, 
        )
