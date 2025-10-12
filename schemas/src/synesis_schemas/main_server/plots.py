from pydantic import BaseModel
from uuid import UUID
from typing import Optional, Dict, Any, List

PREDEFINED_COLORS = [
    '#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6',
    '#EC4899', '#06B6D4', '#84CC16', '#F97316', '#6366F1'
]

class PlotColumn(BaseModel):
    name: str
    line_type: str
    color: str
    enabled: bool
    y_axis_index: int = 0


class StraightLine(BaseModel):
    y_value: float
    color: str
    name: str
    include_in_legend: bool = True

class MarkArea(BaseModel):
    name: str
    color: str
    include_in_legend: bool = True
    y_start: Optional[float] = None
    y_end: Optional[float] = None
    x_start: Optional[float] = None
    x_end: Optional[float] = None

class PlotConfig(BaseModel):
    title: str
    subtitle: Optional[str] = None
    x_axis_column: PlotColumn
    y_axis_columns: List[PlotColumn]
    y_axis_min: Optional[float] = None
    y_axis_max: Optional[float] = None
    y_axis_auto: bool = True
    y_axis_name: Optional[str] = None
    x_axis_name: Optional[str] = None
    y_axis_units: Optional[str] = None
    x_axis_units: Optional[str] = None
    y_axis_2_enabled: bool = False
    y_axis_2_min: Optional[float] = None
    y_axis_2_max: Optional[float] = None
    y_axis_2_name: Optional[str] = None
    y_axis_2_units: Optional[str] = None
    y_axis_2_auto: bool = True
    # Advanced options
    straight_lines: Optional[List[StraightLine]] = None
    mark_areas: Optional[List[MarkArea]] = None
    slider_enabled: Optional[bool] = False

class BasePlot(BaseModel):
    id: UUID
    analysis_result_id: UUID
    plot_config: PlotConfig


class PlotCreate(BaseModel):
    analysis_result_id: UUID
    plot_config: PlotConfig

class PlotUpdate(BaseModel):
    plot_config: Optional[Dict[str, Any]] = None

