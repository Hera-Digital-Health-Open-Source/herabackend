def mask_username(s):
    return s[0:5] + ''.join(['*' for i in range(len(s) - 5)])


def verbose_name(model_class, attribute):
    return model_class._meta.get_field(attribute).verbose_name.capitalize()
