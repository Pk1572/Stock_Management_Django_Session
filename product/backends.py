from django.contrib.auth.backends import ModelBackend
from .models import CustomUser
from django.db.models import Q

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None):
        try:
            user = CustomUser.objects.get( Q(email = username) | Q(phone_number = username))
            if user.check_password(password):
                return user
            return None
        except CustomUser.DoesNotExist:
            return None

    def get_user(self,user_id):
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None
