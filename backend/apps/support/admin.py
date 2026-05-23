from django.contrib import admin

from .models import Ticket, TicketMessage


class TicketMessageInline(admin.TabularInline):
    model = TicketMessage
    extra = 0
    readonly_fields = ("direction", "author", "body", "provider_message_id", "created_at")
    can_delete = False
    show_change_link = False


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("id", "business", "channel", "sender_name", "sender_id", "status", "human_only", "last_message_at")
    list_filter = ("status", "channel", "human_only", "business")
    search_fields = ("sender_id", "sender_name", "subject")
    readonly_fields = ("created_at", "updated_at", "last_message_at")
    inlines = [TicketMessageInline]


@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "ticket", "direction", "author", "created_at")
    list_filter = ("direction", "author")
    search_fields = ("body", "provider_message_id")
    readonly_fields = ("created_at",)
