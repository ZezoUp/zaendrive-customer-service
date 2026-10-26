"""SQLite data and four tools for the fictional ZaenDrive rental desk.

The tools return dictionaries. The language model writes the customer-facing text.
This module uses only Python's standard library and can be tested without an API key.
"""

import csv
import json
import re
import sqlite3
import unicodedata
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_DB = ROOT / "zaendrive.db"


def normalize(text):
    text = unicodedata.normalize("NFKC", str(text)).casefold()
    return " ".join(re.sub(r"[^\w]+", " ", text).split())


def money(value):
    return str(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def initialize_database(db_path=DEFAULT_DB, data_dir=ROOT):
    """Rebuild the two demo tables from CSV at each application startup."""
    data_dir = Path(data_dir)
    with (data_dir / "rental_info.csv").open(encoding="utf-8-sig", newline="") as f:
        info = list(csv.DictReader(f))
    with (data_dir / "vehicles.csv").open(encoding="utf-8-sig", newline="") as f:
        vehicles = list(csv.DictReader(f))
    if len(info) < 8 or len(vehicles) < 15:
        raise ValueError("The assignment needs at least 8 information topics and 15 vehicles.")

    # Read and validate everything before replacing existing database contents.
    records = []
    for row in vehicles:
        rate = Decimal(row["daily_rate_eur"])
        if not rate.is_finite() or rate <= 0 or row["available"] not in {"0", "1"}:
            raise ValueError("Invalid vehicle price or availability in vehicles.csv.")
        search_text = normalize(" ".join(row[k] for k in
            ("vehicle_id", "name", "category", "fuel_type", "transmission", "aliases")))
        records.append((row["vehicle_id"], row["name"], row["category"],
                        money(rate), int(row["seats"]), row["transmission"],
                        row["fuel_type"], int(row["available"]), row["aliases"], search_text))
    policy = json.loads(next(r["content"] for r in info if r["topic"] == "rental_rates"))
    for key in ("discount_percent", "discount_min_days", "included_km_per_day",
                "extra_km_eur", "deposit_eur", "extras_per_day_eur"):
        if key not in policy:
            raise ValueError(f"Missing rental_rates setting: {key}")

    with sqlite3.connect(db_path) as con:
        con.execute("BEGIN")
        con.execute("DROP TABLE IF EXISTS rental_info")
        con.execute("DROP TABLE IF EXISTS vehicles")
        con.execute("CREATE TABLE rental_info (topic TEXT PRIMARY KEY, content TEXT NOT NULL)")
        con.execute("""CREATE TABLE vehicles (
            vehicle_id TEXT PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL,
            daily_rate_eur TEXT NOT NULL, seats INTEGER NOT NULL,
            transmission TEXT NOT NULL, fuel_type TEXT NOT NULL,
            available INTEGER NOT NULL CHECK (available IN (0,1)),
            aliases TEXT NOT NULL, search_text TEXT NOT NULL)""")
        con.executemany("INSERT INTO rental_info VALUES (?, ?)",
                        [(r["topic"], r["content"]) for r in info])
        con.executemany("INSERT INTO vehicles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", records)
    return {"rental_info": len(info), "vehicles": len(vehicles)}


class RentalTools:
    def __init__(self, db_path=DEFAULT_DB):
        self.db_path = Path(db_path)
        # Explicit allowlist: model output is never eval'ed or used as SQL.
        self.registry = {
            "get_rental_info": self.get_rental_info,
            "search_vehicles": self.search_vehicles,
            "calculate_rental": self.calculate_rental,
            "transfer_to_staff": self.transfer_to_staff,
        }

    def query(self, sql, parameters=()):
        with sqlite3.connect(self.db_path) as con:
            con.row_factory = sqlite3.Row
            return [dict(row) for row in con.execute(sql, parameters).fetchall()]

    def get_rental_info(self, topic):
        if not isinstance(topic, str) or not topic.strip() or len(topic) > 160:
            return {"status": "invalid_argument", "field": "topic"}
        aliases = {
            "hours": "opening_hours", "opening hours": "opening_hours",
            "öffnungszeiten": "opening_hours", "location": "address",
            "payment methods": "payment", "bezahlung": "payment",
            "license": "driver_requirements", "minimum age": "driver_requirements",
            "age": "driver_requirements", "documents": "required_documents",
            "deposit": "rental_rates", "kaution": "rental_rates",
            "mileage": "rental_rates", "extras": "rental_rates",
            "discount": "rental_rates", "weekly discount": "rental_rates",
            "pricing": "rental_rates", "fuel": "fuel_and_charging",
            "charging": "fuel_and_charging", "booking": "reservations",
            "parking": "pickup_and_parking", "insurance": "insurance",
        }
        key = aliases.get(normalize(topic), normalize(topic).replace(" ", "_"))
        rows = self.query("SELECT topic, content FROM rental_info WHERE topic = ?", (key,))
        if not rows:
            return {"status": "not_found", "requested_topic": topic,
                    "available_topics": [r["topic"] for r in self.query(
                        "SELECT topic FROM rental_info ORDER BY topic")]}
        row = rows[0]
        if row["topic"] == "rental_rates":
            row["content"] = json.loads(row["content"])
        return {"status": "ok", **row}

    @staticmethod
    def public_vehicle(row):
        return {k: bool(v) if k == "available" else v for k, v in row.items()
                if k not in {"search_text", "aliases"}}

    def search_vehicles(self, keyword="", available_only=False):
        if not isinstance(keyword, str) or len(keyword) > 160 or type(available_only) is not bool:
            return {"status": "invalid_argument", "fields": ["keyword", "available_only"]}
        terms = normalize(keyword).split()
        clauses = ["instr(search_text, ?) > 0" for _ in terms]
        if available_only:
            clauses.append("available = 1")
        sql = "SELECT * FROM vehicles"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY CAST(daily_rate_eur AS REAL), name"
        rows = self.query(sql, terms)
        return {"status": "ok" if rows else "not_found", "keyword": keyword,
                "count": len(rows), "currency": "EUR", "availability_type": "demo_snapshot",
                "vehicles": [self.public_vehicle(r) for r in rows]}

    def resolve_vehicle(self, name):
        key = normalize(name)
        all_rows = self.query("SELECT * FROM vehicles")
        exact = [r for r in all_rows if key in {
            normalize(r["vehicle_id"]), normalize(r["name"]),
            *[normalize(alias) for alias in r["aliases"].split("|") if alias.strip()]}
        ]
        if exact:
            return exact
        # A partial name is allowed; multiple matches must be clarified.
        terms = key.split()
        return [r for r in all_rows if terms and all(t in r["search_text"] for t in terms)]

    def calculate_rental(self, vehicle, days, gps=False, child_seat=False,
                         additional_driver=False, total_km=None):
        if not isinstance(vehicle, str) or not vehicle.strip() or len(vehicle) > 160:
            return {"status": "invalid_argument", "field": "vehicle"}
        if type(days) is not int or not 1 <= days <= 30:
            return {"status": "invalid_argument", "field": "days", "allowed_range": [1, 30]}
        if any(type(v) is not bool for v in (gps, child_seat, additional_driver)):
            return {"status": "invalid_argument", "field": "extras", "expected": "booleans"}
        if total_km is not None and (type(total_km) is not int or not 0 <= total_km <= 100000):
            return {"status": "invalid_argument", "field": "total_km"}

        matches = self.resolve_vehicle(vehicle)
        if not matches:
            return {"status": "not_found", "vehicle": vehicle}
        if len(matches) > 1:
            return {"status": "ambiguous", "vehicle": vehicle,
                    "candidates": [r["name"] for r in matches]}
        car = matches[0]
        if not car["available"]:
            return {"status": "unavailable", "vehicle": car["name"], "quote_created": False}
        policy = self.get_rental_info("rental_rates")["content"]
        daily_rate = Decimal(car["daily_rate_eur"])
        base = daily_rate * days
        discount_percent = policy["discount_percent"] if days >= policy["discount_min_days"] else 0
        discount = (base * Decimal(str(discount_percent)) / 100).quantize(Decimal("0.01"))
        selected = {"gps": gps, "child_seat": child_seat, "additional_driver": additional_driver}
        extras = {k: money(Decimal(policy["extras_per_day_eur"][k]) * days)
                  for k, enabled in selected.items() if enabled}
        extra_total = sum((Decimal(v) for v in extras.values()), Decimal("0"))
        included_km = policy["included_km_per_day"] * days
        extra_km = max(0, total_km - included_km) if total_km is not None else 0
        mileage_cost = Decimal(policy["extra_km_eur"]) * extra_km
        total = base - discount + extra_total + mileage_cost
        return {
            "status": "ok", "quote_only": True, "currency": "EUR",
            "vehicle": car["name"], "days": days, "daily_rate": money(daily_rate),
            "base_rental": money(base), "discount_percent": discount_percent,
            "discount_amount": money(discount), "extras": extras, "extras_total": money(extra_total),
            "included_km": included_km, "estimated_total_km": total_km,
            "extra_km": extra_km, "extra_km_cost": money(mileage_cost),
            "mileage_estimate_provided": total_km is not None,
            "rental_total": money(total), "refundable_deposit_separate": money(policy["deposit_eur"]),
            "tax_included": policy["tax_included"],
            "excluded": ["refundable deposit", "fuel or charging", "unreported excess mileage",
                         "damage charges", "late-return charges"],
        }

    def transfer_to_staff(self, reason):
        if not isinstance(reason, str) or not reason.strip() or len(reason) > 500:
            return {"status": "invalid_argument", "field": "reason"}
        contact = self.get_rental_info("contact")
        return {"status": "referral_only", "reason": reason, "contact": contact.get("content"),
                "demo_only": True, "message_sent": False, "live_transfer_performed": False}

    def dispatch(self, name, arguments):
        if name not in self.registry:
            return {"status": "unknown_tool", "tool": name}
        if not isinstance(arguments, dict):
            return {"status": "invalid_arguments", "expected": "JSON object"}
        try:
            return self.registry[name](**arguments)
        except TypeError:
            return {"status": "invalid_arguments", "tool": name}


def schema(name, description, properties, required=()):
    return {"type": "function", "function": {"name": name, "description": description,
        "parameters": {"type": "object", "properties": properties,
                       "required": list(required), "additionalProperties": False}}}


TOOL_SCHEMAS = [
    schema("get_rental_info", "Read a ZaenDrive policy or information topic. Use for hours, address, "
           "payment, driver_requirements, required_documents, rental_rates (discounts, mileage, "
           "deposit, extras), fuel_and_charging, cancellation, late_return, reservations, "
           "availability, pickup_and_parking, insurance, contact. Also try the requested topic "
           "when a policy is missing; not_found must lead to transfer_to_staff.",
           {"topic": {"type": "string", "description": "Topic key, e.g. opening_hours or pets."}}, ["topic"]),
    schema("search_vehicles", "Find vehicles, their daily rates, seats and demo availability. "
           "Use a short model name, brand, category or fuel type, e.g. Corolla, SUV or electric. "
           "Use an empty keyword to list all. No calendar or real reservations are available.",
           {"keyword": {"type": "string"}, "available_only": {"type": "boolean"}}),
    schema("calculate_rental", "Calculate every rental quote in Python, including any duration, "
           "extras, weekly discount and excess-mileage charge. Use this for ALL rental cost maths; "
           "never multiply prices yourself. Vehicle and whole rental days are required. "
           "Set only explicitly requested extras. total_km is the estimated TOTAL distance for the "
           "whole rental, not distance per day. Omit it if unspecified. Ambiguous vehicles need clarification.",
           {"vehicle": {"type": "string"}, "days": {"type": "integer", "minimum": 1, "maximum": 30},
            "gps": {"type": "boolean"}, "child_seat": {"type": "boolean"},
            "additional_driver": {"type": "boolean"},
            "total_km": {"type": "integer", "minimum": 0, "maximum": 100000}}, ["vehicle", "days"]),
    schema("transfer_to_staff", "Provide the demo staff contact for complaints, missing information, "
           "requests for a person, real bookings or date-specific availability. This only returns "
           "contact details: it does NOT send a message, create a ticket or connect a live person.",
           {"reason": {"type": "string", "description": "Brief reason for the handover."}}, ["reason"]),
]
