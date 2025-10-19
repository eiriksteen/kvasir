import uuid
from typing import List
from project_server.client import ProjectClient
from synesis_schemas.main_server import BasePlot, PlotCreate, PlotUpdate


async def create_plot(client: ProjectClient, plot_create: PlotCreate) -> BasePlot:
    response = await client.send_request("post", "/analysis/plot", json=plot_create.model_dump(mode="json"))
    return BasePlot(**response.body)


async def get_plot(client: ProjectClient, plot_id: uuid.UUID) -> BasePlot:
    response = await client.send_request("get", f"/analysis/plot/{plot_id}")
    return BasePlot(**response.body)


async def get_plots_by_analysis_result(client: ProjectClient, analysis_result_id: uuid.UUID) -> List[BasePlot]:
    response = await client.send_request("get", f"/analysis/plot/analysis-result/{analysis_result_id}")
    return [BasePlot(**plot) for plot in response.body]


async def update_plot(client: ProjectClient, plot_id: uuid.UUID, plot_update: PlotUpdate) -> BasePlot:
    response = await client.send_request("put", f"/analysis/plot/{plot_id}", json=plot_update.model_dump(mode="json"))
    return BasePlot(**response.body)


async def delete_plot(client: ProjectClient, plot_id: uuid.UUID) -> None:
    await client.send_request("delete", f"/analysis/plot/{plot_id}")
