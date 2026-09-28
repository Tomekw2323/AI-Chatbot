"""Public API of the organizations module.

Other modules must use these functions instead of querying ``Membership``
directly, so the permission rules live in one place.
"""

from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.db import transaction

from apps.accounts.models import User

from .models import Membership, Organization, OrganizationQuerySet

AnyUser = AbstractBaseUser | AnonymousUser


def can_manage_organization(user: AnyUser, organization: Organization) -> bool:
    """Owners and admins may edit the organization and its listings."""
    if not user.is_authenticated:
        return False
    return Membership.objects.filter(
        organization=organization, user_id=user.pk, role__in=Membership.MANAGER_ROLES
    ).exists()


def managed_organizations(user: AnyUser) -> OrganizationQuerySet:
    if not user.is_authenticated:
        return Organization.objects.none()
    return Organization.objects.filter(
        memberships__user_id=user.pk, memberships__role__in=Membership.MANAGER_ROLES
    ).distinct()


@transaction.atomic
def create_organization(organization: Organization, owner: User) -> Organization:
    organization.save()
    Membership.objects.create(organization=organization, user=owner, role=Membership.Role.OWNER)
    return organization
