"""Dashboard statistics routes matching API spec."""

import random
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models import (
    ActivityLog,
    Document,
    File,
    Team,
    User,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# ============== Schemas ==============
class StatsResponse(BaseModel):
    totalUsers: int
    totalRevenue: float
    totalOrders: int
    conversionRate: float
    userGrowth: float
    revenueGrowth: float
    orderGrowth: float


class VisitData(BaseModel):
    date: str
    visits: int
    pageViews: int


class VisitsResponse(BaseModel):
    data: list[VisitData]


class SalesData(BaseModel):
    month: str
    sales: float
    orders: int


class SalesResponse(BaseModel):
    data: list[SalesData]


class ProductData(BaseModel):
    id: str
    name: str
    sales: int
    revenue: float


class ProductsResponse(BaseModel):
    data: list[ProductData]


class OrderData(BaseModel):
    id: str
    customer: str
    amount: float
    status: str
    date: str


class OrdersResponse(BaseModel):
    data: list[OrderData]


class ActivityData(BaseModel):
    id: str
    user: str
    action: str
    target: str
    timestamp: datetime


class ActivitiesResponse(BaseModel):
    data: list[ActivityData]


class PieData(BaseModel):
    name: str
    value: int
    color: str


class PieResponse(BaseModel):
    data: list[PieData]


class TaskData(BaseModel):
    id: str
    title: str
    status: str
    priority: str
    dueDate: str | None = None


class TasksResponse(BaseModel):
    data: list[TaskData]
    stats: dict[str, int]


class SystemInfo(BaseModel):
    cpu: float
    memory: float
    disk: float
    uptime: int


class OverviewResponse(BaseModel):
    system: SystemInfo
    stats: dict[str, int]


# ============== Routes ==============
@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> StatsResponse:
    """Get dashboard statistics."""
    total_users = db.query(func.count(User.id)).scalar() or 0

    # Mock data for demo purposes
    return StatsResponse(
        totalUsers=total_users,
        totalRevenue=125680.50,
        totalOrders=1234,
        conversionRate=3.24,
        userGrowth=12.5,
        revenueGrowth=8.3,
        orderGrowth=15.2,
    )


@router.get("/visits", response_model=VisitsResponse)
async def get_visits(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> VisitsResponse:
    """Get visit trends (7 days)."""
    data = []
    today = datetime.now()

    for i in range(7):
        date = today - timedelta(days=6 - i)
        data.append(
            VisitData(
                date=date.strftime("%Y-%m-%d"),
                visits=random.randint(500, 2000),
                pageViews=random.randint(1500, 5000),
            )
        )

    return VisitsResponse(data=data)


@router.get("/sales", response_model=SalesResponse)
async def get_sales(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> SalesResponse:
    """Get sales trends (6 months)."""
    months = ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    data = []

    for month in months:
        data.append(
            SalesData(
                month=month,
                sales=round(random.uniform(10000, 50000), 2),
                orders=random.randint(100, 500),
            )
        )

    return SalesResponse(data=data)


@router.get("/products", response_model=ProductsResponse)
async def get_products(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> ProductsResponse:
    """Get top products."""
    products = [
        ProductData(id="1", name="Product A", sales=1234, revenue=12340.00),
        ProductData(id="2", name="Product B", sales=987, revenue=9870.00),
        ProductData(id="3", name="Product C", sales=756, revenue=7560.00),
        ProductData(id="4", name="Product D", sales=543, revenue=5430.00),
        ProductData(id="5", name="Product E", sales=321, revenue=3210.00),
    ]

    return ProductsResponse(data=products)


@router.get("/orders", response_model=OrdersResponse)
async def get_orders(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> OrdersResponse:
    """Get recent orders."""
    statuses = ["completed", "pending", "processing", "cancelled"]
    orders = []

    for i in range(5):
        orders.append(
            OrderData(
                id=f"ORD-{1000 + i}",
                customer=f"Customer {i + 1}",
                amount=round(random.uniform(50, 500), 2),
                status=random.choice(statuses),
                date=(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
            )
        )

    return OrdersResponse(data=orders)


@router.get("/activities", response_model=ActivitiesResponse)
async def get_activities(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> ActivitiesResponse:
    """Get recent activities."""
    # Try to get real activity logs
    activities = db.query(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(10).all()

    if activities:
        data = [
            ActivityData(
                id=a.id,
                user=a.user_id,
                action=a.action,
                target=a.entity_type,
                timestamp=a.created_at,
            )
            for a in activities
        ]
    else:
        # Mock data
        actions = ["created", "updated", "deleted", "viewed"]
        targets = ["document", "file", "user", "team"]
        data = []

        for i in range(5):
            data.append(
                ActivityData(
                    id=f"act_{i}",
                    user=current_user.name,
                    action=random.choice(actions),
                    target=random.choice(targets),
                    timestamp=datetime.now() - timedelta(hours=i),
                )
            )

    return ActivitiesResponse(data=data)


@router.get("/pie", response_model=PieResponse)
async def get_pie_data(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> PieResponse:
    """Get pie chart data (category distribution)."""
    data = [
        PieData(name="Documents", value=35, color="#4F46E5"),
        PieData(name="Files", value=25, color="#10B981"),
        PieData(name="Images", value=20, color="#F59E0B"),
        PieData(name="Videos", value=12, color="#EF4444"),
        PieData(name="Others", value=8, color="#6B7280"),
    ]

    return PieResponse(data=data)


@router.get("/tasks", response_model=TasksResponse)
async def get_tasks(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> TasksResponse:
    """Get task list and statistics."""
    # Mock task data
    tasks = [
        TaskData(
            id="1",
            title="Review documentation",
            status="completed",
            priority="high",
            dueDate="2024-12-10",
        ),
        TaskData(
            id="2",
            title="Update API endpoints",
            status="in_progress",
            priority="medium",
            dueDate="2024-12-15",
        ),
        TaskData(
            id="3",
            title="Fix authentication bug",
            status="pending",
            priority="high",
            dueDate="2024-12-08",
        ),
        TaskData(
            id="4",
            title="Write unit tests",
            status="pending",
            priority="low",
            dueDate="2024-12-20",
        ),
    ]

    stats = {
        "total": len(tasks),
        "completed": sum(1 for t in tasks if t.status == "completed"),
        "in_progress": sum(1 for t in tasks if t.status == "in_progress"),
        "pending": sum(1 for t in tasks if t.status == "pending"),
    }

    return TasksResponse(data=tasks, stats=stats)


@router.get("/overview", response_model=OverviewResponse)
async def get_overview(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> OverviewResponse:
    """Get system overview."""
    # Get real counts from database
    user_count = db.query(func.count(User.id)).scalar() or 0
    document_count = db.query(func.count(Document.id)).scalar() or 0
    file_count = db.query(func.count(File.id)).scalar() or 0
    team_count = db.query(func.count(Team.id)).scalar() or 0

    return OverviewResponse(
        system=SystemInfo(
            cpu=round(random.uniform(20, 60), 1),
            memory=round(random.uniform(40, 80), 1),
            disk=round(random.uniform(30, 70), 1),
            uptime=random.randint(86400, 864000),  # 1-10 days in seconds
        ),
        stats={
            "users": user_count,
            "documents": document_count,
            "files": file_count,
            "teams": team_count,
        },
    )
