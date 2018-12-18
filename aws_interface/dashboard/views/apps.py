from dashboard.views.view import DashboardView
from django.shortcuts import render, HttpResponse
from django.views.generic import View


class Apps(View, DashboardView):

    def get(self, request):
        context = self.get_context(request)
        return render(request, 'dashboard/apps.html', context=context)

