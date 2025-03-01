import os
from typing import Any, Dict

import grpc

from business.business_pb2_grpc import BusinessModuleStub
from cf.cf_pb2_grpc import CFModuleStub
from gis.gis_pb2_grpc import GISModuleStub
from market.market_pb2_grpc import MarketModuleStub
from reports.reporter import Reporter
from teo.teo_pb2_grpc import TEOModuleStub


class BaseSimulation:

    def __init__(self, initial_data: Dict[str, Any], simulation_session: str):
        self.initial_data = initial_data
        self.simulation_session = simulation_session
        self.__stub_factory()

    def __stub_factory(self):
        self.reporter = Reporter(self.simulation_session)
        self.river_data = {}

        self.cf_channel = grpc.insecure_channel(f"{os.getenv('CF_HOST')}:{os.getenv('CF_PORT')}")
        self.cf = CFModuleStub(self.cf_channel)

        self.gis_channel = grpc.insecure_channel(f"{os.getenv('GIS_HOST')}:{os.getenv('GIS_PORT')}")
        self.gis = GISModuleStub(self.gis_channel)

        self.teo_channel = grpc.insecure_channel(f"{os.getenv('TEO_HOST')}:{os.getenv('TEO_PORT')}")
        self.teo = TEOModuleStub(self.teo_channel)

        self.market_channel = grpc.insecure_channel(f"{os.getenv('MM_HOST')}:{os.getenv('MM_PORT')}")
        self.market = MarketModuleStub(self.market_channel)

        self.business_channel = grpc.insecure_channel(f"{os.getenv('BM_HOST')}:{os.getenv('BM_PORT')}")
        self.business = BusinessModuleStub(self.business_channel)

    def run(self):
        self.simulation_started()
        self._run()
        self.simulation_finished()

    def _run(self):
        self.reporter.save_step_error("NOT-DEFINED", "NOT-DEFINED", {},
                                      {"message": "Simulation Metadata is Not Defined!"})

    def safe_run_step(self, module, function, step):
        try:
            step()
            return True
        except grpc.RpcError as rpc_error:
            if rpc_error.code() == grpc.StatusCode.CANCELLED:
                self.reporter.save_step_error(
                    module=module,
                    function=function,
                    input_data={},
                    errors={"message": "Request has been Cancelled"}
                )
            elif rpc_error.code() == grpc.StatusCode.UNAVAILABLE:
                self.reporter.save_step_error(
                    module=module,
                    function=function,
                    input_data={},
                    errors={"message": "Service is not available"}
                )
            elif rpc_error.code() == grpc.StatusCode.UNKNOWN:
                self.reporter.save_step_error(
                    module=module,
                    function=function,
                    input_data={},
                    errors={"message": rpc_error.details()}
                )
            return False
        except Exception as e:
            self.reporter.save_step_error(
                module=module,
                function=function,
                input_data={},
                errors={"message": str(e)}
            )
            return False

    def simulation_started(self):
        self.reporter.save_step_report("SIMULATOR", "SIMULATION STARTED", {}, {})

    def simulation_finished(self):
        self.reporter.save_step_report("SIMULATOR", "SIMULATION FINISHED", {}, {})
