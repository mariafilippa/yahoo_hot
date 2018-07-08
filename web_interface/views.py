from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.generic import View
from django.views.generic.list import ListView

from web_interface.models import Category, Product


# Create your views here.
class SearchView(ListView):
    model = Product
    template_name = 'search.html'

    def get_queryset(self):
        queryset = super().get_queryset()

        zone = self.request.GET.get('zone')
        category = self.request.GET.get('category')
        if not zone: zone = 1
        if category:
            queryset = queryset.filter(category=category)
        else:
            queryset = queryset.filter(category=zone)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(** kwargs)
        context['zones'] = Category.objects.filter(zone=None)
        return context


class FetchView(View):
    def get(self, request, pk):
        categories = Category.objects.filter(zone=pk)
        json_list = [{'id': str(category.id), 'name': category.name}
                            for category in categories]
        print(json_list)
        return JsonResponse(json_list, safe=False)
