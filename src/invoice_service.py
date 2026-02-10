from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple


@dataclass
class LineItem:
    sku: str
    category: str
    unit_price: float
    qty: int
    fragile: bool = False

@dataclass
class Invoice:
    invoice_id: str
    customer_id: str
    country: str
    membership: str
    coupon: Optional[str]
    items: List[LineItem]

class InvoiceService:
    def __init__(self) -> None:
        self._coupon_rate: Dict[str, float] = {
            "WELCOME10": 0.10,
            "VIP20": 0.20,
            "STUDENT5": 0.05
        }

    def _validate(self, inv: Invoice) -> List[str]:
        problems: List[str] = []
        if inv is None:
            problems.append("Invoice is missing")
            return problems
        if not inv.invoice_id:
            problems.append("Missing invoice_id")
        if not inv.customer_id:
            problems.append("Missing customer_id")
        if not inv.items:
            problems.append("Invoice must contain items")
        for it in inv.items:
            if not it.sku:
                problems.append("Item sku is missing")
            if it.qty <= 0:
                problems.append(f"Invalid qty for {it.sku}")
            if it.unit_price < 0:
                problems.append(f"Invalid price for {it.sku}")
            if it.category not in ("book", "food", "electronics", "other"):
                problems.append(f"Unknown category for {it.sku}")
        return problems

    def _calculate_subtotal_and_fragile_fee(self, items: List[LineItem]) -> Tuple[float, float]:
        subtotal = 0.0
        fragile_fee = 0.0
        for it in items:
            line = it.unit_price * it.qty
            subtotal += line
            if it.fragile:
                fragile_fee += 5.0 * it.qty
        return subtotal, fragile_fee

    def _calculate_shipping(self, country: str, subtotal: float) -> float:
        shipping_rates: Dict[str, Tuple[float, float]] = {
            "TH": (500, 60),
            "JP": (4000, 600),
            "US": (100, 15),
        }
        if country in shipping_rates:
            threshold, base_fee = shipping_rates[country]
            if subtotal < threshold:
                return base_fee
            return 0
        if subtotal < 200:
            return 25
        return 0

    def _calculate_base_discount(self, membership: str, subtotal: float) -> float:
        if membership == "gold":
            return subtotal * 0.03
        if membership == "platinum":
            return subtotal * 0.05
        if subtotal > 3000:
            return 20
        return 0.0

    def _apply_coupon(self, coupon: Optional[str], subtotal: float) -> Tuple[float, List[str]]:
        warnings: List[str] = []
        coupon_discount = 0.0
        if coupon is not None and coupon.strip() != "":
            code = coupon.strip()
            if code in self._coupon_rate:
                coupon_discount = subtotal * self._coupon_rate[code]
            else:
                warnings.append("Unknown coupon")
        return coupon_discount, warnings

    def _calculate_tax(self, country: str, subtotal: float, discount: float) -> float:
        tax_rates: Dict[str, float] = {
            "TH": 0.07,
            "JP": 0.10,
            "US": 0.08,
        }
        rate = tax_rates.get(country, 0.05)
        return (subtotal - discount) * rate

    def compute_total(self, inv: Invoice) -> Tuple[float, List[str]]:
        warnings: List[str] = []
        problems = self._validate(inv)
        if problems:
            raise ValueError("; ".join(problems))

        subtotal, fragile_fee = self._calculate_subtotal_and_fragile_fee(inv.items)
        shipping = self._calculate_shipping(inv.country, subtotal)
        discount = self._calculate_base_discount(inv.membership, subtotal)
        coupon_discount, coupon_warnings = self._apply_coupon(inv.coupon, subtotal)
        warnings.extend(coupon_warnings)
        discount += coupon_discount
        tax = self._calculate_tax(inv.country, subtotal, discount)

        total = subtotal + shipping + fragile_fee + tax - discount
        total = max(total, 0.0)

        if subtotal > 10000 and inv.membership not in ("gold", "platinum"):
            warnings.append("Consider membership upgrade")

        return total, warnings
