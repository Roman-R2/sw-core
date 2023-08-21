import uuid
from datetime import datetime
from typing import List

from sqlalchemy import MetaData, Table, Column, Date, Integer, String, TIMESTAMP, ForeignKey, PrimaryKeyConstraint, \
    ForeignKeyConstraint, BIGINT, VARCHAR, BigInteger, BOOLEAN, Boolean, UniqueConstraint, Text, DOUBLE_PRECISION, \
    SMALLINT, SmallInteger, DateTime, func, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, relationship

#
# # metadata = MetaData()
# # Таблица для хранения отслеживаемых ресурсов
# sw_core_resources = Table(
#     'sw_core_resources',
#     metadata,
#     Column('id', BigInteger, primary_key=True, index=True),
#     Column('name', VARCHAR(length=250), nullable=False),
#     Column('description', VARCHAR(length=250), nullable=True),
#     Column('host', VARCHAR(length=100), nullable=False),
#     Column('port', Integer, nullable=False),
#     Column('is_active', Boolean, nullable=False, default=True),
# )
# # Таблица для хранения данных отслеживания доступности ресурсов
# sw_core_resource_availability_statistics = Table(
#     'sw_core_resource_availability_statistics',
#     metadata,
#     Column('id', BigInteger, primary_key=True, index=True),
#     Column('created_at', DateTime(timezone=True), server_default=func.now()),
#     Column('updated_at', DateTime(timezone=True), onupdate=func.now()),
#     Column('is_available', Boolean, default=False),
#     Column("resource", Integer, ForeignKey("sw_core_resources.id")),
# )

Base = declarative_base()


class SwCoreResources(Base):
    """ Таблица для хранения отслеживаемых ресурсов. """
    __tablename__ = 'sw_core_resources'

    id: Mapped[UUID] = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment='Идентификатор uuid')
    name: Mapped[str] = Column(String(length=250), nullable=False, unique=True, comment='Имя ресурса')
    description: Mapped[str] = Column(String(length=250), nullable=True, comment='Описание ресурса')
    host: Mapped[str] = Column(String(length=100), nullable=False, comment='Хост ресурса')
    port: Mapped[int] = Column(Integer, nullable=False, comment='Имя ресурса')
    is_active: Mapped[datetime] = Column(Boolean, nullable=False, default=True, comment='Активный для отслеживания')


class SwCoreResourceAvailabilityStatistics(Base):
    """ Таблица для хранения данных отслеживания доступности ресурсов. """
    __tablename__ = 'sw_core_resource_availability_statistics'

    id: Mapped[UUID] = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = Column(DateTime(timezone=True), server_onupdate=func.now())
    is_available: Mapped[datetime] = Column(Boolean, default=False)
    resource = Column("resource", UUID, ForeignKey("sw_core_resources.id"))


class SwCoreResourceAvailabilityStatisticsTestStorage(Base):
    """ ВРЕМЕННАЯ ДЛЯ ТЕСТОВ Таблица для хранения данных отслеживания доступности ресурсов. """
    __tablename__ = 'sw_core_resource_availability_statistics_test_storage'

    id: Mapped[UUID] = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = Column(DateTime(timezone=True), server_onupdate=func.now())
    is_available: Mapped[datetime] = Column(Boolean, default=False)
    resource = Column("resource", UUID, ForeignKey("sw_core_resources.id"))


class SwCoreResourceAvailabilityCompare(Base):
    """ Подготовленная таблица из SwCoreResourceAvailabilityStatistics
    для хранения данных отслеживания доступности ресурсов. """
    __tablename__ = 'sw_core_resource_availability_compare'

    id: Mapped[UUID] = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    time_from = Column(DateTime(timezone=True), nullable=False)
    time_to = Column(DateTime(timezone=True), nullable=False)
    is_available: Mapped[datetime] = Column(Boolean, default=False)
    resource = Column("resource", UUID, ForeignKey("sw_core_resources.id"))
