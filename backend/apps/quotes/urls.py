from django.urls import path

from . import views

urlpatterns = [
    path("", views.QuoteList.as_view(), name="quote-list"),
    path("<int:pk>/", views.QuoteDetail.as_view(), name="quote-detail"),
    path("<int:pk>/render-pdf/", views.RenderQuotePdfView.as_view(), name="quote-render-pdf"),
    path("<int:pk>/pdf/", views.DashboardQuotePdfView.as_view(), name="quote-pdf-download"),
]
