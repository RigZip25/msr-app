# backend/src/main.py
from __future__ import annotations

import os
import math
import logging
from datetime import datetime, timezone
from typing import List, Optional, Literal

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

APP_NAME = "MSR Backend"
APP_VERSION = "0.1.0"

# ---------------------------
# Logging
# ---------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
log = logging.getLogger("msr")

# ---------------------------
# FastAPI app
# ---------------------------
app = FastAPI(
    title=f"{APP_NAME} (FastAPI)",
    version=APP_VERSION,
    description=(
        "API for My Smart Road (MSR): route planning, fuel suggestions, toll & IFTA."
        " External services are mocked for now."
    ),
    contact={"name": "MSR", "url": "https://mysmartroad.com"},
)

# CORS (разреши домены фронта, позже перенесём в .env)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# Pydantic models
# ---------------------------
FuelNetwork = Literal["TA", "Pilot", "Loves", "Petro"]

class TruckSpec(BaseModel):
    make: Optional[str] = Field(None, description="e.g., Freightliner, Volvo")
    model: Optional[str] = None
    year: Optional[int] = None
    engine: Optional[str] = Field(None, description="e.g., DD15, X15")
    mpg: float = Field(..., gt=2, lt=15, description="Average MPG, e.g., 6.5–9.0")
    tank_capacity_gal: int = Field(..., gt=50, lt=500, description="Total tanks capacity")
    trailer_type: Optional[str] = Field(None, description="Dry Van, Reefer, Flatbed")
    typical_weight_lbs: Optional[int] = Field(None, description="Typical gross weight")

class Waypoint(BaseModel):
    lat: float
    lon: float
    label: Optional[str] = None

class RoutePlanRequest(BaseModel):
    origin: Waypoint
    destination: Waypoint
    waypoints: List[Waypoint] = []
    truck: TruckSpec
    preferred_networks: List[FuelNetwork] = []
    avoid_tolls: bool = False
    use_weigh_stations_layer: bool = True

class FuelStop(BaseModel):
    network: FuelNetwork
    name: str
    lat: float
    lon: float
    price_per_gal: float
    gallons_to_buy: float
    note: Optional[str] = None

class RouteLeg(BaseModel):
    from_label: str
    to_label: str
    distance_miles: float
    eta_minutes: int

class RoutePlanResponse(BaseModel):
    total_distance_miles: float
    est_fuel_gallons: float
    est_fuel_cost: float
    toll_cost_est: float
    legs: List[RouteLeg]
    suggested_fuel_stops: List[FuelStop]
    currency: str = "USD"

class IFTASummaryRequest(BaseModel):
    miles_by_state: dict[str, float]  # {"TX": 523.4, "NM": 140.2, ...}
    gallons_by_state: dict[str, float]
    period: str = Field(..., description="e.g., 2025-Q1")

class IFTASummaryResponse(BaseModel):
    period: str
    total_miles: float
    total_gallons: float
    mpg: float
    states: List[dict]

class FuelSuggestRequest(BaseModel):
    network: FuelNetwork
    route_distance_miles: float
    truck: TruckSpec

class FuelSuggestResponse(BaseModel):
    recommended_stops: List[FuelStop]
    est_total_cost: float
    notes: Optional[str] = None

# ---------------------------
# Helpers (mock)
# ---------------------------
def haversine_miles(a: Waypoint, b: Waypoint) -> float:
    """Простейшая оценка дистанции по координатам (для моков)."""
    R = 3958.8  # Earth radius in miles
    lat1, lon1 = math.radians(a.lat), math.radians(a.lon)
    lat2, lon2 = math.radians(b.lat), math.radians(b.lon)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))

def mock_fuel_price(network: FuelNetwork) -> float:
    base = {"TA": 3.95, "Pilot": 3.99, "Loves": 4.03, "Petro": 3.97}
    return base.get(network, 4.09)

# ---------------------------
# Routes
# ---------------------------
@app.get("/health")
def health():
    return {
        "status": "ok",
        "app": APP_NAME,
        "version": APP_VERSION,
        "time": datetime.now(timezone.utc).isoformat(),
    }

@app.post("/v1/route/plan", response_model=RoutePlanResponse)
def plan_route(payload: RoutePlanRequest):
    # Оценка общей дистанции: origin -> (waypoints) -> destination
    points = [payload.origin, *payload.waypoints, payload.destination]
    total_miles = sum(haversine_miles(points[i], points[i + 1]) for i in range(len(points) - 1))
    total_miles = round(total_miles * 1.1, 1)  # небольшой коэффициент реальности

    # Топливо
    gallons = round(total_miles / payload.truck.mpg, 2)

    # Простейшая стратегия топлива: 1–2 остановки в выбранных сетях
    networks = payload.preferred_networks or ["TA", "Pilot"]
    stops: List[FuelStop] = []
    remain = gallons
    for i, net in enumerate(networks[:2]):
        buy = round(min(remain, payload.truck.tank_capacity_gal * 0.5), 1)
        remain -= buy
        stops.append(
            FuelStop(
                network=net,
                name=f"{net} Station #{100+i}",
                lat=points[min(i + 1, len(points)-1)].lat,
                lon=points[min(i + 1, len(points)-1)].lon,
                price_per_gal=mock_fuel_price(net),
                gallons_to_buy=buy,
                note="Mock suggestion — replace with live pricing later.",
            )
        )
        if remain <= 0:
            break

    # Стоимость
    est_cost = round(sum(s.price_per_gal * s.gallons_to_buy for s in stops), 2)
    toll_cost = 0.0 if payload.avoid_tolls else round(total_miles * 0.03, 2)  # очень грубо

    # Леги (упрощённо)
    legs = []
    for i in range(len(points) - 1):
        d = round(haversine_miles(points[i], points[i + 1]) * 1.1, 1)
        legs.append(
            RouteLeg(
                from_label=points[i].label or f"WP{i}",
                to_label=points[i + 1].label or f"WP{i+1}",
                distance_miles=d,
                eta_minutes=int(d / 55 * 60),  # ~55 mph
            )
        )

    return RoutePlanResponse(
        total_distance_miles=total_miles,
        est_fuel_gallons=gallons,
        est_fuel_cost=est_cost,
        toll_cost_est=toll_cost,
        legs=legs,
        suggested_fuel_stops=stops,
    )

@app.post("/v1/ifta/summary", response_model=IFTASummaryResponse)
def ifta_summary(payload: IFTASummaryRequest):
    miles_total = round(sum(payload.miles_by_state.values()), 2)
    gallons_total = round(sum(payload.gallons_by_state.values()), 3)
    mpg = round(miles_total / gallons_total, 2) if gallons_total > 0 else 0.0

    states = []
    for st, miles in payload.miles_by_state.items():
        gallons = payload.gallons_by_state.get(st, 0.0)
        states.append({
            "state": st,
            "miles": round(miles, 2),
            "gallons": round(gallons, 3),
            "mpg": round((miles / gallons), 2) if gallons else None,
        })

    return IFTASummaryResponse(
        period=payload.period,
        total_miles=miles_total,
        total_gallons=gallons_total,
        mpg=mpg,
        states=states,
    )

@app.post("/v1/fuel/suggest", response_model=FuelSuggestResponse)
def fuel_suggest(payload: FuelSuggestRequest):
    price = mock_fuel_price(payload.network)
    gallons = round(payload.route_distance_miles / payload.truck.mpg, 2)
    stops = [
        FuelStop(
            network=payload.network,
            name=f"{payload.network} Suggested",
            lat=0.0,
            lon=0.0,
            price_per_gal=price,
            gallons_to_buy=min(gallons, payload.truck.tank_capacity_gal * 0.6),
            note="Mock suggestion based on average price.",
        )
    ]
    total_cost = round(sum(s.price_per_gal * s.gallons_to_buy for s in stops), 2)
    return FuelSuggestResponse(recommended_stops=stops, est_total_cost=total_cost)

# Root info
@app.get("/")
def root():
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
    }

