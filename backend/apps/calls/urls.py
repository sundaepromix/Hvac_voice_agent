from django.urls import path

from . import views

urlpatterns = [
    path("", views.CallList.as_view(), name="call-list"),
    path("bulk-delete/", views.bulk_delete_calls, name="call-bulk-delete"),
    # Outbound calling (declared before <int:pk> so "outbound" isn't read as a pk).
    path("outbound/", views.outbound_list, name="outbound-list"),
    path("outbound/call-now/", views.outbound_call_now, name="outbound-call-now"),
    path("outbound/reactivate/", views.outbound_reactivate, name="outbound-reactivate"),
    path("outbound/cron/", views.outbound_cron, name="outbound-cron"),
    path("outbound/cron/<str:secret>/", views.outbound_cron, name="outbound-cron-keyed"),
    path("<int:pk>/", views.CallDetail.as_view(), name="call-detail"),
    path("webhooks/vapi/", views.VapiWebhook.as_view(), name="vapi-webhook"),
    path("webhooks/twilio/", views.TwilioWebhook.as_view(), name="twilio-webhook"),
    # Vapi custom-LLM mode hits this on every conversation turn.
    # Some Vapi versions append /chat/completions, others don't — register both forms.
    path("vapi/chat/completions/", views.chat_completions, name="vapi-chat-completions"),
    path("vapi/chat/completions", views.chat_completions, name="vapi-chat-completions-noslash"),
    path("vapi/", views.chat_completions, name="vapi-chat-completions-bare"),
    path("vapi", views.chat_completions, name="vapi-chat-completions-bare-noslash"),
    # Keyed variants — Vapi appends "/chat/completions" to model.url, which
    # corrupts any query string ("?key=SECRET/chat/completions"). Putting the
    # secret in the PATH instead survives the auto-append cleanly.
    # Set model.url = "https://.../api/calls/vapi/k/<SECRET>" — Vapi will hit
    # ".../api/calls/vapi/k/<SECRET>/chat/completions" which matches below.
    path("vapi/k/<str:secret>/chat/completions/", views.chat_completions, name="vapi-chat-keyed"),
    path("vapi/k/<str:secret>/chat/completions", views.chat_completions, name="vapi-chat-keyed-noslash"),
    path("vapi/k/<str:secret>/", views.chat_completions, name="vapi-chat-keyed-bare"),
    path("vapi/k/<str:secret>", views.chat_completions, name="vapi-chat-keyed-bare-noslash"),
]
