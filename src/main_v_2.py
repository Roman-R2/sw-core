import asyncio
from datetime import datetime, timedelta
from typing import NamedTuple

from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session
from tcp_latency import latency_point

from app import settings
from app.database import DBAdapter
from app.services.app_decorators import error_logger, settings_sleep, log_execution_time
from app.services.common_service import show_raw_sql
from app.services.logger import SWCoreLogger
from check_resources.models import SwCoreResources, SwCoreResourceAvailabilityStatistics, \
    SwCoreResourceAvailabilityCompare, SwCoreResourceAvailabilityStatisticsTestStorage

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


class PreparedAvailableRows(NamedTuple):
    time_from: datetime
    time_to: datetime
    is_available: bool
    resource: int


@error_logger
# Получит все активные приложения из БД
async def get_active_apps():
    try:
        apps = []
        with DBAdapter().get_session() as session:
            query = session.query(SwCoreResources).filter(SwCoreResources.is_active == True)
            for item in query:
                apps.append(App(
                    id=item.id,
                    name=item.name,
                    description=item.description,
                    host=item.host,
                    port=item.port,
                    is_active=item.is_active
                ))
        # print(f"{apps=}")
        return apps
    except Exception as error:
        LOGGER.error(error)


@error_logger
async def is_available_resource(points):
    return all(point is not None for point in points)


@error_logger
async def get_measure_latency(app, runs: int = settings.COUNT_OF_AVAILABLE_ATTEMPT):
    points = []
    for item in range(runs):
        points.append(latency_point(host=app.host, port=app.port))

    answer = AvailableAnswer(
        app_id=app.id,
        app_name=app.name,
        is_available=await is_available_resource(points)
    )
    return answer


# @log_execution_time
@settings_sleep(seconds_for_sleep=settings.FREQUENCY_OF_LAUNCHING_AVAILABILITY_COLLECTION)
@error_logger
async def availability_check_task_func():
    """
    Задача для получения доступности ресурсов и записи результатов в БД
    :return:
    """
    tasks = []
    for item in await get_active_apps():
        tasks.append(asyncio.create_task(get_measure_latency(app=item)))

    with DBAdapter().get_session() as session:
        for mark_task in asyncio.as_completed(tasks):
            response = await mark_task
            row = SwCoreResourceAvailabilityStatistics(
                resource=response.app_id,
                is_available=response.is_available
            )
            row_temp = SwCoreResourceAvailabilityStatisticsTestStorage(
                resource=response.app_id,
                is_available=response.is_available
            )
            session.add(row)
            session.add(row_temp)
        session.commit()
    print(f"{availability_check_task_func.__name__} {settings.FREQUENCY_OF_LAUNCHING_AVAILABILITY_COLLECTION}")


# @log_execution_time
@settings_sleep(seconds_for_sleep=settings.FREQUENCY_OF_LAUNCHING_AVAILABILITY_COMPILE)
@error_logger
async def compile_availability_check_task_func():
    """ Компоновка резудьтатов сбора доступноси ресурсов. """

    # Временной буфер (в секундах), в течении которого не учитываются изменения состояний доступности
    TIME_BUFFER_IN_SECONDS = 60

    # временная отсечка
    time_cutoff = datetime.now()
    # print(time_cutoff)

    with DBAdapter().get_session() as session:
        session: Session = session
        # Получим реорганизованные строки для добавления данных в результирующую таблицу
        for item in await get_active_apps():
            # print(f"{item=}")
            query = session.query(SwCoreResourceAvailabilityStatistics).filter(
                SwCoreResourceAvailabilityStatistics.created_at < time_cutoff,
                SwCoreResourceAvailabilityStatistics.resource == item.id
            ).order_by(SwCoreResourceAvailabilityStatistics.created_at.asc())
            left_time_bound = None
            is_available_mark = None
            previos_data_created_at = None
            previos_is_available_mark = None
            this_prepared_rows = []
            rows_for_delete = []

            for data_row in query:
                # Если начали - то задаем границы
                if left_time_bound is None:
                    left_time_bound = data_row.created_at
                    is_available_mark = data_row.is_available
                else:
                    # Если метка доступности поменялась, то записываем данные
                    # Дата в будещем + 60 секунд и + секунды периодичности из настроек
                    buffer_minute_timedelta = previos_data_created_at + timedelta(
                        seconds=settings.FREQUENCY_OF_LAUNCHING_AVAILABILITY_COLLECTION + TIME_BUFFER_IN_SECONDS)
                    # Если метка поменялась или время от предидущего изменения больше buffer_minute_timedelta промежутка
                    if data_row.is_available != is_available_mark or data_row.created_at > buffer_minute_timedelta:
                        this_prepared_rows.append(
                            PreparedAvailableRows(
                                time_from=left_time_bound,
                                time_to=previos_data_created_at,
                                is_available=is_available_mark,
                                resource=item.id,
                            )
                        )
                        left_time_bound = data_row.created_at
                        is_available_mark = data_row.is_available

                previos_data_created_at = data_row.created_at
                previos_is_available_mark = data_row.is_available
                rows_for_delete.append(data_row)
                # Пометим строку к удалению
                session.delete(data_row)

            # Запишем последние данные
            this_prepared_rows.append(
                PreparedAvailableRows(
                    time_from=left_time_bound,
                    time_to=previos_data_created_at,
                    is_available=previos_is_available_mark,
                    resource=item.id,
                )
            )

            # Получим данные из результирующей таблицы для возможного объединения
            # и изменим в случае выполнения условий из запроса row_from_compare_query
            for prepered_item in this_prepared_rows:
                row_from_compare_query = session.query(SwCoreResourceAvailabilityCompare).filter(
                    SwCoreResourceAvailabilityCompare.resource == prepered_item.resource,
                    SwCoreResourceAvailabilityCompare.is_available == prepered_item.is_available,
                    SwCoreResourceAvailabilityCompare.time_to >= prepered_item.time_from - timedelta(
                        seconds=TIME_BUFFER_IN_SECONDS)
                ).order_by(SwCoreResourceAvailabilityCompare.time_to.desc())
                for row_item in row_from_compare_query:
                    # Если есть выборка, то удалим из подготовленных данных строку
                    this_prepared_rows.remove(prepered_item)
                    # И пометим найденную строку в результирующей таблице на перезапись граничного значения
                    row_item.time_to = prepered_item.time_from
                    # break - гарантируем, что меняем одну запись
                    break

            # Добавим данные в результирующую таблицу, если новые данные вообще были
            if left_time_bound is not None:
                alchemy_this_prepared_rows = [
                    SwCoreResourceAvailabilityCompare(
                        time_from=row.time_from,
                        time_to=row.time_to,
                        is_available=row.is_available,
                        resource=row.resource
                    )
                    for row in this_prepared_rows
                ]
                session.add_all(alchemy_this_prepared_rows)
                #
                # Принять удаление обработанных строк из исходной таблицы
                session.commit()

    # LOGGER.info("Компоновка резудьтатов сбора доступноси ресурсов завершена")
    print(f"{compile_availability_check_task_func.__name__} {settings.FREQUENCY_OF_LAUNCHING_AVAILABILITY_COMPILE}")


@error_logger
async def app():
    # Задача по проверке доступности ресурсов
    availability_check_task = None
    # Задача по компоновке резудьтатов сбора доступноси ресурсов
    compile_availability_check_task = None

    while True:
        # Обработка задачи на проверку доступности ресурсов
        if availability_check_task is None:
            availability_check_task = asyncio.ensure_future(availability_check_task_func())
        elif availability_check_task.done():
            availability_check_task.cancel()
            availability_check_task = None

        # Обработка задачи на компановку результатов по проверке доступности ресурсов
        if compile_availability_check_task is None:
            compile_availability_check_task = asyncio.ensure_future(compile_availability_check_task_func())
        elif compile_availability_check_task.done():
            compile_availability_check_task.cancel()
            compile_availability_check_task = None

        # Поспим перед следующей обработкой цикла
        await asyncio.sleep(1)


if __name__ == "__main__":
    mesage = f"Старт программы. " \
             f"(" \
             f"{settings.FREQUENCY_OF_LAUNCHING_AVAILABILITY_COLLECTION=}, " \
             f"{settings.FREQUENCY_OF_LAUNCHING_AVAILABILITY_COMPILE=}" \
             f")"
    print(mesage)
    LOGGER.info(mesage)

    run_app = asyncio.ensure_future(app())
    event_loop = asyncio.get_event_loop()
    event_loop.run_forever()
