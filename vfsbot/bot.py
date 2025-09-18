"""Selenium automation for booking VFS France appointments."""

from __future__ import annotations

import logging
import time
from typing import Iterable, Optional

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver import ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait

from .config import Config, PreferredSlot, Selector

LOGGER = logging.getLogger(__name__)


class BookingError(RuntimeError):
    """Raised when the automation cannot complete the booking."""


class VFSFranceBot:
    """High level orchestration for the VFS booking flow."""

    def __init__(self, config: Config, logger: Optional[logging.Logger] = None):
        self.config = config
        self.logger = logger or LOGGER
        self.driver: Optional[WebDriver] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def __enter__(self) -> "VFSFranceBot":
        self.driver = self._create_driver()
        return self

    def __exit__(self, exc_type, exc, exc_tb) -> None:  # type: ignore[override]
        if self.driver:
            self.driver.quit()
            self.driver = None

    # ------------------------------------------------------------------
    def run(self) -> None:
        """Execute the full booking workflow."""

        if self.driver is not None:
            raise BookingError("Driver already active; use a new bot instance")

        with self:
            assert self.driver  # for type checkers
            self._perform_booking()

    # ------------------------------------------------------------------
    def _perform_booking(self) -> None:
        self.logger.info("Signing in to VFS portal")
        self._login()
        self.logger.info("Navigating to appointment page")
        self._open_appointment_page()
        self.logger.info("Applying appointment preferences")
        self._apply_preferences()
        self.logger.info("Monitoring calendar for available slots")
        if not self._monitor_calendar():
            raise BookingError("Preferred appointment slot not found within polling window")
        self.logger.info("Appointment workflow finished")

    # ------------------------------------------------------------------
    def _create_driver(self) -> WebDriver:
        settings = self.config.webdriver
        browser = settings.browser.lower()
        if browser != "chrome":
            raise BookingError(f"Unsupported browser '{settings.browser}'. Only Chrome is supported currently.")

        options = ChromeOptions()
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1280,1024")
        if settings.headless:
            options.add_argument("--headless=new")

        service = ChromeService(executable_path=settings.executable_path) if settings.executable_path else ChromeService()
        try:
            driver = webdriver.Chrome(service=service, options=options)
        except WebDriverException as exc:
            raise BookingError(f"Unable to start Chrome driver: {exc}") from exc

        driver.implicitly_wait(2)
        return driver

    # ------------------------------------------------------------------
    # Login and navigation helpers
    # ------------------------------------------------------------------
    def _login(self) -> None:
        assert self.driver
        self.driver.get(self.config.site.login_url)
        self._fill("login_email", self.config.credentials.email)
        self._fill("login_password", self.config.credentials.password)
        self._click("login_submit")
        if "dashboard_ready" in self.config.selectors:
            self._wait_visible("dashboard_ready", timeout=30)

    def _open_appointment_page(self) -> None:
        assert self.driver
        if self.config.site.appointment_url:
            self.driver.get(self.config.site.appointment_url)
        elif "appointment_nav" in self.config.selectors:
            self._click("appointment_nav")
        else:
            raise BookingError("No appointment URL or navigation selector provided in configuration")

    # ------------------------------------------------------------------
    def _apply_preferences(self) -> None:
        preferences = self.config.appointment
        self._select_dropdown("center_select", preferences.center)
        self._select_dropdown("visa_category_select", preferences.visa_category)
        self._select_dropdown("sub_category_select", preferences.sub_category)
        if "applicants_input" in self.config.selectors:
            self._fill("applicants_input", str(preferences.applicants))
        if "preferences_submit" in self.config.selectors:
            self._click("preferences_submit")

    # ------------------------------------------------------------------
    def _monitor_calendar(self) -> bool:
        attempts = 0
        polling = self.config.appointment.polling
        while attempts < polling.max_attempts:
            attempts += 1
            self.logger.info("Polling for availability (attempt %s/%s)", attempts, polling.max_attempts)
            if self._attempt_booking(self.config.appointment.preferred_slots):
                return True
            self.logger.debug("No matching slot found, waiting %s seconds", polling.interval_seconds)
            time.sleep(polling.interval_seconds)
            assert self.driver
            self.driver.refresh()
        return False

    # ------------------------------------------------------------------
    def _attempt_booking(self, preferred_slots: Iterable[PreferredSlot]) -> bool:
        # If no preferences defined, fall back to any available slot
        slots = list(preferred_slots) or [PreferredSlot()]
        available_dates = self._find_elements("available_date", required=False)
        if not available_dates:
            self.logger.debug("Calendar contains no selectable dates")
            return False

        for date_element in available_dates:
            date_label = self._extract_value(date_element, "available_date")
            for preference in slots:
                if not preference.matches_date(date_label):
                    continue
                self.logger.info("Selecting date %s", date_label)
                date_element.click()
                self._wait_visible("times_container", timeout=15, required=False)
                for time_element in self._find_elements("available_time", required=False):
                    time_label = self._extract_value(time_element, "available_time")
                    if not preference.matches_time(time_label):
                        continue
                    self.logger.info("Attempting booking for %s %s", date_label, time_label)
                    time_element.click()
                    if "time_confirm" in self.config.selectors:
                        self._click("time_confirm")
                    self._fill_applicant_details()
                    if "terms_checkbox" in self.config.selectors:
                        self._set_checkbox("terms_checkbox", True)
                    if "final_submit" in self.config.selectors:
                        self._click("final_submit")
                    return True
        return False

    # ------------------------------------------------------------------
    # Form helpers
    # ------------------------------------------------------------------
    def _fill_applicant_details(self) -> None:
        applicant = self.config.applicant
        mapping = {
            "applicant_first_name": applicant.first_name,
            "applicant_last_name": applicant.last_name,
            "applicant_passport_number": applicant.passport_number,
            "applicant_passport_issue_date": applicant.passport_issue_date,
            "applicant_passport_expiry_date": applicant.passport_expiry_date,
            "applicant_date_of_birth": applicant.date_of_birth,
            "applicant_nationality": applicant.nationality,
            "applicant_phone_number": applicant.phone_number,
        }
        if applicant.email:
            mapping["applicant_email"] = applicant.email

        for selector_key, value in mapping.items():
            if selector_key in self.config.selectors:
                self._fill(selector_key, value)

        for key, value in applicant.additional_fields.items():
            if key in self.config.selectors:
                self._fill(key, value)

    # ------------------------------------------------------------------
    # Selenium primitives
    # ------------------------------------------------------------------
    def _find_elements(self, selector_key: str, *, required: bool = True):
        assert self.driver
        selector = self._get_selector(selector_key)
        elements = self.driver.find_elements(self._resolve_by(selector.by), selector.value)
        if required and not elements:
            raise BookingError(f"No elements found for selector '{selector_key}'")
        return elements

    def _find_element(self, selector_key: str):
        elements = self._find_elements(selector_key)
        return elements[0]

    def _wait_visible(self, selector_key: str, *, timeout: int = 15, required: bool = True):
        assert self.driver
        selector = self._get_selector(selector_key)
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((self._resolve_by(selector.by), selector.value))
            )
        except TimeoutException as exc:
            if required:
                raise BookingError(f"Timeout waiting for selector '{selector_key}' to be visible") from exc
            self.logger.debug("Selector '%s' did not become visible within %s seconds", selector_key, timeout)
            return None

    def _click(self, selector_key: str) -> None:
        element = self._wait_clickable(selector_key)
        element.click()

    def _wait_clickable(self, selector_key: str, timeout: int = 15):
        assert self.driver
        selector = self._get_selector(selector_key)
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((self._resolve_by(selector.by), selector.value))
            )
        except TimeoutException as exc:
            raise BookingError(f"Timeout waiting for selector '{selector_key}' to be clickable") from exc

    def _fill(self, selector_key: str, value: str) -> None:
        element = self._wait_visible(selector_key)
        element.clear()
        element.send_keys(value)

    def _set_checkbox(self, selector_key: str, checked: bool) -> None:
        element = self._wait_clickable(selector_key)
        is_selected = element.is_selected()
        if checked != is_selected:
            element.click()

    def _select_dropdown(self, selector_key: str, visible_text: str) -> None:
        element = self._wait_visible(selector_key)
        try:
            Select(element).select_by_visible_text(visible_text)
        except Exception as exc:  # noqa: BLE001 - we want to surface the selector in the error
            raise BookingError(
                f"Unable to select '{visible_text}' for selector '{selector_key}': {exc}"
            ) from exc

    def _extract_value(self, element, selector_key: str) -> str:
        selector = self._get_selector(selector_key)
        if selector.attribute:
            value = element.get_attribute(selector.attribute)
            if value:
                return value.strip()
        return element.text.strip()

    def _get_selector(self, selector_key: str) -> Selector:
        try:
            return self.config.selectors[selector_key]
        except KeyError as exc:  # noqa: BLE001
            raise BookingError(f"Selector '{selector_key}' is missing from configuration") from exc

    @staticmethod
    def _resolve_by(method: str):
        lookup = {
            "css": By.CSS_SELECTOR,
            "xpath": By.XPATH,
            "id": By.ID,
            "name": By.NAME,
            "link_text": By.LINK_TEXT,
            "partial_link_text": By.PARTIAL_LINK_TEXT,
            "tag": By.TAG_NAME,
            "class": By.CLASS_NAME,
        }
        key = method.lower()
        if key not in lookup:
            raise BookingError(f"Unsupported selector strategy '{method}'")
        return lookup[key]
