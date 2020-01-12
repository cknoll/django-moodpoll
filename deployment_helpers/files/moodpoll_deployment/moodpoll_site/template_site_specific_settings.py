
# {{context.warning}}

{% for key, value in context.app_settings.items() %}
{{key}} = {{value}}
{% endfor %}
