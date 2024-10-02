from django.contrib import admin
from .models import CustomUser, Landlord, Leasee,Room,Deposit,Notification, VisitRequest,ContactForm

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name' ,'is_staff', 'is_active', 'date_joined')

@admin.register(Landlord)
class LandlordAdmin(admin.ModelAdmin):
    list_display = ('id','user',)

@admin.register(Leasee)
class LeaseeAdmin(admin.ModelAdmin):
    list_display = ('id','user', 'preferred_location',)

@admin.register(Room)
class LeaseeAdmin(admin.ModelAdmin):
    list_display = ['title', 'rent_giver', 'price', 'is_available', 'rating']
    

@admin.register(Deposit)
class LeaseeAdmin(admin.ModelAdmin):
    list_display = ('leasee', 'room', 'amount', 'payment_status',)
@admin.register(ContactForm)
class LeaseeAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'email', 'subject', 'message','status',)

admin.site.register(Notification)
admin.site.register(VisitRequest)

