"""aws_interface URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
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
from django.urls import path

from dashboard.views.register import Register
from dashboard.views.logout import Logout
from dashboard.views.login import Login
from dashboard.views.index import Index
from dashboard.views.accesskey import AccessKey
from dashboard.views.apps import Apps

from dashboard.views.app.auth import Auth
from dashboard.views.app.overview import Overview
from dashboard.views.app.storage import Storage
from dashboard.views.app.database import Database
from dashboard.views.app.logic import Logic
from dashboard.views.app.log import Log
from dashboard.views.app.bill import Bill
from dashboard.views.app.guide import Guide


urlpatterns = [
    path('admin/', admin.site.urls),

    path('', Index.as_view(), name='index'),

    path('login/', Login.as_view(), name='login'),
    path('register/', Register.as_view(), name='register'),
    path('apps/', Apps.as_view(), name='apps'),
    path('logout/', Logout.as_view(), name='logout'),
    path('accesskey/', AccessKey.as_view(), name='accesskey'),

    path('<app_id>/overview', Overview.as_view(), name='overview'),
    path('<app_id>/guide', Guide.as_view(), name='guide'),
    path('<app_id>/bill', Bill.as_view(), name='bill'),
    path('<app_id>/auth', Auth.as_view(), name='auth'),
    path('<app_id>/database', Database.as_view(), name='database'),
    path('<app_id>/storage', Storage.as_view(), name='storage'),
    path('<app_id>/logic', Logic.as_view(), name='logic'),
    path('<app_id>/log', Log.as_view(), name='log'),
]
