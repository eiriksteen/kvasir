from sqlalchemy import Column, ForeignKey, Table, UUID, JSON
from synesis_api.database.core import metadata
import uuid

# Main plots table
plot = Table(
    'plot',
    metadata,
    Column('id', UUID, primary_key=True, default=uuid.uuid4),
    Column('analysis_result_id', UUID, ForeignKey('analysis.analysis_result.id'), nullable=False),
    Column('plot_config', JSON, nullable=False),
    schema='plots',
)