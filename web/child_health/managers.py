from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from django.contrib.auth.models import User
from django.db.models import Manager
from django.utils import timezone


if TYPE_CHECKING:
    from child_health.models import Pregnancy


class PregnancyManager(Manager):
    def get_active_pregnancy_for_user(self, user: User) -> Optional[Pregnancy]:
        today = timezone.now().date()
        return self.filter(
            estimated_delivery_date__gte=today
        ).filter(
            user__exact=user
        ).order_by(
            '-id'
        ).first()
