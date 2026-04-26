from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("cities/", views.city_list, name="city_list"),
    path("cities/<int:city_id>/", views.city_detail, name="city_detail"),
    path("rooms/", views.room_list, name="room_list"),
    path("rooms/<int:room_id>/", views.room_detail, name="room_detail"),
    path("hosts/", views.host_list, name="host_list"),
    path("hosts/<int:host_id>/", views.host_detail, name="host_detail"),
    path("ping/", views.ping_view, name="ping"),
]