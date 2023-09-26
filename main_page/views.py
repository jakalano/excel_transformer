from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

def main_page(request):
    template = loader.get_template('1_index.html')
    return HttpResponse(template.render())

def summary(request):
    template = loader.get_template('2_file_summary.html')
    return HttpResponse(template.render())

def edit_data(request):
    template = loader.get_template('3_edit_data.html')
    return HttpResponse(template.render())

def edit_columns(request):
    template = loader.get_template('4_edit_columns.html')
    return HttpResponse(template.render())

def download(request):
    template = loader.get_template('5_download.html')
    return HttpResponse(template.render())