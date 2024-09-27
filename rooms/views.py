from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import CustomUser,Leasee,Landlord,Room,Deposit,VisitRequest, Notification
from .serializers import CustomUserSerializer, CustomUserCreateSerializer,LoginSerializer,LeaseeSerializer,LandlordSerializer,RoomSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from decimal import Decimal

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
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
  
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
class RoomAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        List all available rooms.
        """
        rooms = Room.objects.filter(is_available=True)  # Listing only available rooms
        serializer = RoomSerializer(rooms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """
        Create a new room.
        """
        if hasattr(request.user, 'landlord_profile'):
            landlord = request.user.landlord_profile
            data = request.data.copy()  # Copy the data to make modifications
            serializer = RoomSerializer(data=data)
            if serializer.is_valid():
                # Pass the rent_giver explicitly when saving
                serializer.save(rent_giver=landlord)
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

        serializer = RoomSerializer(room, data=request.data, partial=True)  # Allow partial updates
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
                defaults={'amount': room.price * Decimal('0.1')}  # Example: deposit is 10% of room price
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

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Leasee, Room, VisitRequest, Landlord

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
