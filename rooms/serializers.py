from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rooms.models import (
    CustomUser,
    Landlord,
    Leasee,
    Room,
    Deposit,
    ContactForm,
    RoomImage,
)
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "is_landowner",
            "contact_number",
            "is_active",
            "is_staff",
            "date_joined",
        ]


class CustomUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)
    is_landowner = serializers.BooleanField(required=True)

    class Meta:
        model = CustomUser
        fields = [
            "email",
            "first_name",
            "last_name",
            "password",
            "password2",
            "is_landowner",
            "contact_number",
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        return attrs

    def create(self, validated_data):
        user = CustomUser.objects.create(
            email=validated_data["email"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            is_landowner=validated_data["is_landowner"],
            contact_number=validated_data["contact_number"],
        )
        user.set_password(validated_data["password"])
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        if email and password:
            # Check if the email is registered
            if not CustomUser.objects.filter(email=email).exists():
                raise serializers.ValidationError(
                    _("This email is not registered."), code="authorization"
                )

            user = authenticate(
                request=self.context.get("request"), email=email, password=password
            )
            if not user:
                raise serializers.ValidationError(
                    _("Password provided does not match."), code="authorization"
                )
        else:
            raise serializers.ValidationError(
                _("Must include 'email' and 'password'."), code="authorization"
            )

        data["user"] = user
        return data


class LandlordSerializer(serializers.ModelSerializer):
    email = serializers.ReadOnlyField(source="user.email")
    first_name = serializers.ReadOnlyField(source="user.first_name")
    last_name = serializers.ReadOnlyField(source="user.last_name")

    class Meta:
        model = Landlord
        fields = [
            "email",
            "first_name",
            "last_name",
            "contact_number",
            "address",
            "sub_address",
            "date_of_registration",
        ]


class LeaseeSerializer(serializers.ModelSerializer):
    email = serializers.ReadOnlyField(source="user.email")
    first_name = serializers.ReadOnlyField(source="user.first_name")
    last_name = serializers.ReadOnlyField(source="user.last_name")
    contact_number = serializers.ReadOnlyField(source="user.contact_number")

    class Meta:
        model = Leasee
        fields = [
            "email",
            "first_name",
            "last_name",
            "contact_number",
            "address",
            "sub_address",
            "preferred_location",
            "reviews",
            "location_url",
        ]


class RoomImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomImage
        fields = [
            "id",
            "image",
        ]  # 'id' is included so that you can retrieve it if needed


class RoomSerializer(serializers.ModelSerializer):
    owner_email = serializers.ReadOnlyField(source="rent_giver.user.email")
    contact_number = serializers.ReadOnlyField(source="rent_giver.user.contact_number")
    # Nested serializer for room images
    room_images = RoomImageSerializer(many=True, required=False)

    class Meta:
        model = Room
        fields = [
            "id",
            "owner_email",
            "contact_number",
            "title",
            "description",
            "price",
            "province",
            "district",
            "address",
            "sub_address",
            "location_url",
            "has_electricity",
            "has_wifi",
            "has_water_supply",
            "has_parking",
            "is_available",
            "photos",
            "room_images",
            "rating",
            "pets_allowed",
            "smoking_allowed",
            "curfew_time",
        ]
        read_only_fields = ["id", "owner_email", "contact_number"]

    def update(self, instance, validated_data):
        # Handle room images update
        room_images_data = self.context["request"].FILES.getlist("room_images")
        if room_images_data:
            RoomImage.objects.filter(room=instance).delete()  # Clear existing images
            for image_data in room_images_data:
                RoomImage.objects.create(room=instance, image=image_data)

        # Update other fields
        instance = super().update(instance, validated_data)
        return instance

    def validate_price(self, value):
        """Ensure the price is positive."""
        if value <= 0:
            raise serializers.ValidationError("The price must be a positive number.")
        return value

    def validate_location_url(self, value):
        """Ensure location URL starts with 'http' or 'https'."""
        if value and not (value.startswith("http://") or value.startswith("https://")):
            raise serializers.ValidationError(
                "Location URL must start with 'http://' or 'https://'."
            )
        return value


class DepositSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deposit
        fields = [
            "id",
            "leasee",
            "landlord",
            "room",
            "amount",
            "payment_status",
            "deposit_date",
        ]
        read_only_fields = ["id", "deposit_date"]

    def validate(self, data):
        leasee = data.get("leasee")
        landlord = data.get("landlord")
        room = data.get("room")

        if room.has_deposit(leasee=leasee, landlord=landlord):
            raise serializers.ValidationError("Deposit already exists")

        return data


class ContactFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactForm
        fields = ["id", "name", "email", "subject", "message", "status", "created_at"]
        read_only_fields = [
            "status",
            "created_at",
        ]  # Status and creation date are read-only

    # Optionally add custom validation for the subject if needed
    def validate_subject(self, value):
        if value not in dict(ContactForm.SUBJECT_CHOICES):
            raise serializers.ValidationError("Invalid subject choice")
        return value
