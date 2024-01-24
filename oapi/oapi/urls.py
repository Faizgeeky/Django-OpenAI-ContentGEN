from django.contrib import admin
from django.urls import path, include
# import customBot

urlpatterns = [
    path("admin/", admin.site.urls),
    # path("", include('customBot.urls'),"cutom home"),
    path("", include('customBot.urls'), name='home'),


]
