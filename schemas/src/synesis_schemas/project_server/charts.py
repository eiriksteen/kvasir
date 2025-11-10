from pydantic import BaseModel, Field
from typing import Literal, List, Union, Optional, Any, Dict
from datetime import datetime


# ============================================================================
# SMALL SCHEMA (for LLM generation)
# ============================================================================
# This minimal schema is designed for LLMs to easily generate charts.
# It contains only the essential fields needed for common visualizations.


class XAxisSmall(BaseModel):
    """Simplified X-axis - only essential fields"""
    type: str  # "category", "value", "time", "log"
    data: Optional[List[Union[str, float, int, datetime]]] = None
    name: Optional[str] = None


class YAxisSmall(BaseModel):
    """Simplified Y-axis - only essential fields"""
    type: str  # "category", "value", "time", "log"
    name: Optional[str] = None


class LineStyleSmall(BaseModel):
    """Simplified line style"""
    color: Optional[str] = None
    width: Optional[int] = None
    type: Optional[str] = None  # "solid", "dashed", "dotted"


class MarkLineDataItemSmall(BaseModel):
    """Mark line point - for vertical/horizontal lines"""
    name: Optional[str] = None
    xAxis: Optional[Union[str, float, int]] = None
    yAxis: Optional[Union[str, float, int]] = None
    type: Optional[str] = None  # "min", "max", "average", "median"


class MarkLineSmall(BaseModel):
    """Mark line - for vertical/horizontal reference lines"""
    data: List[Union[MarkLineDataItemSmall, List[MarkLineDataItemSmall]]]
    lineStyle: Optional[LineStyleSmall] = None


class MarkAreaDataItemSmall(BaseModel):
    """Mark area boundary point"""
    name: Optional[str] = None
    xAxis: Optional[Union[str, float, int]] = None
    yAxis: Optional[Union[str, float, int]] = None


class MarkAreaSmall(BaseModel):
    """Mark area - for highlighting regions/intervals"""
    data: List[List[MarkAreaDataItemSmall]]  # Each item is [start, end]
    # e.g., {"color": "rgba(0,0,255,0.1)"}
    itemStyle: Optional[Dict[str, Any]] = None


class MarkPointDataItemSmall(BaseModel):
    """Mark point - for highlighting specific data points"""
    name: Optional[str] = None
    coord: Optional[List[Union[str, float, int]]] = None  # [x, y]
    type: Optional[str] = None  # "min", "max", "average"
    itemStyle: Optional[Dict[str, Any]] = None


class MarkPointSmall(BaseModel):
    """Mark point configuration"""
    data: List[MarkPointDataItemSmall]


class SeriesSmall(BaseModel):
    """Simplified series - core visualization element"""
    name: Optional[str] = None
    type: str  # "line", "bar", "scatter"
    data: List[Union[float, int, List[Union[float, int]], Dict[str, Any]]]

    # Optional styling
    smooth: Optional[bool] = None  # For smooth curves (line charts)
    # Fill area under line, e.g., {"opacity": 0.3}
    areaStyle: Optional[Dict[str, Any]] = None

    # Marking features
    markLine: Optional[MarkLineSmall] = None
    markArea: Optional[MarkAreaSmall] = None
    markPoint: Optional[MarkPointSmall] = None


class VisualMapSmall(BaseModel):
    """Simplified visual map - for color mapping"""
    type: str  # "continuous", "piecewise"
    min: Optional[float] = None
    max: Optional[float] = None
    # e.g., {"color": ["#blue", "#red"]}
    inRange: Optional[Dict[str, Any]] = None
    # Which dimension to map (0=x, 1=y, 2=z, etc.)
    dimension: Optional[int] = None


class DataZoomSmall(BaseModel):
    """Simplified data zoom - for zooming/panning"""
    type: str = "inside"  # "inside" = mouse/touch, "slider" = UI control
    start: Optional[float] = None  # Start percentage (0-100)
    end: Optional[float] = None  # End percentage (0-100)


class EChartsOptionSmall(BaseModel):
    """
    Minimal ECharts config for LLM generation.
    Supports: time series, bar charts, scatter plots, zooming, interval marking.
    """
    xAxis: Union[XAxisSmall, List[XAxisSmall]]
    yAxis: Union[YAxisSmall, List[YAxisSmall]]
    series: List[SeriesSmall]
    visualMap: Optional[Union[VisualMapSmall, List[VisualMapSmall]]] = None
    dataZoom: Optional[Union[DataZoomSmall, List[DataZoomSmall]]] = None


# ============================================================================
# FULL SCHEMA (with all fields and defaults)
# ============================================================================
# This is the complete schema that gets sent to ECharts with sensible defaults.


class XAxis(BaseModel):
    type: Literal["category", "value", "time", "log"]
    data: Optional[List[Union[str, float, int, datetime]]] = None
    name: Optional[str] = None
    nameLocation: Optional[Literal["start", "middle", "end"]] = None
    nameGap: Optional[int] = None
    nameTextStyle: Optional[Dict[str, Any]] = None
    boundaryGap: Optional[Union[bool, List[str]]] = None
    min: Optional[Union[float, int, Literal["dataMin"]]] = None
    max: Optional[Union[float, int, Literal["dataMax"]]] = None
    splitLine: Optional[Dict[str, Any]] = None
    axisLine: Optional[Dict[str, Any]] = None
    axisTick: Optional[Dict[str, Any]] = None
    axisLabel: Optional[Dict[str, Any]] = None

    class Config:
        extra = "allow"


class YAxis(BaseModel):
    type: Literal["category", "value", "time", "log"]
    name: Optional[str] = None
    nameLocation: Optional[Literal["start", "middle", "end"]] = None
    nameGap: Optional[int] = None
    nameTextStyle: Optional[Dict[str, Any]] = None
    min: Optional[Union[float, int, Literal["dataMin"]]] = None
    max: Optional[Union[float, int, Literal["dataMax"]]] = None
    splitLine: Optional[Dict[str, Any]] = None
    axisLine: Optional[Dict[str, Any]] = None
    axisTick: Optional[Dict[str, Any]] = None
    axisLabel: Optional[Dict[str, Any]] = None

    class Config:
        extra = "allow"


class LineStyle(BaseModel):
    color: Optional[str] = None
    width: Optional[int] = None
    type: Literal["solid", "dashed", "dotted"] = "solid"
    opacity: Optional[float] = None

    class Config:
        extra = "allow"


class ItemStyle(BaseModel):
    color: Optional[str] = None
    borderColor: Optional[str] = None
    borderWidth: Optional[int] = None
    opacity: Optional[float] = None

    class Config:
        extra = "allow"


class Label(BaseModel):
    show: Optional[bool] = None
    position: Optional[str] = None
    formatter: Optional[Union[str, Dict[str, Any]]] = None
    color: Optional[str] = None
    fontSize: Optional[int] = None

    class Config:
        extra = "allow"


class MarkLineDataItem(BaseModel):
    name: Optional[str] = None
    xAxis: Optional[Union[str, float, int]] = None
    yAxis: Optional[Union[str, float, int]] = None
    type: Optional[Literal["min", "max", "average", "median"]] = None
    lineStyle: Optional[LineStyle] = None
    label: Optional[Label] = None

    class Config:
        extra = "allow"


class MarkLine(BaseModel):
    silent: Optional[bool] = None
    symbol: Optional[Union[str, List[str]]] = None
    lineStyle: Optional[LineStyle] = None
    label: Optional[Label] = None
    data: List[Union[MarkLineDataItem, List[MarkLineDataItem]]]

    class Config:
        extra = "allow"


class MarkAreaDataItem(BaseModel):
    name: Optional[str] = None
    xAxis: Optional[Union[str, float, int]] = None
    yAxis: Optional[Union[str, float, int]] = None
    type: Optional[Literal["min", "max", "average", "median"]] = None
    itemStyle: Optional[ItemStyle] = None
    label: Optional[Label] = None

    class Config:
        extra = "allow"


class MarkArea(BaseModel):
    silent: Optional[bool] = None
    itemStyle: Optional[ItemStyle] = None
    label: Optional[Label] = None
    data: List[List[MarkAreaDataItem]]

    class Config:
        extra = "allow"


class MarkPointDataItem(BaseModel):
    name: Optional[str] = None
    coord: Optional[List[Union[str, float, int]]] = None
    type: Optional[Literal["min", "max", "average"]] = None
    itemStyle: Optional[ItemStyle] = None
    label: Optional[Label] = None
    symbol: Optional[str] = None
    symbolSize: Optional[Union[int, List[int]]] = None

    class Config:
        extra = "allow"


class MarkPoint(BaseModel):
    symbol: Optional[str] = None
    symbolSize: Optional[Union[int, List[int]]] = None
    label: Optional[Label] = None
    itemStyle: Optional[ItemStyle] = None
    data: List[MarkPointDataItem]

    class Config:
        extra = "allow"


class VisualMapContinuous(BaseModel):
    type: Literal["continuous"] = "continuous"
    min: float
    max: float
    text: Optional[List[str]] = None
    inRange: Optional[Dict[str, Any]] = None
    outOfRange: Optional[Dict[str, Any]] = None
    orient: Optional[Literal["horizontal", "vertical"]] = "vertical"
    left: Optional[Union[str, int]] = None
    right: Optional[Union[str, int]] = None
    top: Optional[Union[str, int]] = None
    bottom: Optional[Union[str, int]] = None
    calculable: Optional[bool] = True
    seriesIndex: Optional[Union[int, List[int]]] = None
    dimension: Optional[int] = None

    class Config:
        extra = "allow"


class VisualMapPiecewise(BaseModel):
    type: Literal["piecewise"] = "piecewise"
    pieces: Optional[List[Dict[str, Any]]] = None
    categories: Optional[List[str]] = None
    min: Optional[float] = None
    max: Optional[float] = None
    splitNumber: Optional[int] = None
    text: Optional[List[str]] = None
    inRange: Optional[Dict[str, Any]] = None
    outOfRange: Optional[Dict[str, Any]] = None
    orient: Optional[Literal["horizontal", "vertical"]] = "vertical"
    left: Optional[Union[str, int]] = None
    right: Optional[Union[str, int]] = None
    top: Optional[Union[str, int]] = None
    bottom: Optional[Union[str, int]] = None
    seriesIndex: Optional[Union[int, List[int]]] = None
    dimension: Optional[int] = None

    class Config:
        extra = "allow"


VisualMap = Union[VisualMapContinuous, VisualMapPiecewise]


class Series(BaseModel):
    name: Optional[str] = None
    type: Literal["line", "bar", "scatter", "pie",
                  "candlestick", "boxplot", "heatmap"]
    data: List[Union[float, int, List[Union[float, int]], Dict[str, Any]]]
    xAxisIndex: Optional[int] = None
    yAxisIndex: Optional[int] = None
    smooth: Optional[bool] = False
    lineStyle: Optional[LineStyle] = None
    itemStyle: Optional[ItemStyle] = None
    areaStyle: Optional[Dict[str, Any]] = None
    markLine: Optional[MarkLine] = None
    markArea: Optional[MarkArea] = None
    markPoint: Optional[MarkPoint] = None
    showSymbol: Optional[bool] = None
    symbolSize: Optional[int] = None
    stack: Optional[str] = None
    label: Optional[Label] = None
    emphasis: Optional[Dict[str, Any]] = None

    class Config:
        extra = "allow"


class Legend(BaseModel):
    show: Optional[bool] = True
    data: Optional[List[str]] = None
    orient: Optional[Literal["horizontal", "vertical"]] = "horizontal"
    left: Optional[Union[str, int,
                         Literal["left", "center", "right"]]] = "left"
    top: Optional[Union[str, int, Literal["top", "middle", "bottom"]]] = "top"
    right: Optional[Union[str, int]] = None
    bottom: Optional[Union[str, int]] = None

    class Config:
        extra = "allow"


class Tooltip(BaseModel):
    show: Optional[bool] = True
    trigger: Optional[Literal["item", "axis", "none"]] = "axis"
    axisPointer: Optional[Dict[str, Any]] = None
    formatter: Optional[Union[str, Dict[str, Any]]] = None

    class Config:
        extra = "allow"


class DataZoom(BaseModel):
    type: Literal["inside", "slider"]
    xAxisIndex: Optional[Union[int, List[int]]] = None
    yAxisIndex: Optional[Union[int, List[int]]] = None
    start: Optional[float] = None
    end: Optional[float] = None
    startValue: Optional[Union[int, float, str]] = None
    endValue: Optional[Union[int, float, str]] = None
    minSpan: Optional[float] = None
    maxSpan: Optional[float] = None
    filterMode: Optional[Literal["filter",
                                 "weakFilter", "empty", "none"]] = None

    class Config:
        extra = "allow"


class Grid(BaseModel):
    """Grid configuration for positioning the chart"""
    left: Optional[Union[str, int]] = None
    right: Optional[Union[str, int]] = None
    top: Optional[Union[str, int]] = None
    bottom: Optional[Union[str, int]] = None
    containLabel: Optional[bool] = None

    class Config:
        extra = "allow"


class EChartsOption(BaseModel):
    """
    Complete ECharts configuration with all options and sensible defaults.
    Can be created from EChartsOptionSmall with expand_small_option().
    """
    xAxis: Optional[Union[XAxis, List[XAxis]]] = None
    yAxis: Optional[Union[YAxis, List[YAxis]]] = None
    series: List[Series]

    visualMap: Optional[Union[VisualMap, List[VisualMap]]] = None
    dataZoom: Optional[Union[DataZoom, List[DataZoom]]] = None

    # Auto-populated fields (set sensible defaults)
    legend: Optional[Legend] = Field(default_factory=lambda: Legend(show=True))
    tooltip: Optional[Tooltip] = Field(
        default_factory=lambda: Tooltip(show=True, trigger="axis"))
    grid: Optional[Grid] = Field(
        default_factory=lambda: Grid(containLabel=True))

    class Config:
        extra = "allow"


def expand_small_option(small: EChartsOptionSmall) -> EChartsOption:
    """
    Convert EChartsOptionSmall to EChartsOption with sensible defaults.
    This fills in legend, tooltip, grid, and expands any simplified structures.
    """

    def expand_axis(axis_small: Union[XAxisSmall, YAxisSmall], is_x: bool) -> Union[XAxis, YAxis]:
        """Expand small axis to full axis"""
        data = axis_small.model_dump()
        if is_x:
            return XAxis(**data)
        return YAxis(**data)

    def expand_series(series_small: SeriesSmall) -> Series:
        """Expand small series to full series"""
        data = series_small.model_dump(exclude_none=True)

        # Convert nested small objects to full objects
        if series_small.markLine:
            mark_line_data = []
            for item in series_small.markLine.data:
                if isinstance(item, list):
                    mark_line_data.append([
                        MarkLineDataItem(**d.model_dump()) for d in item
                    ])
                else:
                    mark_line_data.append(
                        MarkLineDataItem(**item.model_dump()))

            line_style = None
            if series_small.markLine.lineStyle:
                line_style = LineStyle(
                    **series_small.markLine.lineStyle.model_dump())

            data["markLine"] = MarkLine(
                data=mark_line_data, lineStyle=line_style)

        if series_small.markArea:
            mark_area_data = []
            for pair in series_small.markArea.data:
                mark_area_data.append([
                    MarkAreaDataItem(**item.model_dump()) for item in pair
                ])
            data["markArea"] = MarkArea(
                data=mark_area_data,
                itemStyle=series_small.markArea.itemStyle
            )

        if series_small.markPoint:
            mark_point_data = [
                MarkPointDataItem(**item.model_dump())
                for item in series_small.markPoint.data
            ]
            data["markPoint"] = MarkPoint(data=mark_point_data)

        return Series(**data)

    # Expand axes
    x_axes = small.xAxis if isinstance(small.xAxis, list) else [small.xAxis]
    y_axes = small.yAxis if isinstance(small.yAxis, list) else [small.yAxis]

    expanded_x = [expand_axis(ax, True) for ax in x_axes]
    expanded_y = [expand_axis(ax, False) for ax in y_axes]

    # Expand series
    expanded_series = [expand_series(s) for s in small.series]

    # Expand visualMap if present
    expanded_visual_map = None
    if small.visualMap:
        visual_maps = small.visualMap if isinstance(
            small.visualMap, list) else [small.visualMap]
        expanded_vms = []
        for vm in visual_maps:
            if vm.type == "continuous":
                expanded_vms.append(VisualMapContinuous(
                    type="continuous",
                    min=vm.min or 0,
                    max=vm.max or 100,
                    inRange=vm.inRange,
                    dimension=vm.dimension
                ))
            else:
                expanded_vms.append(VisualMapPiecewise(
                    type="piecewise",
                    min=vm.min,
                    max=vm.max,
                    inRange=vm.inRange,
                    dimension=vm.dimension
                ))
        expanded_visual_map = expanded_vms if len(
            expanded_vms) > 1 else expanded_vms[0]

    # Expand dataZoom if present
    expanded_data_zoom = None
    if small.dataZoom:
        data_zooms = small.dataZoom if isinstance(
            small.dataZoom, list) else [small.dataZoom]
        expanded_dzs = [
            DataZoom(
                type=dz.type,
                start=dz.start,
                end=dz.end
            ) for dz in data_zooms
        ]
        expanded_data_zoom = expanded_dzs if len(
            expanded_dzs) > 1 else expanded_dzs[0]

    return EChartsOption(
        xAxis=expanded_x if len(expanded_x) > 1 else expanded_x[0],
        yAxis=expanded_y if len(expanded_y) > 1 else expanded_y[0],
        series=expanded_series,
        visualMap=expanded_visual_map,
        dataZoom=expanded_data_zoom,
        legend=Legend(show=True),
        tooltip=Tooltip(show=True, trigger="axis"),
        grid=Grid(containLabel=True)
    )
