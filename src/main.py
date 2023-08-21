import asyncio
import time
from typing import NamedTuple

import schedule
from tcp_latency import latency_point

from app.database import DBAdapter
from app.services.logger import SWCoreLogger
from app.settings import COUNT_OF_AVAILABLE_ATTEMPT
from check_resources.models import SwCoreResourceAvailabilityStatistics, SwCoreResources

LOGGER = SWCoreLogger().get_logger()


class App(NamedTuple):
    id: int
    name: str
    description: str
    host: str
    port: int
    is_active: bool


class AvailableAnswer(NamedTuple):
    app_id: int
    app_name: str
    is_available: bool


# Получит все активные приложения из БД
async def get_active_apps():
    apps = []
    with DBAdapter().get_session() as session:
        query = session.query(SwCoreResources).all()
        for item in query:
            apps.append(App(
                id=item.id,
                name=item.name,
                description=item.description,
                host=item.host,
                port=item.port,
                is_active=item.is_active
            ))
    return apps


async def is_available_resource(points):
    return all(point is not None for point in points)


async def get_measure_latency(app, runs: int = COUNT_OF_AVAILABLE_ATTEMPT):
    points = []
    for item in range(runs):
        points.append(latency_point(host=app.host, port=app.port))

    answer = AvailableAnswer(
        app_id=app.id,
        app_name=app.name,
        is_available=await is_available_resource(points)
    )
    # print(answer)
    return answer


async def main():
    tasks = []
    for item in await get_active_apps():
        tasks.append(asyncio.create_task(get_measure_latency(app=item)))

    with DBAdapter().get_session() as session:

        rows = []
        for item in tasks:
            response = await item
            rows.append(
                SwCoreResourceAvailabilityStatistics(
                    resource=response.app_id,
                    is_available=response.is_available
                )
            )
        session.add_all(rows)
        session.commit()


async def prepare_resource_availability_data():
    await asyncio.sleep(10)
    return 1000


async def main_resource_availability_data():
    prepare_task = asyncio.create_task(prepare_resource_availability_data())
    print(f"{await prepare_task= }")


# Работа по отслеживанию ресурсов
def check_resource_availability():
    message = f"Начинаем проверку доступности ресурсов..."
    LOGGER.info(message)
    print(message)

    asyncio.run(main())


# Работа по отслеживанию ресурсов
def prepare_resource_availability_job():
    message = f"Начинаем обработку данных по ресурсам..."
    LOGGER.info(message)
    print(message)

    asyncio.run(main_resource_availability_data())


if __name__ == "__main__":
    LOGGER.info("---- Старт SW Core ----")
    schedule.every(5).seconds.do(check_resource_availability)
    schedule.every(30).seconds.do(prepare_resource_availability_job)

    while True:
        schedule.run_pending()
        print(f"Schedule jobs={schedule.get_jobs()}")
        time.sleep(2)
