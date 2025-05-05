from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import get_template
from django.template.exceptions import TemplateDoesNotExist

def index(response):
    try:
        tpl = get_template("index.html")
        return render(response,"index.html")
    except TemplateDoesNotExist:
        return HttpResponse("Backend OK. Posa en marxa el frontend seguint el README.")

def custom404(request, exception=None):
    return render(request, '404.html', status=404)

def custom403(request, exception=None):
    return render(request, '403.html', status=403)