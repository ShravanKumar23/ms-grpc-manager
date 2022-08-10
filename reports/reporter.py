from dataclasses import dataclass
from datetime import datetime
import os
from typing import Any, Dict
from sqlalchemy import create_engine, func, select, insert
from sqlalchemy.orm.session import Session

from reports.db_models import IntegrationReport, SimulationSession
from uuid import uuid4

import logging

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


@dataclass
class Reporter:
    session_uuid: str

    def __post_init__(self):
        db_url = "postgresql+psycopg2://{name}:{password}@{host}:{port}/{db}"
        self.engine = create_engine(url=db_url.format(
            user=os.getenv('PG_USERNAME'),
            password=os.getenv('PG_PASSWORD'),
            host=os.getenv('PG_HOST'),
            port=os.getenv('PG_PORT'),
            db=os.getenv('PG_DATABASE')))
        self.__load_simulation()

    def __load_simulation(self):
        stmt = (
            select(SimulationSession)
            .join(SimulationSession.simulation)
            .where(SimulationSession.simulation_uuid == self.session_uuid)
        )

        with Session(self.engine) as session:
            self.simulation_session: SimulationSession = session.scalars(stmt).one()

    def save_step_report(self, module: str, function: str, input_data: Dict[str, Any], output_data: Dict[str, Any]):
        stmt = insert(IntegrationReport).values(
            simulation_id=self.simulation_session.simulation_id,
            simulation_uuid=self.simulation_session.simulation_uuid,
            data=input_data,
            output=output_data,
            type="simulation",
            module=module,
            function=function,
            step_uuid=str(uuid4()),
            created_at=datetime.now()

        )

        with self.engine.connect() as connection:
            with connection.begin():
                connection.execute(stmt)

    def save_step_error(self, module: str, function: str, input_data: Dict[str, Any], errors: Dict[str, Any]):
        stmt = insert(IntegrationReport).values(
            simulation_id=self.simulation_session.simulation_id,
            simulation_uuid=self.simulation_session.simulation_uuid,
            data=input_data,
            output={},
            errors=errors,
            type="simulation",
            module=module,
            function=function,
            step_uuid=str(uuid4()),
            created_at=datetime.now()

        )

        with self.engine.connect() as connection:
            with connection.begin():
                connection.execute(stmt)
