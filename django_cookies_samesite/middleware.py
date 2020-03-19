# Cookie library has moved to http in python3
try:
    import Cookie
except ImportError:
    import http.cookies as Cookie
    
import re

import warnings

import django

from distutils.version import LooseVersion

from django.conf import settings

try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    MiddlewareMixin = object


Cookie.Morsel._reserved['samesite'] = 'SameSite'
CHROME_VALIDATE_REGEX = "(Chrome|Chromium)\/((5[1-9])|6[0-6])"

# TODO: change this to 3.1.0 once Django 3.1 is released
DJANGO_SUPPORTED_VERSION = '3.0.0'

class CookiesSameSite(MiddlewareMixin):
    """
    Support for SameSite attribute in Cookies is fully implemented in Django 3.1 and won't
    be back-ported to Django 2.x.
    This middleware will be obsolete when your app will start using Django 3.1.
    """
    def process_response(self, request, response):
        # same-site = None introduced for Chrome 80 breaks for Chrome 51-66 
        # Refer (https://www.chromium.org/updates/same-site/incompatible-clients)
        http_user_agent = request.META.get('HTTP_USER_AGENT') or " "
        if re.search(CHROME_VALIDATE_REGEX, http_user_agent):
            return response
        if LooseVersion(django.get_version()) >= LooseVersion(DJANGO_SUPPORTED_VERSION):
            raise DeprecationWarning(
                'Your version of Django supports SameSite flag in the cookies mechanism. '
                'You should remove django-cookies-samesite from your project.'
            )

        protected_cookies = getattr(
            settings,
            'SESSION_COOKIE_SAMESITE_KEYS',
            set()
        ) or set()

        if not isinstance(protected_cookies, (list, set, tuple)):
            raise ValueError('SESSION_COOKIE_SAMESITE_KEYS should be a list, set or tuple.')

        protected_cookies = set(protected_cookies)
        protected_cookies |= {settings.SESSION_COOKIE_NAME, settings.CSRF_COOKIE_NAME}

        samesite_flag = getattr(
            settings,
            'SESSION_COOKIE_SAMESITE',
            None
        )

        if not samesite_flag:
            return response

        samesite_flag = samesite_flag.lower()

        if samesite_flag not in {'lax', 'none', 'strict', 'none; secure'}:
            raise ValueError('samesite must be "lax", "none", or "strict".')

        samesite_force_all = getattr(
            settings,
            'SESSION_COOKIE_SAMESITE_FORCE_ALL',
            False
        )
        if samesite_force_all:
            for cookie in response.cookies:
                response.cookies[cookie]['samesite'] = samesite_flag
        else:
            for cookie in protected_cookies:
                if cookie in response.cookies:
                    response.cookies[cookie]['samesite'] = samesite_flag

        return response
