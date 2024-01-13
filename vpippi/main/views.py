from django.shortcuts import render, redirect


def index(request):
    return redirect("https://scholar.google.com/citations?user=OHmt2vUAAAAJ")