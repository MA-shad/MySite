from django.shortcuts import render
from django.http import HttpResponse,JsonResponse

def login_view(request):
    return render(request,'login.html')

def test_view(request):
    return render(request,'test.html')
# Create your views here.
