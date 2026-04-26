from django.db import models


class City(models.Model):
    name = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]
        verbose_name = "city"
        verbose_name_plural = "cities"

    def __str__(self):
        return self.name


class ServerRoom(models.Model):
    name = models.CharField(max_length=64)
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="rooms")
    address = models.CharField(max_length=255, blank=True)
    remark = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]
        unique_together = ("city", "name")

    def __str__(self):
        return f"{self.city.name} - {self.name}"


class Host(models.Model):
    STATUS_CHOICES = (
        ("unknown", "unknown"),
        ("online", "online"),
        ("offline", "offline"),
    )

    hostname = models.CharField(max_length=128)
    ip_address = models.GenericIPAddressField(unique=True)
    city = models.ForeignKey(City, on_delete=models.PROTECT, related_name="hosts")
    server_room = models.ForeignKey(
        ServerRoom,
        on_delete=models.PROTECT,
        related_name="hosts",
    )
    root_password_secret = models.TextField(blank=True)
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default="unknown",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.hostname}({self.ip_address})"


class PasswordChangeLog(models.Model):
    host = models.ForeignKey(Host, on_delete=models.CASCADE, related_name="password_logs")
    password_secret = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"{self.host.hostname} password changed at {self.created_at}"


class HostCountStat(models.Model):
    stat_date = models.DateField()
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    server_room = models.ForeignKey(ServerRoom, on_delete=models.CASCADE)
    host_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-stat_date", "city_id", "server_room_id"]
        unique_together = ("stat_date", "city", "server_room")

    def __str__(self):
        return f"{self.stat_date} {self.city.name}/{self.server_room.name}: {self.host_count}"
