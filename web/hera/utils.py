

def get_sanitized_hstore_dict(context: dict) -> dict:
    result = dict()
    for key in context:
        value = context[key]
        if isinstance(value, list):
            value = [str(v) for v in value]
            result[key] = ', '.join(value)
        else:
            result[key] = value
    return result