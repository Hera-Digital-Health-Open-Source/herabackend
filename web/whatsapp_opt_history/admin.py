from django.contrib import admin
from whatsapp_opt_history.models import WhatsAppOptHistory

class WhatsAppOptInOutAdmin(admin.ModelAdmin):
    list_display = ('username', 'opt_status', 'opt_datetime', 'source')

    readonly_fields = ('opt_datetime',)  # Make it read-only

admin.site.register(WhatsAppOptHistory, WhatsAppOptInOutAdmin)