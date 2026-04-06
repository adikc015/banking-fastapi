from decimal import Decimal


def calculate_emi(principal: Decimal, annual_interest_rate: Decimal, months: int) -> Decimal:
    if months <= 0:
        raise ValueError("Loan tenure must be greater than zero")

    monthly_rate = (annual_interest_rate / Decimal("100")) / Decimal("12")
    if monthly_rate == 0:
        return (principal / Decimal(months)).quantize(Decimal("0.01"))

    one_plus_r_power_n = (Decimal("1") + monthly_rate) ** months
    emi = principal * monthly_rate * one_plus_r_power_n / (one_plus_r_power_n - Decimal("1"))
    return emi.quantize(Decimal("0.01"))
