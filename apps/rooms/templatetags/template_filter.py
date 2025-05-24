from django import template
register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Template filter to get an item from a dictionary by key.
    This is needed because Django templates don't allow accessing dictionary items with variables.

    Usage in template:
    {{ my_dict|get_item:my_key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)







# @register.filter(name='get_item') # The name here must match what's in your template
# def get_item(dictionary, key):
#             if isinstance(dictionary, dict):
#                return dictionary.get(key)
#             return None
