from django import template
from urllib.parse import urlencode, parse_qs, urlparse

register = template.Library()

@register.filter
def remove_param(url, param):
    """
    Remove a parameter from a URL query string.
    Usage: {{ request.get_full_path|remove_param:"param_name" }}
    """
    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    if param in params:
        del params[param]

    # Rebuild the URL
    query = urlencode(params, doseq=True)
    return f"{parsed.path}?{query}" if query else parsed.path