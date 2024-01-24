
from django.urls import path
from .views import *

urlpatterns = [
        path('', home, name='home'),
        path('askAi', askAi, name='askAi'),

]
