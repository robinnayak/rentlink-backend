from django.urls import path
from .views import (
    UserListView, 
    UserDetailView,
    LoginView,
    LandlordListView,
    LandlordDetailView,
    LeaseeListView,
    LeaseeDetailView,
    RoomAPIView,
    RoomDetailAPIView,
    DepositAPIView,
    CreateVisitRequestView,  # Imported the visit request views
    ConfirmVisitRequestView, 
    CancelVisitRequestView,
    NotificationListView,  # Imported notification views
    MarkNotificationAsReadView,
    RoomGetAPIView,
    RoomGetDetailView,
    LogoutView,
    RoomFilterView,
    ContactFormView,RoomCommentAPIView
)

urlpatterns = [
    path('register/', UserListView.as_view(), name='user-list'),
    path('register/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    path('landlords/', LandlordListView.as_view(), name='landlord-list'),
    path('landlord/', LandlordDetailView.as_view(), name='landlord-detail'),
    path('leasees/', LeaseeListView.as_view(), name='leasee-list'),
    path('leasee/', LeaseeDetailView.as_view(), name='leasee-detail'),
    path('rooms/', RoomAPIView.as_view(), name='room-api'),
    path('rooms/<int:pk>/', RoomDetailAPIView.as_view(), name='room-detail-api'),
    path('deposit/', DepositAPIView.as_view(), name='deposit'),
    
    # Visit Request URLs
    path('visit-request/', CreateVisitRequestView.as_view(), name='create_visit_request'),
    path('visit-request/confirm/<int:visit_request_id>/', ConfirmVisitRequestView.as_view(), name='confirm_visit_request'),
    path('visit-request/cancel/<int:visit_request_id>/', CancelVisitRequestView.as_view(), name='cancel_visit_request'),

    # Notification URLs
    path('notifications/', NotificationListView.as_view(), name='notification_list'),
    path('notifications/read/<int:notification_id>/', MarkNotificationAsReadView.as_view(), name='mark_notification_as_read'),
    
    path('roomsview/',RoomGetAPIView.as_view(),name="rooms-view"),
    path('roomsview/<int:pk>/',RoomGetDetailView.as_view(),name="rooms-detail-view"),

    path('rooms-filter/', RoomFilterView.as_view(), name='room-list'),
    
    path('contact/', ContactFormView.as_view(), name='contact-form'),
    
    path('roomsview/<int:room_id>/comments/',RoomCommentAPIView.as_view(),name='room-comments'),
]

