from django.shortcuts import render
from django.http import HttpResponse

import json

from django.db import IntegrityError
from django.db.models import ProtectedError
from django.core.exceptions import ValidationError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import City, Host, ServerRoom
from .services import encrypt_password, make_password, ping_ip
# Create your views here.

def index(request):
    pass

def read_json(request):
    if not request.body:
        return HttpResponse("No data provided", status=400)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse("Invalid JSON data", status=400)
    
def error(message, status=400):
    return JsonResponse({"error": message}, status=status)

def city_data(city):
    return{
        "id": city.id,
        "name": city.name,
        "created_at": city.created_at.isoformat(),
        "updated_at": city.updated_at.isoformat(),
    }

def room_data(room):
    return{
        "id": room.id,
        "name": room.name,
        "city_id": room.city_id,
        "city_name": room.city.name,
        "address": room.address,
        "remark": room.remark,
        "created_at": room.created_at.isoformat(),
        "updated_at": room.updated_at.isoformat(),
    }

def host_data(host):
    return{
        "id": host.id,
        "hostname": host.hostname,
        "ip_address": host.ip_address,
        "city_id": host.city_id,
        "city_name": host.city.name,
        "server_room_id": host.server_room_id,
        "server_room_name": host.server_room.name,
        "status": host.status,
        "created_at": host.created_at.isoformat(),
        "updated_at": host.updated_at.isoformat(),
    }

@csrf_exempt
@require_http_methods(["GET", "POST"])
def city_list(request):
    if request.method == "GET":
        cities = City.objects.all()
        return JsonResponse({"results": [city_data(city) for city in cities]})

    try:
        data = read_json(request)
    except ValueError as exc:
        return error(str(exc))

    name = (data.get("name") or "").strip()
    if not name:
        return error("name is required")

    try:
        city = City.objects.create(name=name)
    except IntegrityError:
        return error("city already exists")

    return JsonResponse(city_data(city), status=201)


@csrf_exempt
@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
def city_detail(request, city_id):
    city = get_object_or_404(City, id=city_id)

    if request.method == "GET":
        return JsonResponse(city_data(city))

    if request.method == "DELETE":
        try:
            city.delete()
        except ProtectedError:
            return error("city is still used by hosts", status=409)
        return JsonResponse({"deleted": True})

    try:
        data = read_json(request)
    except ValueError as exc:
        return error(str(exc))

    name = (data.get("name") or "").strip()
    if not name:
        return error("name is required")

    city.name = name
    try:
        city.save()
    except IntegrityError:
        return error("city already exists")

    return JsonResponse(city_data(city))


@csrf_exempt
@require_http_methods(["GET", "POST"])
def room_list(request):
    if request.method == "GET":
        rooms = ServerRoom.objects.select_related("city")
        return JsonResponse({"results": [room_data(room) for room in rooms]})

    try:
        data = read_json(request)
    except ValueError as exc:
        return error(str(exc))

    name = (data.get("name") or "").strip()
    city_id = data.get("city_id")
    if not name or not city_id:
        return error("name and city_id are required")

    city = get_object_or_404(City, id=city_id)
    try:
        room = ServerRoom.objects.create(
            name=name,
            city=city,
            address=(data.get("address") or "").strip(),
            remark=(data.get("remark") or "").strip(),
        )
    except IntegrityError:
        return error("server room already exists in this city")

    return JsonResponse(room_data(room), status=201)


@csrf_exempt
@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
def room_detail(request, room_id):
    room = get_object_or_404(ServerRoom.objects.select_related("city"), id=room_id)

    if request.method == "GET":
        return JsonResponse(room_data(room))

    if request.method == "DELETE":
        try:
            room.delete()
        except ProtectedError:
            return error("server room is still used by hosts", status=409)
        return JsonResponse({"deleted": True})

    try:
        data = read_json(request)
    except ValueError as exc:
        return error(str(exc))

    if "city_id" in data:
        room.city = get_object_or_404(City, id=data["city_id"])
    if "name" in data:
        room.name = (data.get("name") or "").strip()
    if "address" in data:
        room.address = (data.get("address") or "").strip()
    if "remark" in data:
        room.remark = (data.get("remark") or "").strip()

    if not room.name:
        return error("name is required")

    try:
        room.save()
    except IntegrityError:
        return error("server room already exists in this city")

    return JsonResponse(room_data(room))


@csrf_exempt
@require_http_methods(["GET", "POST"])
def host_list(request):
    if request.method == "GET":
        hosts = Host.objects.select_related("city", "server_room")
        return JsonResponse({"results": [host_data(host) for host in hosts]})

    try:
        data = read_json(request)
    except ValueError as exc:
        return error(str(exc))

    required = ["hostname", "ip_address", "city_id", "server_room_id"]
    if any(not data.get(name) for name in required):
        return error("hostname, ip_address, city_id and server_room_id are required")

    city = get_object_or_404(City, id=data["city_id"])
    room = get_object_or_404(ServerRoom, id=data["server_room_id"])
    if room.city_id != city.id:
        return error("server room does not belong to this city")

    raw_password = data.get("root_password") or make_password()
    host = Host(
        hostname=(data.get("hostname") or "").strip(),
        ip_address=data["ip_address"],
        city=city,
        server_room=room,
        root_password_secret=encrypt_password(raw_password),
        status=data.get("status") or "unknown",
    )

    try:
        host.full_clean()
        host.save()
    except (ValidationError, IntegrityError) as exc:
        return error(str(exc))

    return JsonResponse(host_data(host), status=201)


@csrf_exempt
@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
def host_detail(request, host_id):
    host = get_object_or_404(
        Host.objects.select_related("city", "server_room"),
        id=host_id,
    )

    if request.method == "GET":
        return JsonResponse(host_data(host))

    if request.method == "DELETE":
        host.delete()
        return JsonResponse({"deleted": True})

    try:
        data = read_json(request)
    except ValueError as exc:
        return error(str(exc))

    if "hostname" in data:
        host.hostname = (data.get("hostname") or "").strip()
    if "ip_address" in data:
        host.ip_address = data["ip_address"]
    if "city_id" in data:
        host.city = get_object_or_404(City, id=data["city_id"])
    if "server_room_id" in data:
        host.server_room = get_object_or_404(ServerRoom, id=data["server_room_id"])
    if "status" in data:
        host.status = data["status"]
    if "root_password" in data:
        host.root_password_secret = encrypt_password(data["root_password"])

    if host.server_room.city_id != host.city_id:
        return error("server room does not belong to this city")

    try:
        host.full_clean()
        host.save()
    except (ValidationError, IntegrityError) as exc:
        return error(str(exc))

    return JsonResponse(host_data(host))


@require_http_methods(["GET"])
def ping_view(request):
    host_id = request.GET.get("host_id")
    ip_address = request.GET.get("ip")
    host = None

    if host_id:
        if not host_id.isdigit():
            return error("host_id must be a number")
        host = get_object_or_404(Host, id=host_id)
        ip_address = host.ip_address

    if not ip_address:
        return error("host_id or ip is required")

    reachable = ping_ip(ip_address)
    if host:
        host.status = "online" if reachable else "offline"
        host.save(update_fields=["status", "updated_at"])

    return JsonResponse({"ip": ip_address, "reachable": reachable})
