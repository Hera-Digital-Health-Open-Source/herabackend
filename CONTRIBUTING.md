# Code Style Guidelines

This document shows the preferred coding style for things that can be achieved in 
multiple ways. This is a general guideline. If you have a strong reason to deviate
from this style in your specific context, please feel free to do so. Preferably,
you can add comment in the code or Pull Request explaining why the chosen approach
is more appropriate for your context. 


## Django Models

### Choice Field

It is preferred to declare choice fields as a class instead of as an array of tuples.

:white_check_mark: Preferred

```
class Gender(models.TextChoices):
    MALE = 'MALE', _('Male')
    FEMALE = 'FEMALE', _('Female')

class Foo:
    gender = models.CharField(choices=Gender.choices)
```

:man_shrugging: Not Preffered

```
class Foo:
    gender = models.CharField(
        choices=[('MALE', _('Male')), ('FEMALE', _('Female'))]
```

