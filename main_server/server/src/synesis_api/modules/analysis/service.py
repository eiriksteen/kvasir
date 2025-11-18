import uuid
from datetime import datetime, timezone
from typing import List, Annotated, AsyncGenerator, Union
from sqlalchemy import select, insert, delete
from fastapi import HTTPException, Depends

from synesis_api.database.service import fetch_all, execute, fetch_one
from synesis_api.redis import get_redis
from synesis_api.modules.analysis.models import (
    analysis,
    analysis_section,
    analysis_cell,
    markdown_cell,
    code_cell,
    code_output,
    result_image,
    result_echart,
    result_table,
)
from synesis_api.modules.visualization.service import VisualizationService
from kvasir_ontology.entities.analysis.data_model import (
    AnalysisBase,
    AnalysisSectionBase,
    AnalysisCellBase,
    MarkdownCellBase,
    CodeCellBase,
    CodeOutputBase,
    ResultImageBase,
    ResultEChartBase,
    ResultTableBase,
    CodeOutput,
    CodeCell,
    AnalysisCell,
    Section,
    Analysis,
    AnalysisCreate,
    SectionCreate,
    CodeCellCreate,
    MarkdownCellCreate,
    CodeOutputCreate,
)
from kvasir_ontology.entities.analysis.interface import AnalysisInterface
from synesis_api.auth.service import get_current_user
from synesis_api.auth.schema import User


class Analyses(AnalysisInterface):
    def __init__(self, user_id: uuid.UUID):
        super().__init__(user_id)
        self.visualization_service = VisualizationService(user_id)

    async def create_analysis(self, analysis_create: AnalysisCreate) -> Analysis:
        now = datetime.now(timezone.utc)
        analysis_record = AnalysisBase(
            id=uuid.uuid4(),
            name=analysis_create.name,
            description=analysis_create.description,
            created_at=now,
            updated_at=now,
        )

        await execute(
            insert(analysis).values(
                **analysis_record.model_dump(),
                user_id=self.user_id
            ),
            commit_after=True
        )

        if analysis_create.sections_create:
            for section_create in analysis_create.sections_create:
                section_create_with_analysis = SectionCreate(
                    analysis_id=analysis_record.id,
                    name=section_create.name,
                    description=section_create.description,
                    code_cells_create=section_create.code_cells_create,
                    markdown_cells_create=section_create.markdown_cells_create,
                )
                await self.create_section(section_create_with_analysis)

        return await self.get_analysis(analysis_record.id)

    async def get_analysis(self, analysis_id: uuid.UUID) -> Analysis:
        analyses = await self.get_analyses([analysis_id])
        if not analyses:
            raise HTTPException(
                status_code=404,
                detail=f"Analysis with id {analysis_id} not found"
            )
        return analyses[0]

    async def _get_analysis_cell(self, cell_id: uuid.UUID) -> AnalysisCell:
        cell_query = select(analysis_cell).where(analysis_cell.c.id == cell_id)
        cell_record = await fetch_one(cell_query)
        if not cell_record:
            raise HTTPException(
                status_code=404,
                detail=f"Analysis cell with id {cell_id} not found"
            )

        cell_obj = AnalysisCellBase(**cell_record)

        if cell_obj.type == "markdown":
            markdown_query = select(markdown_cell).where(
                markdown_cell.c.id == cell_id)
            markdown_data = await fetch_one(markdown_query)
            if not markdown_data:
                raise HTTPException(
                    status_code=404,
                    detail=f"Markdown cell with id {cell_id} not found"
                )
            markdown_obj = MarkdownCellBase(**markdown_data)
            return AnalysisCell(**cell_obj.model_dump(), type_fields=markdown_obj)

        elif cell_obj.type == "code":
            code_query = select(code_cell).where(code_cell.c.id == cell_id)
            code_data = await fetch_one(code_query)
            if not code_data:
                raise HTTPException(
                    status_code=404,
                    detail=f"Code cell with id {cell_id} not found"
                )
            code_obj = CodeCellBase(**code_data)

            output_query = select(code_output).where(
                code_output.c.id == cell_id)
            output_data = await fetch_one(output_query)

            if output_data:
                output_obj = CodeOutputBase(**output_data)

                image_query = select(result_image).where(
                    result_image.c.code_cell_id == cell_id)
                result_images_data = await fetch_all(image_query)
                image_ids = [ri["image_id"] for ri in result_images_data]

                echart_query = select(result_echart).where(
                    result_echart.c.code_cell_id == cell_id)
                result_echarts_data = await fetch_all(echart_query)
                echart_ids = [re["echart_id"] for re in result_echarts_data]

                table_query = select(result_table).where(
                    result_table.c.code_cell_id == cell_id)
                result_tables_data = await fetch_all(table_query)
                table_ids = [rt["table_id"] for rt in result_tables_data]

                images_list = await self.visualization_service.get_images(image_ids) if image_ids else []
                echarts_list = await self.visualization_service.get_echarts(echart_ids) if echart_ids else []
                tables_list = await self.visualization_service.get_tables(table_ids) if table_ids else []

                code_output_full = CodeOutput(
                    **output_obj.model_dump(),
                    images=images_list,
                    echarts=echarts_list,
                    tables=tables_list,
                )
            else:
                code_output_full = CodeOutput(
                    id=code_obj.id,
                    output="",
                    created_at=code_obj.created_at,
                    updated_at=code_obj.updated_at,
                    images=[],
                    echarts=[],
                    tables=[],
                )

            code_cell_full = CodeCell(
                **code_obj.model_dump(), output=code_output_full)
            return AnalysisCell(**cell_obj.model_dump(), type_fields=code_cell_full)

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown cell type: {cell_obj.type}"
            )

    async def get_analyses(self, analysis_ids: List[uuid.UUID]) -> List[Analysis]:
        if not analysis_ids:
            return []

        analysis_query = select(analysis).where(
            analysis.c.id.in_(analysis_ids),
            analysis.c.user_id == self.user_id
        )
        analysis_records = await fetch_all(analysis_query)

        if not analysis_records:
            return []

        analysis_ids_list = [a["id"] for a in analysis_records]

        section_query = select(analysis_section).where(
            analysis_section.c.analysis_id.in_(analysis_ids_list)
        )
        section_records = await fetch_all(section_query)

        if not section_records:
            return [
                Analysis(**AnalysisBase(**a).model_dump(), sections=[])
                for a in analysis_records
            ]

        section_ids_list = [s["id"] for s in section_records]

        cell_query = select(analysis_cell).where(
            analysis_cell.c.section_id.in_(section_ids_list)
        )
        cell_records = await fetch_all(cell_query)

        markdown_cell_ids = []
        code_cell_ids = []
        for cell in cell_records:
            if cell["type"] == "markdown":
                markdown_cell_ids.append(cell["id"])
            elif cell["type"] == "code":
                code_cell_ids.append(cell["id"])

        markdown_cells_data = []
        if markdown_cell_ids:
            markdown_query = select(markdown_cell).where(
                markdown_cell.c.id.in_(markdown_cell_ids)
            )
            markdown_cells_data = await fetch_all(markdown_query)

        code_cells_data = []
        if code_cell_ids:
            code_query = select(code_cell).where(
                code_cell.c.id.in_(code_cell_ids)
            )
            code_cells_data = await fetch_all(code_query)

        code_output_ids = []
        code_outputs_data = []
        if code_cell_ids:
            output_query = select(code_output).where(
                code_output.c.id.in_(code_cell_ids)
            )
            code_outputs_data = await fetch_all(output_query)
            code_output_ids = [co["id"] for co in code_outputs_data]

        result_images_data = []
        result_echarts_data = []
        result_tables_data = []
        if code_output_ids:
            image_query = select(result_image).where(
                result_image.c.code_cell_id.in_(code_output_ids)
            )
            result_images_data = await fetch_all(image_query)

            echart_query = select(result_echart).where(
                result_echart.c.code_cell_id.in_(code_output_ids)
            )
            result_echarts_data = await fetch_all(echart_query)

            table_query = select(result_table).where(
                result_table.c.code_cell_id.in_(code_output_ids)
            )
            result_tables_data = await fetch_all(table_query)

        image_ids = [ri["image_id"]
                     for ri in result_images_data] if result_images_data else []
        echart_ids = [re["echart_id"]
                      for re in result_echarts_data] if result_echarts_data else []
        table_ids = [rt["table_id"]
                     for rt in result_tables_data] if result_tables_data else []

        images_dict = {}
        if image_ids:
            images_list = await self.visualization_service.get_images(image_ids)
            images_dict = {img.id: img for img in images_list}

        echarts_dict = {}
        if echart_ids:
            echarts_list = await self.visualization_service.get_echarts(echart_ids)
            echarts_dict = {ech.id: ech for ech in echarts_list}

        tables_dict = {}
        if table_ids:
            tables_list = await self.visualization_service.get_tables(table_ids)
            tables_dict = {tbl.id: tbl for tbl in tables_list}

        output_analyses = []
        for analysis_record in analysis_records:
            analysis_obj = AnalysisBase(**analysis_record)

            sections_for_analysis = [
                s for s in section_records if s["analysis_id"] == analysis_obj.id
            ]

            sections_list = []
            for section_record in sections_for_analysis:
                section_obj = AnalysisSectionBase(**section_record)

                cells_for_section = [
                    c for c in cell_records if c["section_id"] == section_obj.id
                ]

                cells_list = []
                for cell_record in cells_for_section:
                    cell_obj = AnalysisCellBase(**cell_record)

                    if cell_obj.type == "markdown":
                        markdown_data = next(
                            (m for m in markdown_cells_data if m["id"]
                             == cell_obj.id),
                            None
                        )
                        if markdown_data:
                            markdown_obj = MarkdownCellBase(**markdown_data)
                            cells_list.append(
                                AnalysisCell(**cell_obj.model_dump(),
                                             type_fields=markdown_obj)
                            )

                    elif cell_obj.type == "code":
                        code_data = next(
                            (c for c in code_cells_data if c["id"]
                             == cell_obj.id),
                            None
                        )
                        if code_data:
                            code_obj = CodeCellBase(**code_data)

                            output_data = next(
                                (o for o in code_outputs_data if o["id"]
                                 == code_obj.id),
                                None
                            )

                            if output_data:
                                output_obj = CodeOutputBase(**output_data)

                                images_for_cell = [
                                    images_dict[ri["image_id"]]
                                    for ri in result_images_data
                                    if ri["code_cell_id"] == code_obj.id
                                    and ri["image_id"] in images_dict
                                ]
                                echarts_for_cell = [
                                    echarts_dict[re["echart_id"]]
                                    for re in result_echarts_data
                                    if re["code_cell_id"] == code_obj.id
                                    and re["echart_id"] in echarts_dict
                                ]
                                tables_for_cell = [
                                    tables_dict[rt["table_id"]]
                                    for rt in result_tables_data
                                    if rt["code_cell_id"] == code_obj.id
                                    and rt["table_id"] in tables_dict
                                ]

                                code_output_full = CodeOutput(
                                    **output_obj.model_dump(),
                                    images=images_for_cell,
                                    echarts=echarts_for_cell,
                                    tables=tables_for_cell,
                                )
                            else:
                                code_output_full = CodeOutput(
                                    id=code_obj.id,
                                    output="",
                                    created_at=code_obj.created_at,
                                    updated_at=code_obj.updated_at,
                                    images=[],
                                    echarts=[],
                                    tables=[],
                                )

                            code_cell_full = CodeCell(
                                **code_obj.model_dump(),
                                output=code_output_full
                            )
                            cells_list.append(
                                AnalysisCell(**cell_obj.model_dump(),
                                             type_fields=code_cell_full)
                            )

                cells_list.sort(key=lambda c: c.order)

                section_full = Section(
                    **section_obj.model_dump(),
                    cells=cells_list
                )
                sections_list.append(section_full)

            output_analyses.append(
                Analysis(**analysis_obj.model_dump(), sections=sections_list)
            )

        return output_analyses

    async def create_section(self, section_create: SectionCreate) -> Analysis:
        now = datetime.now(timezone.utc)
        section_record = AnalysisSectionBase(
            id=uuid.uuid4(),
            name=section_create.name,
            analysis_id=section_create.analysis_id,
            description=section_create.description,
            created_at=now,
            updated_at=now,
        )

        await execute(
            insert(analysis_section).values(section_record.model_dump()),
            commit_after=True
        )

        if section_create.code_cells_create:
            for code_cell_create in section_create.code_cells_create:
                code_cell_create.section_id = section_record.id
                await self.create_code_cell(code_cell_create)

        if section_create.markdown_cells_create:
            for markdown_cell_create in section_create.markdown_cells_create:
                markdown_cell_create.section_id = section_record.id
                await self.create_markdown_cell(markdown_cell_create)

        return await self.get_analysis(section_create.analysis_id)

    async def create_markdown_cell(self, markdown_cell_create: MarkdownCellCreate) -> AnalysisCell:
        now = datetime.now(timezone.utc)

        cell_id = uuid.uuid4()
        cell_record = AnalysisCellBase(
            id=cell_id,
            order=markdown_cell_create.order,
            type="markdown",
            section_id=markdown_cell_create.section_id,
            created_at=now,
            updated_at=now,
        )

        await execute(
            insert(analysis_cell).values(cell_record.model_dump()),
            commit_after=True
        )

        markdown_record = MarkdownCellBase(
            id=cell_id,
            markdown=markdown_cell_create.markdown,
            created_at=now,
            updated_at=now,
        )

        await execute(
            insert(markdown_cell).values(markdown_record.model_dump()),
            commit_after=True
        )

        return AnalysisCell(**cell_record.model_dump(), type_fields=markdown_record)

    async def create_code_cell(self, code_cell_create: CodeCellCreate) -> AnalysisCell:
        now = datetime.now(timezone.utc)

        cell_id = uuid.uuid4()
        cell_record = AnalysisCellBase(
            id=cell_id,
            order=code_cell_create.order,
            type="code",
            section_id=code_cell_create.section_id,
            created_at=now,
            updated_at=now,
        )

        await execute(
            insert(analysis_cell).values(cell_record.model_dump()),
            commit_after=True
        )

        code_record = CodeCellBase(
            id=cell_id,
            code=code_cell_create.code,
            created_at=now,
            updated_at=now,
        )

        await execute(
            insert(code_cell).values(code_record.model_dump()),
            commit_after=True
        )

        code_output_full = None
        if code_cell_create.output:
            # Use the generated cell_id if code_cell_id is not provided
            output_cell_id = code_cell_create.output.code_cell_id or cell_id
            code_output_create = CodeOutputCreate(
                code_cell_id=output_cell_id,
                output=code_cell_create.output.output,
                images=code_cell_create.output.images,
                echarts=code_cell_create.output.echarts,
                tables=code_cell_create.output.tables,
            )
            images_list = []
            if code_output_create.images:
                images_created = await self.visualization_service.create_images(code_output_create.images)
                images_list = images_created

            echarts_list = []
            if code_output_create.echarts:
                echarts_created = await self.visualization_service.create_echarts(code_output_create.echarts)
                echarts_list = echarts_created

            tables_list = []
            if code_output_create.tables:
                tables_created = await self.visualization_service.create_tables(code_output_create.tables)
                tables_list = tables_created

            output_record = CodeOutputBase(
                id=cell_id,
                output=code_output_create.output,
                created_at=now,
                updated_at=now,
            )

            await execute(
                insert(code_output).values(output_record.model_dump()),
                commit_after=True
            )

            if images_list:
                image_ids = [img.id for img in images_list]
                image_records = [
                    ResultImageBase(
                        id=uuid.uuid4(),
                        code_cell_id=cell_id,
                        created_at=now,
                        updated_at=now,
                    ).model_dump() | {"image_id": img_id}
                    for img_id in image_ids
                ]
                await execute(
                    insert(result_image).values(image_records),
                    commit_after=True
                )

            if echarts_list:
                echart_ids = [ech.id for ech in echarts_list]
                echart_records = [
                    ResultEChartBase(
                        id=uuid.uuid4(),
                        code_cell_id=cell_id,
                        created_at=now,
                        updated_at=now,
                    ).model_dump() | {"echart_id": ech_id}
                    for ech_id in echart_ids
                ]
                await execute(
                    insert(result_echart).values(echart_records),
                    commit_after=True
                )

            if tables_list:
                table_ids = [tbl.id for tbl in tables_list]
                table_records = [
                    ResultTableBase(
                        id=uuid.uuid4(),
                        code_cell_id=cell_id,
                        created_at=now,
                        updated_at=now,
                    ).model_dump() | {"table_id": tbl_id}
                    for tbl_id in table_ids
                ]
                await execute(
                    insert(result_table).values(table_records),
                    commit_after=True
                )

            code_output_full = CodeOutput(
                **output_record.model_dump(),
                images=images_list,
                echarts=echarts_list,
                tables=tables_list,
            )
        else:
            code_output_full = None

        code_cell_full = CodeCell(
            **code_record.model_dump(), output=code_output_full)
        return AnalysisCell(**cell_record.model_dump(), type_fields=code_cell_full)

    async def create_code_output(self, code_output_create: CodeOutputCreate) -> Analysis:
        if code_output_create.code_cell_id is None:
            raise HTTPException(
                status_code=400,
                detail="code_cell_id is required when creating code output separately"
            )

        now = datetime.now(timezone.utc)

        image_ids = []
        if code_output_create.images:
            images_created = await self.visualization_service.create_images(code_output_create.images)
            image_ids = [img.id for img in images_created]

        echart_ids = []
        if code_output_create.echarts:
            echarts_created = await self.visualization_service.create_echarts(code_output_create.echarts)
            echart_ids = [ech.id for ech in echarts_created]

        table_ids = []
        if code_output_create.tables:
            tables_created = await self.visualization_service.create_tables(code_output_create.tables)
            table_ids = [tbl.id for tbl in tables_created]

        output_record = CodeOutputBase(
            id=code_output_create.code_cell_id,
            output=code_output_create.output,
            created_at=now,
            updated_at=now,
        )

        await execute(
            insert(code_output).values(output_record.model_dump()),
            commit_after=True
        )

        if image_ids:
            image_records = [
                ResultImageBase(
                    id=uuid.uuid4(),
                    code_cell_id=code_output_create.code_cell_id,
                    created_at=now,
                    updated_at=now,
                ).model_dump() | {"image_id": img_id}
                for img_id in image_ids
            ]
            await execute(
                insert(result_image).values(image_records),
                commit_after=True
            )

        if echart_ids:
            echart_records = [
                ResultEChartBase(
                    id=uuid.uuid4(),
                    code_cell_id=code_output_create.code_cell_id,
                    created_at=now,
                    updated_at=now,
                ).model_dump() | {"echart_id": ech_id}
                for ech_id in echart_ids
            ]
            await execute(
                insert(result_echart).values(echart_records),
                commit_after=True
            )

        if table_ids:
            table_records = [
                ResultTableBase(
                    id=uuid.uuid4(),
                    code_cell_id=code_output_create.code_cell_id,
                    created_at=now,
                    updated_at=now,
                ).model_dump() | {"table_id": tbl_id}
                for tbl_id in table_ids
            ]
            await execute(
                insert(result_table).values(table_records),
                commit_after=True
            )

        code_cell_query = select(code_cell).where(
            code_cell.c.id == code_output_create.code_cell_id
        )
        code_cell_record = await fetch_one(code_cell_query)
        if not code_cell_record:
            raise HTTPException(
                status_code=404,
                detail=f"Code cell with id {code_output_create.code_cell_id} not found"
            )

        analysis_cell_query = select(analysis_cell).where(
            analysis_cell.c.id == code_output_create.code_cell_id
        )
        analysis_cell_record = await fetch_one(analysis_cell_query)
        if not analysis_cell_record:
            raise HTTPException(
                status_code=404,
                detail=f"Analysis cell with id {code_output_create.code_cell_id} not found"
            )

        section_query = select(analysis_section).where(
            analysis_section.c.id == analysis_cell_record["section_id"]
        )
        section_record = await fetch_one(section_query)
        if not section_record:
            raise HTTPException(
                status_code=404,
                detail=f"Section not found"
            )

        return await self.get_analysis(section_record["analysis_id"])

    async def create_code_output_image(
        self, code_cell_id: uuid.UUID, code_output_image
    ) -> Analysis:
        now = datetime.now(timezone.utc)

        images_created = await self.visualization_service.create_images([code_output_image])
        image_id = images_created[0].id

        image_record = ResultImageBase(
            id=uuid.uuid4(),
            code_cell_id=code_cell_id,
            created_at=now,
            updated_at=now,
        ).model_dump() | {"image_id": image_id}
        await execute(
            insert(result_image).values(image_record),
            commit_after=True
        )

        analysis_cell_query = select(analysis_cell).where(
            analysis_cell.c.id == code_cell_id
        )
        analysis_cell_record = await fetch_one(analysis_cell_query)
        if not analysis_cell_record:
            raise HTTPException(
                status_code=404,
                detail=f"Analysis cell with id {code_cell_id} not found"
            )

        section_query = select(analysis_section).where(
            analysis_section.c.id == analysis_cell_record["section_id"]
        )
        section_record = await fetch_one(section_query)
        if not section_record:
            raise HTTPException(
                status_code=404,
                detail=f"Section not found"
            )

        return await self.get_analysis(section_record["analysis_id"])

    async def create_code_output_echart(
        self, code_cell_id: uuid.UUID, code_output_echart
    ) -> Analysis:
        now = datetime.now(timezone.utc)

        echarts_created = await self.visualization_service.create_echarts([code_output_echart])
        echart_id = echarts_created[0].id

        echart_record = ResultEChartBase(
            id=uuid.uuid4(),
            code_cell_id=code_cell_id,
            created_at=now,
            updated_at=now,
        ).model_dump() | {"echart_id": echart_id}
        await execute(
            insert(result_echart).values(echart_record),
            commit_after=True
        )

        analysis_cell_query = select(analysis_cell).where(
            analysis_cell.c.id == code_cell_id
        )
        analysis_cell_record = await fetch_one(analysis_cell_query)
        if not analysis_cell_record:
            raise HTTPException(
                status_code=404,
                detail=f"Analysis cell with id {code_cell_id} not found"
            )

        section_query = select(analysis_section).where(
            analysis_section.c.id == analysis_cell_record["section_id"]
        )
        section_record = await fetch_one(section_query)
        if not section_record:
            raise HTTPException(
                status_code=404,
                detail=f"Section not found"
            )

        return await self.get_analysis(section_record["analysis_id"])

    async def create_code_output_table(
        self, code_cell_id: uuid.UUID, code_output_table
    ) -> Analysis:
        now = datetime.now(timezone.utc)

        tables_created = await self.visualization_service.create_tables([code_output_table])
        table_id = tables_created[0].id

        table_record = ResultTableBase(
            id=uuid.uuid4(),
            code_cell_id=code_cell_id,
            created_at=now,
            updated_at=now,
        ).model_dump() | {"table_id": table_id}
        await execute(
            insert(result_table).values(table_record),
            commit_after=True
        )

        analysis_cell_query = select(analysis_cell).where(
            analysis_cell.c.id == code_cell_id
        )
        analysis_cell_record = await fetch_one(analysis_cell_query)
        if not analysis_cell_record:
            raise HTTPException(
                status_code=404,
                detail=f"Analysis cell with id {code_cell_id} not found"
            )

        section_query = select(analysis_section).where(
            analysis_section.c.id == analysis_cell_record["section_id"]
        )
        section_record = await fetch_one(section_query)
        if not section_record:
            raise HTTPException(
                status_code=404,
                detail=f"Section not found"
            )

        return await self.get_analysis(section_record["analysis_id"])

    async def delete_analysis(self, analysis_id: uuid.UUID) -> None:

        section_query = select(analysis_section).where(
            analysis_section.c.analysis_id == analysis_id
        )
        section_records = await fetch_all(section_query)
        section_ids = [s["id"] for s in section_records]

        if section_ids:
            cell_query = select(analysis_cell).where(
                analysis_cell.c.section_id.in_(section_ids)
            )
            cell_records = await fetch_all(cell_query)
            cell_ids = [c["id"] for c in cell_records]

            markdown_cell_ids = [
                c["id"] for c in cell_records if c["type"] == "markdown"
            ]
            code_cell_ids = [
                c["id"] for c in cell_records if c["type"] == "code"
            ]

            if code_cell_ids:
                await execute(
                    delete(result_image).where(
                        result_image.c.code_cell_id.in_(code_cell_ids)
                    ),
                    commit_after=True
                )
                await execute(
                    delete(result_echart).where(
                        result_echart.c.code_cell_id.in_(code_cell_ids)
                    ),
                    commit_after=True
                )
                await execute(
                    delete(result_table).where(
                        result_table.c.code_cell_id.in_(code_cell_ids)
                    ),
                    commit_after=True
                )

                await execute(
                    delete(code_output).where(
                        code_output.c.id.in_(code_cell_ids)
                    ),
                    commit_after=True
                )

                await execute(
                    delete(code_cell).where(
                        code_cell.c.id.in_(code_cell_ids)
                    ),
                    commit_after=True
                )

            if markdown_cell_ids:
                await execute(
                    delete(markdown_cell).where(
                        markdown_cell.c.id.in_(markdown_cell_ids)
                    ),
                    commit_after=True
                )

            if cell_ids:
                await execute(
                    delete(analysis_cell).where(
                        analysis_cell.c.id.in_(cell_ids)
                    ),
                    commit_after=True
                )

            await execute(
                delete(analysis_section).where(
                    analysis_section.c.id.in_(section_ids)
                ),
                commit_after=True
            )

        await execute(
            delete(analysis).where(analysis.c.id == analysis_id),
            commit_after=True
        )

    async def write_to_analysis_stream(self, run_id: uuid.UUID, message: Union[Section, AnalysisCell]) -> None:
        redis_stream = get_redis()
        await redis_stream.xadd(str(run_id) + "-analysis", message.model_dump(mode="json"))

    async def listen_to_analysis_stream(self, run_id: uuid.UUID) -> AsyncGenerator[Union[Section, AnalysisCell], None]:
        redis_stream = get_redis()
        stream_key = str(run_id) + "-analysis"

        last_id = "$"
        while True:
            response = await redis_stream.xread({stream_key: last_id}, count=1, block=1000)

            if not response:
                continue

            for _, messages in response:
                for message_id, message_data in messages:
                    last_id = message_id

                    if "type" in message_data and message_data["type"] in ["code", "markdown"]:
                        cell = AnalysisCell.model_validate(message_data)
                        yield cell
                    else:
                        section = Section.model_validate(message_data)
                        yield section


# For dependency injection
async def get_analysis_service(user: Annotated[User, Depends(get_current_user)]) -> AnalysisInterface:
    return Analyses(user.id)
