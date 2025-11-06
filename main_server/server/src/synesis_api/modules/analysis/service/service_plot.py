import uuid
from typing import List, Optional, Dict, Any, List
from fastapi import HTTPException
import math
from datetime import datetime
from pyecharts import options as opts
from pyecharts.charts import Line, Bar, Scatter
from pyecharts.globals import ThemeType
from pyecharts.render import make_snapshot
from snapshot_selenium import snapshot
from sqlalchemy import select, insert, update, delete


from synesis_api.database.service import execute, fetch_one, fetch_all
from synesis_api.modules.analysis.models import result_image
from synesis_schemas.main_server import BasePlot, PlotCreate, PlotUpdate
# from synesis_schemas.main_server import AggregationObjectWithRawData
from synesis_schemas.main_server import BasePlot


async def create_plot(plot_create: PlotCreate) -> BasePlot:
    plot_in_db = BasePlot(
        id=uuid.uuid4(),
        **plot_create.model_dump()
    )
    await execute(
        insert(result_image).values(**plot_in_db.model_dump()),
        commit_after=True
    )

    return plot_in_db


async def get_plot_by_id(plot_id: uuid.UUID) -> Optional[BasePlot]:
    result = await fetch_one(
        select(result_image).where(result_image.c.id == plot_id)
    )

    if result is None:
        return None

    return BasePlot(**result)


async def get_plots_by_analysis_result_id(analysis_result_id: uuid.UUID) -> List[BasePlot]:
    results = await fetch_all(
        select(result_image).where(
            result_image.c.analysis_result_id == analysis_result_id)
    )

    return [BasePlot(**result) for result in results]


async def update_plot(plot_id: uuid.UUID, plot_update: PlotUpdate) -> Optional[BasePlot]:
    # Check if plot exists
    plot_in_db = await get_plot_by_id(plot_id)
    if plot_in_db is None:
        raise HTTPException(status_code=404, detail="Plot not found")

    # Update the plot
    await execute(
        update(result_image).where(result_image.c.id == plot_id).values(
            **plot_update.model_dump()),
        commit_after=True
    )
    # Return updated plot
    updated_plot = await get_plot_by_id(plot_id)
    return updated_plot


async def delete_plot(plot_id: uuid.UUID) -> bool:
    # Check if plot exists
    existing_plot = await get_plot_by_id(plot_id)
    if existing_plot is None:
        return False

    # Delete the plot
    await execute(
        delete(result_image).where(result_image.c.id == plot_id),
        commit_after=True
    )


def convert_data_by_type(key: tuple, raw_data: List[Any]) -> List[Any]:
    """Convert data based on datatype, similar to EChartWrapper logic"""
    if len(key) == 2:
        column_name, data_type = key
        if data_type == 'datetime' and raw_data and len(raw_data) > 0:
            # Convert bigint array to Date array
            return [datetime.fromtimestamp(timestamp/1e9) for timestamp in raw_data]
    return raw_data


def get_min_max(series: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate min/max values for series data"""
    all_values = []
    for serie in series:
        if 'data' in serie and serie['data']:
            numeric_values = [v for v in serie['data'] if isinstance(
                v, (int, float)) and (not isinstance(v, float) or not math.isnan(v))]
            all_values.extend(numeric_values)

    if not all_values:
        return {'min': 0, 'max': 100}

    return {'min': min(all_values), 'max': max(all_values)}


def format_time_stamps(value: Any, x_axis_data: List[Any]) -> str:
    """Format timestamps for display"""
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M')
    return str(value)


def create_pyecharts_chart(plot: BasePlot, aggregation_data) -> Any:
    raise NotImplementedError("This function is not implemented")
    """Convert plot configuration and data to pyecharts chart"""
    config = plot.plot_config

    data = aggregation_data.data.output_data.data
    columns_to_plot = [col for col in config.y_axis_columns if col.enabled]

    # Get the x-axis column data
    x_axis_key = next((key for key in data.keys()
                      if key[0] == config.x_axis_column.name), None)
    if not x_axis_key:
        raise ValueError(
            f"X-axis column {config.x_axis_column.name} not found in data")

    x_axis_raw_data = data.get(x_axis_key, [])
    x_axis_data = convert_data_by_type(x_axis_key, x_axis_raw_data)

    # Convert datetime objects to strings for x-axis
    x_axis_labels = [format_time_stamps(val, x_axis_data) if isinstance(
        val, datetime) else str(val) for val in x_axis_data]

    # Dictionary to store whether to inlcude each series in the legend
    legend_include = {}

    bar_chart = Bar(init_opts=opts.InitOpts(
        width="600px",
        height="450px",
        theme=ThemeType.DARK,
        bg_color="transparent"
    ))
    scatter_chart = Scatter(init_opts=opts.InitOpts(
        width="600px",
        height="450px",
        theme=ThemeType.DARK,
        bg_color="transparent"
    ))
    line_chart = Line(init_opts=opts.InitOpts(
        width="600px",
        height="450px",
        theme=ThemeType.DARK,
        bg_color="transparent"
    ))

    # Add series for each enabled column
    for col in columns_to_plot:
        column_key = next((key for key in data.keys()
                          if key[0] == col.name), None)
        column_raw_data = data.get(column_key, []) if column_key else []
        column_data = convert_data_by_type(
            column_key, column_raw_data) if column_key else []
        chart_type = col.line_type

        # Convert data to the format expected by pyecharts
        if chart_type == 'scatter':
            # For scatter plots, data should be list of [x, y] pairs
            scatter_data = list(zip(x_axis_data, column_data))
            scatter_chart.add_xaxis(x_axis_labels)
            scatter_chart.add_yaxis(
                series_name=col.name,
                y_axis=scatter_data,
                color=col.color,
                symbol_size=6,
                yaxis_index=col.y_axis_index
            )
        elif chart_type == 'bar':
            bar_chart.add_xaxis(x_axis_labels)
            bar_chart.add_yaxis(
                series_name=col.name,
                y_axis=list(column_data),
                color=col.color,
                is_large=True,
                yaxis_index=col.y_axis_index
            )
        else:
            # For line and bar charts
            line_chart.add_xaxis(x_axis_labels)
            line_chart.add_yaxis(
                series_name=col.name,
                y_axis=list(column_data),
                is_symbol_show=False,
                color=col.color,
                is_smooth=True,
                yaxis_index=col.y_axis_index
            )

    # Add straight lines if configured
    if config.straight_lines:
        for i, line in enumerate(config.straight_lines):
            if not line.include_in_legend:
                legend_include[line.name] = False
            straight_line_data = [line.y_value] * len(x_axis_data)
            line_chart.add_yaxis(
                series_name=line.name if line.include_in_legend else '',
                y_axis=straight_line_data,
                color=line.color or '#e5e7eb',
                is_smooth=False,
                label_opts=opts.LabelOpts(
                    is_show=True if line.include_in_legend else False)
            )

    # Add mark areas
    if config.mark_areas:
        for i, area in enumerate(config.mark_areas):
            if not area.include_in_legend:
                legend_include[area.name] = False
            line_chart.add_yaxis(
                series_name=area.name if area.include_in_legend else '',
                y_axis=[],
                markarea_opts=opts.MarkAreaOpts(
                    data=[opts.MarkAreaItem(
                        x=(area.x_start, area.x_end), y=(area.y_start, area.y_end))],
                    itemstyle_opts=opts.ItemStyleOpts(
                        color=area.color or '#e5e7eb', opacity=0.1)
                ),
                is_smooth=True,
                label_opts=opts.LabelOpts(
                    is_show=True if line.include_in_legend else False)
            )
    # Set chart options
    if config.y_axis_2_enabled:
        line_chart.extend_axis(
            yaxis=opts.AxisOpts(
                name=config.y_axis_2_name or "",
                splitline_opts=opts.SplitLineOpts(
                    is_show=True,
                    linestyle_opts=opts.LineStyleOpts(color="#dddddd")
                ),
                axisline_opts=opts.AxisLineOpts(
                    linestyle_opts=opts.LineStyleOpts(color="#000000")),
                axislabel_opts=opts.LabelOpts(color="#000000", formatter=f"{{value}} {config.y_axis_2_units or ''}"
                                              ),
                min_=config.y_axis_2_min,
                max_=config.y_axis_2_max
            )
        )

    line_chart.overlap(bar_chart).overlap(scatter_chart)
    line_chart.set_global_opts(
        title_opts=opts.TitleOpts(
            title=config.title or "Chart Visualization",
            pos_left="center",
            title_textstyle_opts=opts.TextStyleOpts(
                color="#000000",
                font_size=16,
                font_weight="bold"
            )
        ),
        tooltip_opts=opts.TooltipOpts(
            trigger="axis",
            background_color="#0a101c",
            border_color="#2a4170",
            textstyle_opts=opts.TextStyleOpts(color="#000000")
        ),
        legend_opts=opts.LegendOpts(
            pos_top="30px",
            textstyle_opts=opts.TextStyleOpts(color="#000000"),
            selected_map=legend_include
        ),
        xaxis_opts=opts.AxisOpts(
            name=config.x_axis_name or "",
            splitline_opts=opts.SplitLineOpts(
                is_show=True,
                linestyle_opts=opts.LineStyleOpts(color="#dddddd")
            ),
            axisline_opts=opts.AxisLineOpts(
                linestyle_opts=opts.LineStyleOpts(color="#000000")),
            axislabel_opts=opts.LabelOpts(color="#000000", font_size=12)
        ),
        yaxis_opts=opts.AxisOpts(
            name=config.y_axis_name or "",
            splitline_opts=opts.SplitLineOpts(
                is_show=True,
                linestyle_opts=opts.LineStyleOpts(color="#dddddd")
            ),
            axisline_opts=opts.AxisLineOpts(
                linestyle_opts=opts.LineStyleOpts(color="#000000")),
            axislabel_opts=opts.LabelOpts(
                color="#000000",
                formatter=f"{{value}} {config.y_axis_units or ''}"
            ),
            min_=config.y_axis_min,
            max_=config.y_axis_max
        ),
        datazoom_opts=[
            opts.DataZoomOpts(type_="inside"),
            opts.DataZoomOpts(
                type_="slider") if config.slider_enabled else None
        ] if config.slider_enabled else None
    )

    return line_chart


async def render_plot_to_png_pyecharts(plot: BasePlot, aggregation_data) -> bytes:
    """
    Render a plot to PNG file using pyecharts

    Args:
        plot: BasePlot object with plot configuration
        aggregation_data: AggregationObjectWithRawData with chart data
        output_path: Path where to save the PNG file
        width: Chart width in pixels
        height: Chart height in pixels

    Returns:
        Path to the generated PNG file
    """
    raise NotImplementedError("This function is not implemented")
    try:
        # Create pyecharts chart
        chart = create_pyecharts_chart(plot, aggregation_data)

        # Render to PNG using snapshot and return the bytes data
        import base64
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(mode='w', suffix='.png', delete=False) as temp_file:
            temp_file_path = temp_file.name

        make_snapshot(snapshot, chart.render(), temp_file_path)

        with open(temp_file_path, "rb") as f:
            bytes_data = f.read()

        b64 = base64.b64encode(bytes_data).decode("utf-8")
        os.unlink(temp_file_path)
        return b64

    except Exception as e:
        raise RuntimeError(
            f"Failed to render plot to PNG with pyecharts: {str(e)}")
