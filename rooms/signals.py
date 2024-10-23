from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group


@receiver(post_migrate)
def create_default_groups(sender, **kwargs):
    rent_giver_group, created = Group.objects.get_or_create(name="Landlord")
    rent_taker_group, created = Group.objects.get_or_create(name="Leasee")
    if created:
        print("rent giver group", rent_giver_group, created)
        print("rent taker group", rent_taker_group, created)
