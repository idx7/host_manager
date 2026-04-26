try:
    from celery import shared_task
except ModuleNotFoundError:
    def shared_task(func=None, **_kwargs):
        if func is None:
            return lambda real_func: real_func
        return func

from .services import create_stats, rotate_passwords


@shared_task
def rotate_host_passwords():
    return rotate_passwords()


@shared_task
def count_hosts_by_city_and_room():
    return create_stats()