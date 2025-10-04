import uuid
from typing import List, Annotated
from fastapi import APIRouter, Depends, HTTPException
from synesis_schemas.main_server import BasePlot, PlotCreate, PlotUpdate
from synesis_api.modules.plots.service import (
    create_plot,
    get_plot_by_id,
    get_plots_by_analysis_result_id,
    update_plot,
    delete_plot
)
from synesis_api.auth.service import get_current_user
from synesis_schemas.main_server import User

router = APIRouter()


# TODO: Add security checks to all endpoints (check they own the analysis result)

@router.post("/", response_model=BasePlot)
async def create_plot_endpoint(
    plot_create: PlotCreate,
    user: Annotated[User, Depends(get_current_user)] = None
) -> BasePlot:
    """Create a new plot."""
    
    return await create_plot(plot_create)


@router.get("/{plot_id}", response_model=BasePlot)
async def get_plot_endpoint(
    plot_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> BasePlot:
    """Get a specific plot by ID."""
    plot = await get_plot_by_id(plot_id)
    if plot is None:
        raise HTTPException(status_code=404, detail="Plot not found")
    
    return plot


@router.get("/analysis-result/{analysis_result_id}", response_model=List[BasePlot])
async def get_plots_by_analysis_result_endpoint(
    analysis_result_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> List[BasePlot]:
    """Get all plots for a specific analysis result."""
    
    return await get_plots_by_analysis_result_id(analysis_result_id)


@router.put("/{plot_id}", response_model=BasePlot)
async def update_plot_endpoint(
    plot_id: uuid.UUID,
    plot_update: PlotUpdate,
    user: Annotated[User, Depends(get_current_user)] = None
) -> BasePlot:
    """Update an existing plot."""
    # Get the plot to verify user access
    plot = await get_plot_by_id(plot_id)
    if plot is None:
        raise HTTPException(status_code=404, detail="Plot not found")
    
    return await update_plot(plot_id, plot_update)


@router.delete("/{plot_id}")
async def delete_plot_endpoint(
    plot_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> None:
    """Delete a plot."""
    # Get the plot to verify user access
    plot = await get_plot_by_id(plot_id)
    if plot is None:
        raise HTTPException(status_code=404, detail="Plot not found")
    
    
    try:
        await delete_plot(plot_id)
        return
    except:
        raise HTTPException(status_code=500, detail="Failed to delete plot")