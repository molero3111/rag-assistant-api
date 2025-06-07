from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.tokens import AccessToken, BlacklistMixin
from rest_framework import exceptions
from django.conf import settings
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

class CustomJWTAuthentication(JWTAuthentication):
    def get_validated_token(self, raw_token):
        token = super().get_validated_token(raw_token)
        # Check if token is blacklisted (denylist)
        jti = token.get('jti')
        if jti:
            try:
                outstanding_token = OutstandingToken.objects.get(jti=jti)
                if BlacklistedToken.objects.filter(token=outstanding_token).exists():
                    raise InvalidToken('Token is blacklisted')
            except OutstandingToken.DoesNotExist:
                pass  # If not found, treat as valid (could be access token not in DB)
        return token
