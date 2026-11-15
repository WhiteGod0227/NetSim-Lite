from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Annotated, Literal
from pydantic import StringConstraints
from .core import route, subnet

app = FastAPI(title='NetSim Lite')
app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:5173', 'http://127.0.0.1:5173'], allow_methods=['*'], allow_headers=['*'])
router = APIRouter()

DeviceId = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Node(BaseModel):
    id: DeviceId
    label: str = ''
    ip: str | None = None
    kind: Literal['pc', 'router', 'switch'] = 'router'


class Link(BaseModel):
    source: DeviceId
    target: DeviceId
    cost: float = Field(default=1, ge=0, allow_inf_nan=False, strict=True)
    enabled: bool = Field(default=True, strict=True)


class RouteRequest(BaseModel):
    nodes: list[Node]
    links: list[Link]
    source: DeviceId
    destination: DeviceId


class SubnetRequest(BaseModel):
    cidr: str


@router.get('/api/health')
def health():
    return {'status': 'ok'}


@router.post('/api/route')
def calculate_route(request: RouteRequest):
    try:
        return route([n.model_dump() for n in request.nodes], [e.model_dump() for e in request.links], request.source, request.destination)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post('/api/simulate')
def simulate(request: RouteRequest):
    result = calculate_route(request)
    path = result['path']
    events = [{'type': 'created', 'node': request.source}]
    events += [{'type': 'forwarded', 'source': a, 'destination': b} for a, b in zip(path, path[1:])]
    events.append({'type': 'delivered' if result['reachable'] else 'unreachable', 'node': request.destination})
    return {**result, 'events': events}


@router.post('/api/subnet')
def calculate_subnet(request: SubnetRequest):
    try:
        return subnet(request.cidr)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


app.include_router(router)
