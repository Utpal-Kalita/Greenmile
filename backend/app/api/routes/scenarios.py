import uuid

from fastapi import APIRouter, File, UploadFile, status

from app.api.dependencies import DatabaseSession
from app.schemas import ImportResult, MapPayload, ScenarioCreate, ScenarioRead, StopRead
from app.services.scenarios import ScenarioService

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get("", response_model=list[ScenarioRead])
async def list_scenarios(session: DatabaseSession) -> list[ScenarioRead]:
    return await ScenarioService(session).list()


@router.get("/demo", response_model=ScenarioRead)
async def get_demo_scenario(session: DatabaseSession) -> ScenarioRead:
    return await ScenarioService(session).get_demo()


@router.post("", response_model=ScenarioRead, status_code=status.HTTP_201_CREATED)
async def create_scenario(payload: ScenarioCreate, session: DatabaseSession) -> ScenarioRead:
    return await ScenarioService(session).create(payload)


@router.get("/{scenario_id}", response_model=ScenarioRead)
async def get_scenario(scenario_id: uuid.UUID, session: DatabaseSession) -> ScenarioRead:
    return await ScenarioService(session).get(scenario_id)


@router.get("/{scenario_id}/stops", response_model=list[StopRead])
async def get_scenario_stops(scenario_id: uuid.UUID, session: DatabaseSession) -> list[StopRead]:
    return await ScenarioService(session).stops(scenario_id)


@router.get("/{scenario_id}/map", response_model=MapPayload)
async def get_scenario_map(scenario_id: uuid.UUID, session: DatabaseSession) -> MapPayload:
    return await ScenarioService(session).map_data(scenario_id)


@router.post("/{scenario_id}/stops/import", response_model=ImportResult)
async def import_scenario_stops(scenario_id: uuid.UUID, session: DatabaseSession, file: UploadFile = File(...)) -> ImportResult:
    return await ScenarioService(session).import_stops(scenario_id, file)
