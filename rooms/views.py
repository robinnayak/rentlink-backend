from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import CustomUser,Leasee,Landlord,Room,Deposit,VisitRequest, Notification,ContactForm,RoomImage
from .serializers import CustomUserSerializer, CustomUserCreateSerializer,LoginSerializer,LeaseeSerializer,LandlordSerializer,RoomSerializer,DepositSerializer, ContactFormSerializer,RoomImageSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from decimal import Decimal
from django.db.models import Q
from django.contrib.auth import login, logout, authenticate
from django_filters.rest_framework import DjangoFilterBackend
from rooms.filters import RoomFilter
from rest_framework.parsers import MultiPartParser, FormParser
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
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            user = CustomUserSerializer(user).data
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user' :user
                
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            logout(request)
            return Response({
                'message': 'User logged out successfully',
                'user': user.email
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
  
class LandlordListView(APIView):
    def get(self, request):
        landlords = Landlord.objects.all()
        serializer = LandlordSerializer(landlords, many=True)
        return Response(serializer.data)

    # def post(self, request):
    #     serializer = LandlordSerializer(data=request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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

    # def post(self, request):
    #     serializer = LeaseeSerializer(data=request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
    def get(self, request, *args, **kwargs):
        """
        List all available rooms.
        Only show the location URL if:
        1. The user is the room's landlord (room owner).
        2. The user is a leasee and has made a deposit for that room.
        """
        rooms = Room.objects.filter(is_available=True)  # Listing only available rooms
        serializer = RoomSerializer(rooms, many=True)
        data = serializer.data

        if request.user.is_authenticated:
            # Check if the user is a leasee
            if hasattr(request.user, 'leasee_profile'):
                leasee = request.user.leasee_profile
                for room_data, room_obj in zip(data, rooms):
                    if not room_obj.has_deposit(leasee):
                        # Hide the location URL if the leasee has not made a deposit
                        room_data['location_url'] = "Deposit required to view location URL."
            
            # Check if the user is a landlord
            elif hasattr(request.user, 'landlord_profile'):
                landlord = request.user.landlord_profile
                for room_data, room_obj in zip(data, rooms):
                    # If the landlord is not the owner of the room, hide the location URL
                    if room_obj.rent_giver != landlord:
                        room_data['location_url'] = "You do not own this room, location hidden."
        else:
            # For unauthenticated users, hide the location URL
            for room in data:
                room['location_url'] = "Deposit required to view location URL."

        return Response(data, status=status.HTTP_200_OK)
    

class RoomGetDetailView(APIView):
    def get(self, request, pk, *args, **kwargs):
        """
        Retrieve detailed information about a specific room.
        Only show the location URL if:
        1. The user is the room's landlord (room owner).
        2. The user is a leasee and has made a deposit for that room.
        """
        room = get_object_or_404(Room, pk=pk)
        serializer = RoomSerializer(room)
        data = serializer.data

        if request.user.is_authenticated:
            # Check if the user is a leasee
            if hasattr(request.user, 'leasee_profile'):
                leasee = request.user.leasee_profile
                if not room.has_deposit(leasee):
                    # Hide the location URL if the leasee has not made a deposit
                    data['location_url'] = "Deposit required to view location URL."
            
            # Check if the user is a landlord
            elif hasattr(request.user, 'landlord_profile'):
                landlord = request.user.landlord_profile
                if room.rent_giver != landlord:
                    # If the landlord is not the owner of the room, hide the location URL
                    data['location_url'] = "You do not own this room, location hidden."
        else:
            # For unauthenticated users, hide the location URL
            data['location_url'] = "Authentication required before Deposit required to view location URL."

        return Response(data, status=status.HTTP_200_OK)

class RoomAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # To handle file uploads

    def get(self, request, *args, **kwargs):
        """
        List all rooms related to the authenticated user as a landlord, regardless of availability.
        """
        if hasattr(request.user, 'landlord_profile'):
            rooms = Room.objects.filter(rent_giver=request.user.landlord_profile)
        else:
            return Response({"detail": "Landlord profile not found."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = RoomSerializer(rooms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """
        Create a new room with the option to upload a single main photo and multiple additional images.
        """
        if hasattr(request.user, 'landlord_profile'):
            landlord = request.user.landlord_profile
            data = request.data.copy()

            # Serialize room data
            serializer = RoomSerializer(data=data)
            
            if serializer.is_valid():
                room = serializer.save(rent_giver=landlord)

                # Handling the single room photo (from 'photos')
                if 'photos' in request.FILES:
                    room.photos = request.FILES['photos']
                    room.save()

                # Handling the multiple room images (from 'room_images')
                images = request.FILES.getlist('room_images')
                if images:
                    for image in images:
                        RoomImage.objects.create(room=room, image=image)

                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"detail": "Only landlords can create rooms."}, status=status.HTTP_403_FORBIDDEN)

# Room Detail, Update, and Delete View
class RoomDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, *args, **kwargs):
        """
        Retrieve the details of a specific room.
        """
        room = get_object_or_404(Room, pk=pk)
        serializer = RoomSerializer(room)
        
        if hasattr(request.user, 'leasee_profile'):
            leasee = request.user.leasee_profile
            if not room.has_deposit(leasee):
                # If the leasee has not made a deposit, hide the location_url
                data = serializer.data
                data['location_url'] = "Deposit required to view location URL."
                return Response(data, status=status.HTTP_200_OK)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk, *args, **kwargs):
        """
        Update an existing room. Ensure only the landlord who created the room can update it.
        """
        room = get_object_or_404(Room, pk=pk)

        # Check if the user is a landlord
        if not hasattr(request.user, 'landlord_profile'):
            return Response({"detail": "Only landlords can update rooms."}, status=status.HTTP_403_FORBIDDEN)

        # Ensure the user is the rent giver (landlord) who created the room
        if room.rent_giver.user != request.user:
            return Response({"detail": "You do not have permission to update this room."}, status=status.HTTP_403_FORBIDDEN)

        # Validate and update room data using RoomSerializer
        room_serializer = RoomSerializer(room, data=request.data, partial=True, context={'request': request})  # Allow partial updates
        if room_serializer.is_valid():
            room = room_serializer.save()

            # # Handling the single room photo (from 'photos')
            # if 'photos' in request.FILES:
            #     room.photos = request.FILES['photos']
            #     room.save()

            # # Handling multiple room images (from 'room_images') using RoomImageSerializer
            # images_data = request.FILES.getlist('room_images')
            # if images_data:
            #     for image in images_data:
            #         # Create a new RoomImage for each new image file
            #         image_data = {'room': room.id, 'image': image}
            #         image_serializer = RoomImageSerializer(data=image_data, partial=True)
            #         if image_serializer.is_valid():
            #             image_serializer.save()
            #         else:
            #             return Response(image_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Return the updated room data
            return Response(room_serializer.data, status=status.HTTP_200_OK)

        # Return validation errors if any
        return Response(room_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, *args, **kwargs):
        """
        Delete an existing room. Ensure only the landlord who created the room can delete it.
        """
        room = get_object_or_404(Room, pk=pk)

        # Check if the user is a landlord
        if not hasattr(request.user, 'landlord_profile'):
            return Response({"detail": "Only landlords can delete rooms."}, status=status.HTTP_403_FORBIDDEN)

        # Ensure the user is the rent giver (landlord) who created the room
        if room.rent_giver.user != request.user:
            return Response({"detail": "You do not have permission to delete this room."}, status=status.HTTP_403_FORBIDDEN)

        room.delete()
        return Response({"detail": "Room deleted successfully."}, status=status.HTTP_200_OK)

class DepositAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Create a deposit for a room. Assume a payment is made externally and its status is updated accordingly.
        """
        room = get_object_or_404(Room, pk=request.data.get('room_id'))
        if hasattr(request.user, 'leasee_profile'):
            leasee = request.user.leasee_profile

            # Check if a deposit already exists for this room by this leasee
            deposit, created = Deposit.objects.get_or_create(
                leasee=leasee, 
                room=room, 
                # defaults={'amount': room.price * Decimal('0.1')}  # Example: deposit is 10% of room price
                defaults={'amount': Decimal('20')}  # Example: deposit is 10% of room price
            )
            
            if not created and deposit.is_paid():
                return Response({"detail": "Deposit already paid."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Handle deposit payment (external payment integration would go here)
            # Assuming the deposit is successfully paid externally
            deposit.payment_status = 'paid'
            deposit.save()

            return Response({"detail": "Deposit successful."}, status=status.HTTP_201_CREATED)

        return Response({"detail": "Leasee profile not found."}, status=status.HTTP_403_FORBIDDEN)

class ConfirmVisitRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, visit_request_id):
        visit_request = get_object_or_404(VisitRequest, id=visit_request_id, room__rent_giver__user=request.user)
        
        visit_request.confirm()
        
        return Response({"detail": "Visit request confirmed."}, status=status.HTTP_200_OK)

class VisitRequestListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get all visit requests for the current landlord
        landlord = request.user.landlord_profile
        visit_requests = VisitRequest.objects.filter(room__rent_giver=landlord).order_by('-request_date')
        
        data = [
            {
                'leasee': f"{visit.leasee.user.first_name} {visit.leasee.user.last_name}",
                'room': visit.room.title,
                'status': visit.status,
                'request_date': visit.request_date
            }
            for visit in visit_requests
        ]
        
        return Response(data, status=status.HTTP_200_OK)

# Leasee can create visit requests
class CreateVisitRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        leasee = get_object_or_404(Leasee, user=request.user)
        room_id = request.data.get('room_id')

        room = get_object_or_404(Room, id=room_id)

        # Check if the leasee already has a pending or confirmed request
        existing_request = VisitRequest.objects.filter(
            leasee=leasee, room=room, status__in=['pending', 'confirmed']
        ).exists()
        
        if existing_request:
            return Response(
                {"error": "You already have a pending or confirmed visit request for this room."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create the visit request
        visit_request = VisitRequest.objects.create(leasee=leasee, room=room)
        return Response({"detail": "Visit request created successfully."}, status=status.HTTP_201_CREATED)

# Only the landlord can confirm visit requests
class ConfirmVisitRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, visit_request_id):
        # Ensure the current user is a landlord
        landlord = get_object_or_404(Landlord, user=request.user)

        # Get the visit request, ensuring it's for the current landlord's room
        visit_request = get_object_or_404(VisitRequest, id=visit_request_id, room__rent_giver=landlord)

        # Confirm the visit request
        visit_request.confirm()
        return Response({"detail": "Visit request confirmed."}, status=status.HTTP_200_OK)

# Only the landlord can cancel visit requests
class CancelVisitRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, visit_request_id):
        # Ensure the current user is a landlord
        landlord = get_object_or_404(Landlord, user=request.user)

        # Get the visit request, ensuring it's for the current landlord's room
        visit_request = get_object_or_404(VisitRequest, id=visit_request_id, room__rent_giver=landlord)

        # Cancel the visit request
        visit_request.cancel()
        return Response({"detail": "Visit request cancelled."}, status=status.HTTP_200_OK)

class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = request.user.notifications.all().order_by('-created_at')
        notification_data = [
            {
                'id': notification.id,
                'message': notification.message,
                'is_read': notification.is_read,
                'created_at': notification.created_at
            }
            for notification in notifications
        ]
        return Response(notification_data, status=status.HTTP_200_OK)

class MarkNotificationAsReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, notification_id):
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.mark_as_read()
        return Response({"detail": "Notification marked as read."}, status=status.HTTP_200_OK)


class RoomFilterView(APIView):
    def get(self, request, *args, **kwargs):
        queryset = Room.objects.all()

        # Apply filters using RoomFilter
        filter_backends = DjangoFilterBackend()
        filterset = RoomFilter(request.query_params, queryset=queryset)
        
        if filterset.is_valid():
            queryset = filterset.qs
        
        # Apply ordering
        ordering = request.query_params.get('ordering', None)
        if ordering:
            if ordering in ['price', '-price', 'rating', '-rating']:
                queryset = queryset.order_by(ordering)

        # Pagination
        page = request.query_params.get('page', 1)
        page_size = request.query_params.get('page_size', 10)
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