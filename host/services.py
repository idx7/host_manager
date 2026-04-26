import ipaddress
import secrets
import string
import subprocess

from django.core import signing
from django.db.models import Count
from django.utils import timezone

from .models import Host, HostCountStat, PasswordChangeLog


def make_password(length=16):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(chars) for _ in range(length))


def encrypt_password(raw_password):
    return signing.dumps({"password": raw_password}, salt="host-root-password")


def rotate_passwords():
    count = 0

    for host in Host.objects.all():
        new_password = make_password()
        password_secret = encrypt_password(new_password)
        host.root_password_secret = password_secret
        host.save(update_fields=["root_password_secret", "updated_at"])
        PasswordChangeLog.objects.create(
            host=host,
            password_secret=password_secret,
        )
        count += 1

    return count


def create_stats(stat_date=None):
    stat_date = stat_date or timezone.localdate()
    rows = (
        Host.objects.values("city_id", "server_room_id")
        .annotate(total=Count("id"))
        .order_by("city_id", "server_room_id")
    )

    count = 0
    for row in rows:
        HostCountStat.objects.update_or_create(
            stat_date=stat_date,
            city_id=row["city_id"],
            server_room_id=row["server_room_id"],
            defaults={"host_count": row["total"]},
        )
        count += 1

    return count


def ping_ip(ip_address):
    try:
        ipaddress.ip_address(ip_address)
    except ValueError:
        return False
    
    args = ["ping", "-n", "1", "-w", "1000", ip_address]

    try:
        result = subprocess.run(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False

    return result.returncode == 0
