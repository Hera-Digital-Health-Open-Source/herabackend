from whatsapp_opt_history.models import WhatsAppOptHistory

def is_user_opt_in(username):
    last_opt = WhatsAppOptHistory.objects \
        .filter(username=username) \
        .order_by('-opt_datetime') \
        .first()
    if last_opt:
        return last_opt.opt_status == "opt_in"
    else:
        return False