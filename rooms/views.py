from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import (
    CustomUser,
    Leasee,
    Landlord,
    Room,
    Deposit,
    VisitRequest,
    Notification,
    ContactForm,
    RoomImage,
)
from .serializers import (
    CustomUserSerializer,
    CustomUserCreateSerializer,
    LoginSerializer,
    LeaseeSerializer,
    LandlordSerializer,
    RoomSerializer,
    DepositSerializer,
    ContactFormSerializer,
    RoomImageSerializer,
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from decimal import Decimal
from django.db.models import Q
from django.contrib.auth import login, logout, authenticate
from django_filters.rest_framework import DjangoFilterBackend
from rooms.filters import RoomFilter
from rest_framework.parsers import MultiPartParser, FormParser
from .renderer import UserRenderer
from rest_framework.exceptions import UnsupportedMediaType


class UserListView(APIView):
    def get(self, request):
        users = CustomUser.objects.all()
        serializer = CustomUserSerializer(users, many=True)
        return Response(serializer.data)

    def post(self, request):
        with transaction.atomic():
            serializer = CustomUserCreateSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDetailView(APIView):
    def get(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk)
        serializer = CustomUserSerializer(user)
        return Response(serializer.data)

    def put(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk)
        serializer = CustomUserCreateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk)
        user.delete()
        return Response(status=status.HTTP_200_OK)


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            refresh = RefreshToken.for_user(user)
            user = CustomUserSerializer(user).data
            return Response(
                {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "user": user,
                }
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            logout(request)
            return Response(
                {"message": "User logged out successfully", "user": user.email},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class LandlordListView(APIView):
    def get(self, request):
        landlords = Landlord.objects.all()
        serializer = LandlordSerializer(landlords, many=True)
        return Response(serializer.data)


class LandlordDetailView(APIView):
    def get(self, request, pk):
        landlord = get_object_or_404(Landlord, pk=pk)
        serializer = LandlordSerializer(landlord)
        return Response(serializer.data)

    def put(self, request, pk):
        landlord = get_object_or_404(Landlord, pk=pk)
        serializer = LandlordSerializer(landlord, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        landlord = get_object_or_404(Landlord, pk=pk)
        landlord.delete()
        return Response(status=status.HTTP_200_OK)


class LeaseeListView(APIView):
    def get(self, request):
        leasees = Leasee.objects.all()
        serializer = LeaseeSerializer(leasees, many=True)
        return Response(serializer.data)


class LeaseeDetailView(APIView):
    def get(self, request, pk):
        leasee = get_object_or_404(Leasee, pk=pk)
        serializer = LeaseeSerializer(leasee)
        return Response(serializer.data)

    def put(self, request, pk):
        leasee = get_object_or_404(Leasee, pk=pk)
        serializer = LeaseeSerializer(leasee, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        leasee = get_object_or_404(Leasee, pk=pk)
        leasee.delete()
        return Response(status=status.HTTP_200_OK)


# Room List and Create View
class RoomGetAPIView(APIView):
    renderer_classes = [UserRenderer]

    def get(self, request):
        try:
            # Fetch all rooms
            rooms = Room.objects.filter(
                is_available=True
            )  # Listing only available rooms
            serializer = RoomSerializer(rooms, many=True)
            data = serializer.data

            if request.user.is_authenticated:
                # For Leasee users
                if hasattr(request.user, "leasee_profile"):
                    leasee = request.user.leasee_profile
                    for room_data, room_obj in zip(data, rooms):
                        if not room_obj.has_deposit(leasee=leasee):
                            room_data["location_url"] = (
                                "Deposit required to view location on map directly"
                            )

                # For Landlord users
                elif hasattr(request.user, "landlord_profile"):
                    landlord = (
                        request.user.landlord_profile
                    )  # Ensure this is a Landlord instance
                    for room_data, room_obj in zip(data, rooms):
                        if room_obj.rent_giver != landlord:
                            if not room_obj.has_deposit(landlord=landlord):
                                room_data["location_url"] = (
                                    "Deposit required to view location on map directly"
                                )
            else:
                # If the user is not authenticated
                for room_data in data:
                    room_data["location_url"] = (
                        "Login required to view location on map directly"
                    )

            return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"message": str(e), "error": "Something went wrong"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class RoomGetDetailView(APIView):
    def get(self, request, pk, *args, **kwargs):

        room = get_object_or_404(Room, pk=pk)
        try:
            serialzer = RoomSerializer(room)
            data = serialzer.data
            if request.user.is_authenticated:

                if hasattr(request.user, "leasee_profile"):
                    leasee = request.user.leasee_profile
                    if not room.has_deposit(leasee=leasee):
                        data["location_url"] = (
                            "Deposit required to view the Locaion on map directly."
                        )

                elif hasattr(request.user, "landlord_profile"):
                    landlord = request.user.landlord_profile
                    if room.rent_giver != landlord:
                        if not room.has_deposit(landlord=landlord):

                            data["location_url"] = (
                                "Deposit required to view the Locaion on map directly."
                            )
            else:
                # For unathenticated users, hide the location URL
                data["location_url"] = (
                    "You don't have access to this room. Location is hidden. Please log in to continue."
                )
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"message": str(e), "error": "Something went wrong"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class RoomAPIView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # To handle file uploads

    def get(self, request, *args, **kwargs):
        """
        List all rooms related to the authenticated user as a landlord, regardless of availability.
        """
        if hasattr(request.user, "landlord_profile"):
            rooms = Room.objects.filter(rent_giver=request.user.landlord_profile)
        else:
            return Response(
                {"detail": "Landlord profile not found."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = RoomSerializer(rooms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):

        if hasattr(request.user, "landlord_profile"):
            landlord = request.user.landlord_profile
            if not landlord:
                return Response(
                    {"message": "Landlord profile not found"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = RoomSerializer(data=request.data)

            if serializer.is_valid():
                room = serializer.save(rent_giver=landlord)

                if "photos" in request.FILES:
                    room.photos = request.FILES["photos"]
                    room.save()

                images = request.FILES.getlist("room_images")
                if images:
                    for image in images:
                        RoomImage.objects.create(room=room, image=image)

                return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {"message": "You are not athenticated as landlord"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = request.data
        serializer = RoomSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Room Detail, Update, and Delete View
class RoomDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [UserRenderer]
    # parser_classes = [MultiPartParser, FormParser]

    def get(self, request, pk, *args, **kwargs):

        room = get_object_or_404(Room, pk=pk)
        try:
            serialzer = RoomSerializer(room)
            data = serialzer.data
            if hasattr(request.user, "leasee_profile"):
                leasee = request.user.leasee_profile
                if not room.has_deposit(leasee=leasee):
                    data["location_url"] = (
                        "Deposit required to view the Locaion on map directly."
                    )

            elif hasattr(request.user, "landlord_profile"):
                landlord = request.user.landlord_profile
                if room.rent_giver != landlord:
                    if not room.has_deposit(landlord=landlord):

                        data["location_url"] = (
                            "Deposit required to view the Locaion on map directly."
                        )
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"message": str(e), "error": "Something went wrong"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def put(self, request, pk, *args, **kwargs):
        room = get_object_or_404(Room, pk=pk)
        try:
            # Ensure that the authenticated user is the rent_giver of the room
            if not request.user.landlord_profile == room.rent_giver:
                return Response(
                    {"message": "You are not authorized to edit this room"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            data = request.data
            serializer = RoomSerializer(
                room, data=data, partial=True, context={"request": request}
            )

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {"message": str(e), "error": "Something went wrong"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def delete(self, request, pk, *args, **kwargs):
        room = get_object_or_404(Room, pk=pk)
        try:
            if not request.user.landlord_profile == room.rent_giver:
                return Response(
                    {"message": "You are not authorized to delete this room"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            room.delete()
            return Response(
                {"message": "Room deleted successfully"},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"message": str(e), "error": "Something went wrong"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class DepositAPIView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [UserRenderer]

    def post(self, request, *args, **kwargs):
        room = get_object_or_404(Room, pk=request.data.get("room_id"))

        # Determine if the user is a leasee or a landlord
        if hasattr(request.user, "leasee_profile"):
            profile = request.user.leasee_profile
            user_type = "leasee"
        elif (
            hasattr(request.user, "landlord_profile")
            and request.user.landlord_profile != room.rent_giver
        ):
            profile = request.user.landlord_profile
            user_type = "landlord"
        else:
            return Response(
                {"detail": "You are not authorized to make a deposit."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get or create the deposit instance
        deposit, created = Deposit.objects.get_or_create(
            **{user_type: profile, "room": room}, defaults={"amount": Decimal("20")}
        )

        # Check if the deposit has already been paid
        if not created and deposit.is_paid():
            return Response(
                {"detail": "Deposit already paid."}, status=status.HTTP_200_OK
            )

        # Mark the deposit as paid
        deposit.payment_status = "paid"
        deposit.save()

        return Response(
            {"detail": "Deposit successful."}, status=status.HTTP_201_CREATED
        )


class ConfirmVisitRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, visit_request_id):
        visit_request = get_object_or_404(
            VisitRequest, id=visit_request_id, room__rent_giver__user=request.user
        )

        visit_request.confirm()

        return Response(
            {"detail": "Visit request confirmed."}, status=status.HTTP_200_OK
        )


class VisitRequestListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get all visit requests for the current landlord
        landlord = request.user.landlord_profile
        visit_requests = VisitRequest.objects.filter(
            room__rent_giver=landlord
        ).order_by("-request_date")

        data = [
            {
                "leasee": f"{visit.leasee.user.first_name} {visit.leasee.user.last_name}",
                "room": visit.room.title,
                "status": visit.status,
                "request_date": visit.request_date,
            }
            for visit in visit_requests
        ]

        return Response(data, status=status.HTTP_200_OK)


# Leasee can create visit requests
class CreateVisitRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        leasee = get_object_or_404(Leasee, user=request.user)
        room_id = request.data.get("room_id")

        room = get_object_or_404(Room, id=room_id)

        # Check if the leasee already has a pending or confirmed request
        existing_request = VisitRequest.objects.filter(
            leasee=leasee, room=room, status__in=["pending", "confirmed"]
        ).exists()

        if existing_request:
            return Response(
                {
                    "error": "You already have a pending or confirmed visit request for this room."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create the visit request
        visit_request = VisitRequest.objects.create(leasee=leasee, room=room)
        return Response(
            {"detail": "Visit request created successfully."},
            status=status.HTTP_201_CREATED,
        )


# Only the landlord can confirm visit requests
class ConfirmVisitRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, visit_request_id):
        # Ensure the current user is a landlord
        landlord = get_object_or_404(Landlord, user=request.user)

        # Get the visit request, ensuring it's for the current landlord's room
        visit_request = get_object_or_404(
            VisitRequest, id=visit_request_id, room__rent_giver=landlord
        )

        # Confirm the visit request
        visit_request.confirm()
        return Response(
            {"detail": "Visit request confirmed."}, status=status.HTTP_200_OK
        )


# Only the landlord can cancel visit requests
class CancelVisitRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, visit_request_id):
        # Ensure the current user is a landlord
        landlord = get_object_or_404(Landlord, user=request.user)

        # Get the visit request, ensuring it's for the current landlord's room
        visit_request = get_object_or_404(
            VisitRequest, id=visit_request_id, room__rent_giver=landlord
        )

        # Cancel the visit request
        visit_request.cancel()
        return Response(
            {"detail": "Visit request cancelled."}, status=status.HTTP_200_OK
        )


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = request.user.notifications.all().order_by("-created_at")
        notification_data = [
            {
                "id": notification.id,
                "message": notification.message,
                "is_read": notification.is_read,
                "created_at": notification.created_at,
            }
            for notification in notifications
        ]
        return Response(notification_data, status=status.HTTP_200_OK)


class MarkNotificationAsReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, notification_id):
        notification = get_object_or_404(
            Notification, id=notification_id, user=request.user
        )
        notification.mark_as_read()
        return Response(
            {"detail": "Notification marked as read."}, status=status.HTTP_200_OK
        )


class RoomFilterView(APIView):
    def get(self, request, *args, **kwargs):
        queryset = Room.objects.filter(is_available=True)

        # Apply filters using RoomFilter
        filter_backends = DjangoFilterBackend()
        filterset = RoomFilter(request.query_params, queryset=queryset)

        if filterset.is_valid():
            queryset = filterset.qs

        # Apply ordering
        ordering = request.query_params.get("ordering", None)
        if ordering:
            if ordering in ["price", "-price", "rating", "-rating"]:
                queryset = queryset.order_by(ordering)

        # Pagination
        page = request.query_params.get("page", 1)
        page_size = request.query_params.get("page_size", 10)
        start = (int(page) - 1) * int(page_size)
        end = start + int(page_size)
        paginated_queryset = queryset[start:end]

        # Serialize the data
        serializer = RoomSerializer(paginated_queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# API View for handling GET (retrieve all forms) and POST (submit a new form) requests
class ContactFormView(APIView):
    # GET request to retrieve all contact forms
    def get(self, request):
        forms = ContactForm.objects.all()
        serializer = ContactFormSerializer(forms, many=True)
        return Response(serializer.data)

    # POST request to submit a new contact form
    def post(self, request):
        serializer = ContactFormSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()  # Save the new form data
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
