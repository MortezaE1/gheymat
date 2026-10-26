from celery import shared_task

from . import services


@shared_task(ignore_result=True, soft_time_limit=50)
def update_prices():
    return services.update_prices()


@shared_task(ignore_result=True)
def prune_history():
    return services.prune_history()
