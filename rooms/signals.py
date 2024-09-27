# rooms/signals.py

from django.db.models.signals import post_migrate
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.apps import apps
from django.dispatch import receiver

@receiver(post_migrate)
def create_default_groups(sender, **kwargs):
    # Create default groups here (e.g., Rent Giver, Rent Taker)
    rent_giver_group, created = Group.objects.get_or_create(name='Landlord')
    rent_taker_group, created = Group.objects.get_or_create(name='Leasee')

    # Comment out permission assignment for now, since permissions may not exist yet
    # content_type = ContentType.objects.get_for_model(apps.get_model('rooms', 'Room'))
    
    # try:
    #     can_add_room = Permission.objects.get(codename='add_room', content_type=content_type)
    #     rent_giver_group.permissions.add(can_add_room)
    # except Permission.DoesNotExist:
    #     print("Permission does not exist yet, skipping assignment.")
    
    # You can repeat the permission fetching for other models and groups as needed

    print(f"Created groups: Landlord and Leasee")







# from django.db.models.signals import post_migrate
# from django.contrib.auth.models import Group, Permission
# from django.dispatch import receiver
# from django.contrib.contenttypes.models import ContentType
# from .models import CustomUser, Landlord, Leasee

# @receiver(post_migrate)
# def create_default_groups(sender, **kwargs):
#     """Create default groups and assign permissions to them."""
    
#     # Create Landlord group
#     landlord_group, created = Group.objects.get_or_create(name='Landlord')
#     if created:
#         # Add permissions for Landlords (e.g., managing rooms)
#         # Assuming that Landlord will manage 'Room' model (you'll need to create it)
#         content_type = ContentType.objects.get_for_model(Landlord)
#         can_add_room = Permission.objects.get(codename='add_room', content_type=content_type)
#         can_change_room = Permission.objects.get(codename='change_room', content_type=content_type)
#         landlord_group.permissions.add(can_add_room, can_change_room)

#     # Create Leasee group
#     leasee_group, created = Group.objects.get_or_create(name='Leasee')
#     if created:
#         # Leasees can only view rooms, not create or modify them
#         content_type = ContentType.objects.get_for_model(Leasee)
#         can_view_room = Permission.objects.get(codename='view_room', content_type=content_type)
#         leasee_group.permissions.add(can_view_room)

#     # Create Admin group (if you want non-superuser staff access to limited functions)
#     admin_group, created = Group.objects.get_or_create(name='Admin')
#     if created:
#         # Admins can manage both Landlord and Leasee profiles but don't have full superuser privileges
#         content_type_user = ContentType.objects.get_for_model(CustomUser)
#         view_user = Permission.objects.get(codename='view_user', content_type=content_type_user)
#         change_user = Permission.objects.get(codename='change_user', content_type=content_type_user)
#         admin_group.permissions.add(view_user, change_user)



