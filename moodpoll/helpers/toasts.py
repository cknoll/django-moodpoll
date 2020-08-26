from ..utils import init_session_toasts

def error(request, text):
    init_session_toasts(request)
    request.session['toasts']['error'].append(text)

def warning(request, text):
    init_session_toasts(request)
    request.session['toasts']['warning'].append(text)

def info(request, text):
    init_session_toasts(request)
    request.session['toasts']['info'].append(text)

def success(request, text):
    init_session_toasts(request)
    request.session['toasts']['success'].append(text)
