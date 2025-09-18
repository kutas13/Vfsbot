"""Configuration helpers for the VFS appointment automation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import yaml


@dataclass
class Credentials:
    """Login credentials for the VFS portal."""

    email: str
    password: str


@dataclass
class PreferredSlot:
    """A date/time combination the automation should target."""

    date: Optional[str] = None
    times: List[str] = field(default_factory=list)

    def matches_date(self, candidate: str) -> bool:
        if not self.date:
            return True
        return candidate.strip().lower() == self.date.strip().lower()

    def matches_time(self, candidate: str) -> bool:
        if not self.times:
            return True
        candidate_norm = candidate.strip().lower()
        return any(candidate_norm == option.strip().lower() for option in self.times)


@dataclass
class Polling:
    """Configuration for polling the appointment calendar."""

    interval_seconds: int = 60
    max_attempts: int = 100


@dataclass
class AppointmentPreferences:
    """User preferences for the appointment search."""

    center: str
    visa_category: str
    sub_category: str
    applicants: int = 1
    preferred_slots: List[PreferredSlot] = field(default_factory=list)
    polling: Polling = field(default_factory=Polling)


@dataclass
class Applicant:
    """Passport holder details required by the booking form."""

    first_name: str
    last_name: str
    passport_number: str
    passport_issue_date: str
    passport_expiry_date: str
    date_of_birth: str
    nationality: str
    phone_number: str
    email: Optional[str] = None
    additional_fields: Dict[str, str] = field(default_factory=dict)


@dataclass
class Selector:
    """Locator description for a DOM element."""

    by: str
    value: str
    attribute: Optional[str] = None


@dataclass
class Site:
    """URLs for the VFS portal."""

    login_url: str
    dashboard_url: Optional[str] = None
    appointment_url: Optional[str] = None


@dataclass
class WebDriverSettings:
    """Browser configuration."""

    browser: str = "chrome"
    headless: bool = True
    executable_path: Optional[str] = None


@dataclass
class Config:
    """Root configuration object for the automation."""

    site: Site
    credentials: Credentials
    applicant: Applicant
    appointment: AppointmentPreferences
    selectors: Dict[str, Selector]
    webdriver: WebDriverSettings = field(default_factory=WebDriverSettings)


def _load_selectors(data: Dict[str, Dict[str, str]]) -> Dict[str, Selector]:
    selectors: Dict[str, Selector] = {}
    for name, entry in data.items():
        selectors[name] = Selector(
            by=entry["by"],
            value=entry["value"],
            attribute=entry.get("attribute"),
        )
    return selectors


def _load_preferred_slots(slots: Optional[Iterable[Dict[str, object]]]) -> List[PreferredSlot]:
    if not slots:
        return []
    result: List[PreferredSlot] = []
    for slot in slots:
        result.append(
            PreferredSlot(
                date=slot.get("date"),
                times=list(slot.get("times", [])),
            )
        )
    return result


def load_config(path: str | Path) -> Config:
    """Load the automation configuration from a YAML file."""

    with Path(path).open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)

    site = Site(
        login_url=raw["site"]["login_url"],
        dashboard_url=raw["site"].get("dashboard_url"),
        appointment_url=raw["site"].get("appointment_url"),
    )
    credentials = Credentials(**raw["credentials"])
    applicant = Applicant(
        first_name=raw["applicant"]["first_name"],
        last_name=raw["applicant"]["last_name"],
        passport_number=raw["applicant"]["passport_number"],
        passport_issue_date=raw["applicant"]["passport_issue_date"],
        passport_expiry_date=raw["applicant"]["passport_expiry_date"],
        date_of_birth=raw["applicant"]["date_of_birth"],
        nationality=raw["applicant"]["nationality"],
        phone_number=raw["applicant"]["phone_number"],
        email=raw["applicant"].get("email"),
        additional_fields=raw["applicant"].get("additional_fields", {}),
    )
    polling = Polling(
        interval_seconds=raw["appointment"].get("polling", {}).get("interval_seconds", 60),
        max_attempts=raw["appointment"].get("polling", {}).get("max_attempts", 100),
    )
    appointment = AppointmentPreferences(
        center=raw["appointment"]["center"],
        visa_category=raw["appointment"]["visa_category"],
        sub_category=raw["appointment"]["sub_category"],
        applicants=raw["appointment"].get("applicants", 1),
        preferred_slots=_load_preferred_slots(raw["appointment"].get("preferred_slots")),
        polling=polling,
    )
    selectors = _load_selectors(raw.get("selectors", {}))
    webdriver = WebDriverSettings(**raw.get("webdriver", {}))

    return Config(
        site=site,
        credentials=credentials,
        applicant=applicant,
        appointment=appointment,
        selectors=selectors,
        webdriver=webdriver,
    )
