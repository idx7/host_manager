from django.contrib import admin
from .models import City, ServerRoom, Host, PasswordChangeLog, HostCountStat 
# Register your models here.

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at", "updated_at")
    search_fields = ("name",)

@admin.register(ServerRoom)
class ServerRoomAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "city", "address", "remark", "created_at", "updated_at")
    search_fields = ("name", "address")
    list_filter = ("city",)

@admin.register(Host)
class HostAdmin(admin.ModelAdmin):
    list_display = ("id", "hostname", "ip_address", "city", "server_room", "status", "created_at", "updated_at")
    search_fields = ("hostname", "ip_address")
    list_filter = ("city", "server_room", "status")

@admin.register(PasswordChangeLog)
class PasswordChangeLogAdmin(admin.ModelAdmin):
    list_display = ("id", "host", "created_at")
    search_fields = ("host__hostname", "host__ip_address")
    list_filter = ("created_at",)

@admin.register(HostCountStat)
class HostCountStatAdmin(admin.ModelAdmin):
    list_display = ("id", "stat_date", "city", "server_room", "host_count", "created_at")
    list_filter = ("stat_date", "city", "server_room")