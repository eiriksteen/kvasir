import pandas as pd
from io import BytesIO
from uuid import UUID
from typing import Annotated, List, Dict, Any, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from kvasir_api.modules.visualization.service import get_visualization_service
from kvasir_ontology.visualization.data_model import ImageBase, EchartBase, TableBase, ImageCreate, EchartCreate, TableCreate, EChartsOption
from kvasir_ontology.visualization.interface import VisualizationInterface
from kvasir_api.modules.entity_graph.service import EntityGraphs


router = APIRouter()


@router.get("/images/{image_id}", response_model=ImageBase)
async def get_image_endpoint(
    image_id: UUID,
    visualization_service: Annotated[VisualizationInterface, Depends(
        get_visualization_service)]
) -> ImageBase:
    """Get an image"""
    return (await visualization_service.get_images([image_id]))[0]


@router.post("/images", response_model=List[ImageBase])
async def post_images_endpoint(
    image_creates: List[ImageCreate],
    visualization_service: Annotated[VisualizationInterface, Depends(
        get_visualization_service)]
) -> List[ImageBase]:
    """Create new images"""
    return await visualization_service.create_images(image_creates)


@router.get("/echarts/{echart_id}", response_model=EchartBase)
async def get_echart_endpoint(
    echart_id: UUID,
    visualization_service: Annotated[VisualizationInterface, Depends(
        get_visualization_service)]
) -> EchartBase:
    """Get an echart"""
    return (await visualization_service.get_echarts([echart_id]))[0]


@router.post("/echarts", response_model=List[EchartBase])
async def post_echarts_endpoint(
    echart_creates: List[EchartCreate],
    visualization_service: Annotated[VisualizationInterface, Depends(
        get_visualization_service)]
) -> List[EchartBase]:
    """Create new echarts"""
    return await visualization_service.create_echarts(echart_creates)


@router.get("/tables/{table_id}", response_model=TableBase)
async def get_table_endpoint(
    table_id: UUID,
    visualization_service: Annotated[VisualizationInterface, Depends(
        get_visualization_service)]
) -> TableBase:
    """Get a table"""
    return (await visualization_service.get_tables([table_id]))[0]


@router.post("/tables", response_model=List[TableBase])
async def post_tables_endpoint(
    table_creates: List[TableCreate],
    visualization_service: Annotated[VisualizationInterface, Depends(
        get_visualization_service)]
) -> List[TableBase]:
    """Create new tables"""
    return await visualization_service.create_tables(table_creates)


@router.get("/images/{image_id}/download")
async def download_image_endpoint(
    image_id: UUID,
    mount_group_id: UUID,
    visualization_service: Annotated[VisualizationInterface, Depends(
        get_visualization_service)]
) -> Response:
    image_obj = await visualization_service.get_image(image_id)
    image_path = Path(image_obj.image_path)
    allowed_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp']
    if image_path.suffix.lower() not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image file type: {image_path.suffix}"
        )

    image_content = await visualization_service.download_image(image_id, mount_group_id)

    content_type_map = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.svg': 'image/svg+xml',
        '.webp': 'image/webp'
    }
    content_type = content_type_map.get(
        image_path.suffix.lower(), 'application/octet-stream')

    return Response(content=image_content, media_type=content_type)


class ResultTable(BaseModel):
    data: Dict[str, List[Any]]
    index_column: str


@router.get("/tables/{table_id}/download", response_model=ResultTable)
async def download_table_endpoint(
    table_id: UUID,
    mount_group_id: UUID,
    visualization_service: Annotated[VisualizationInterface, Depends(
        get_visualization_service)]
) -> ResultTable:
    try:
        table_obj = await visualization_service.get_table(table_id)
        table_path = Path(table_obj.table_path)

        if table_path.suffix.lower() != '.parquet':
            raise HTTPException(
                status_code=400,
                detail=f"Invalid table file type. Expected .parquet, got: {table_path.suffix}"
            )

        table_bytes = await visualization_service.download_table(table_id, mount_group_id)

        df = pd.read_parquet(BytesIO(table_bytes))
        data_dict = df.to_dict(orient="list")
        index_column = df.index.name if df.index.name else "index"
        data_dict[index_column] = df.index.tolist()

        return ResultTable(
            data=data_dict,
            index_column=index_column
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read parquet file: {str(e)}"
        )


@router.post("/echarts/{chart_id}/get-chart", response_model=EChartsOption)
async def get_chart_endpoint(
    chart_id: UUID,
    mount_group_id: UUID,
    original_object_id: Optional[str] = None,
    visualization_service: Annotated[VisualizationInterface, Depends(
        get_visualization_service)] = None,
) -> EChartsOption:
    return await visualization_service.download_echart(chart_id, mount_group_id, original_object_id)
