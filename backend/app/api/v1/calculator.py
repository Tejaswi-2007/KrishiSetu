"""Net proceeds calculator API endpoint."""
from decimal import Decimal, ROUND_HALF_UP
from fastapi import APIRouter
from app.schemas.market_price import NetProceedsInput, NetProceedsResult

router = APIRouter()


@router.post("/net-proceeds", response_model=NetProceedsResult)
def calculate_net_proceeds(data: NetProceedsInput):
    """Calculate estimated net proceeds from a sale.

    This calculator estimates the amount a seller would receive after
    deducting known selling-related costs. It does NOT include farming
    or cultivation expenses, so the result is not farming profit.
    """
    TWO_PLACES = Decimal("0.01")

    gross = (data.rate_per_unit * data.quantity).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    transportation = data.transportation_cost or None
    loading = data.loading_unloading_cost or None
    packaging = data.packaging_cost or None
    other = data.other_costs or None

    commission_amount = None
    if data.commission_percent is not None and data.commission_percent > 0:
        commission_amount = (gross * data.commission_percent / Decimal("100")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    # Sum known deductions
    known_deductions = Decimal("0")
    unknown_items = []

    for label, val in [
        ("transportation", transportation),
        ("loading/unloading", loading),
        ("packaging", packaging),
        ("commission", commission_amount),
        ("other costs", other),
    ]:
        if val is not None:
            known_deductions += val
        else:
            unknown_items.append(label)

    total_deductions = known_deductions.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    net = (gross - total_deductions).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    if unknown_items:
        unknown_note = (
            f"The following costs are not included and are treated as unknown (not zero): "
            f"{', '.join(unknown_items)}. "
            f"Actual net proceeds may be lower. "
            f"This estimate does not include cultivation or farming expenses."
        )
    else:
        unknown_note = (
            "All disclosed selling cost categories have been provided. "
            "This estimate does not include cultivation or farming expenses."
        )

    return NetProceedsResult(
        gross_value=gross,
        transportation_cost=transportation,
        loading_unloading_cost=loading,
        packaging_cost=packaging,
        commission_amount=commission_amount,
        commission_percent=data.commission_percent,
        other_costs=other,
        other_costs_description=data.other_costs_description,
        total_deductions=total_deductions,
        estimated_net_proceeds=net,
        unknown_costs_note=unknown_note,
        currency=data.currency,
        unit=data.unit,
        quantity=data.quantity,
        rate_per_unit=data.rate_per_unit,
    )
