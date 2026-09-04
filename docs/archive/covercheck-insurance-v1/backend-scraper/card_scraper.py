"""Scrape every SingSaver credit card into the simplified Supabase schema.

Each product becomes one ``credit_cards`` row. Variable cashback/miles/points
fields are stored in ``benefits`` and the complete parsed source is retained in
``raw_details``. No browser is required because the pages are server-rendered.

Expected in backend/.env:
    SUPABASE_URL=https://<project-ref>.supabase.co
    SUPABASE_SERVICE_ROLE_KEY=<service-role JWT or sb_secret_ key>
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import logging
import os
import re
import sys
import time
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qs, quote, unquote, urljoin, urlsplit

import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


LISTING_URL = "https://www.singsaver.com.sg/credit-card/all"
BASE_URL = "https://www.singsaver.com.sg"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36"
)
LOG = logging.getLogger("card_scraper")

BANK_NAMES = {
    "AMEX": "American Express",
    "CITI": "Citi",
    "CIMB": "CIMB",
    "DBS": "DBS",
    "DCS": "DCS",
    "HSBC": "HSBC",
    "MBB": "Maybank",
    "MAYBANK": "Maybank",
    "OCBC": "OCBC",
    "POSB": "POSB",
    "SC": "Standard Chartered",
    "SCB": "Standard Chartered",
    "TRB": "Trust",
    "TRUST": "Trust",
    "UOB": "UOB",
}

FIELD_LABELS = {
    "Ideal for", "Best for", "Card benefit", "Supported Payment Network",
    "Supported Payment Type", "Promo Code", "Promo_Code",
    "Minimum Payment", "Minimum Monthly Repayment", "Late Payment Charge",
    "Late Payment Fee", "Interest on Purchase", "Purchase Interest Rate",
    "Interest Rate", "Interest on Cash Advance", "Cash Advance Interest Rate",
    "Interest Free Period", "Interest Free Days", "Annual Fee",
    "Foreign Currency Transaction Fee", "Air Miles Conversion Fee",
    "Miles Conversion Fee", "Cash Advance Service Charge", "Cash Advance Fee",
    "Monthly Spend Required", "Minimum Annual Income", "Minimum Age",
}

VALUE_NOISE = {"", ":", "-", "—", "Apply", "Apply Now", "See more", "Terms and Conditions"}
CARD_SECTIONS = {"Offers", "Highlights", "Benefits", "Fees", "Fees & Charges", "Eligibility", "Card Details"}


@dataclass
class ListingCard:
    product_id: str
    name: str
    issuer_code: str
    detail_url: str | None
    apply_urls: list[str] = field(default_factory=list)
    links: list[dict[str, str]] = field(default_factory=list)
    image_url: str | None = None
    text: str = ""
    schema_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class CardPage:
    name: str
    source_url: str
    summary: str | None
    image_url: str | None
    sections: dict[str, str]
    section_tokens: dict[str, list[str]]
    fields: dict[str, str]
    links: list[dict[str, str]]
    apply_urls: list[str]
    status_code: int


class SupabaseError(RuntimeError):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code

    @property
    def is_authorization_error(self) -> bool:
        return self.status_code in {401, 403}


class ConfigurationError(RuntimeError):
    """Actionable setup/deployment problem rather than a scraper bug."""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    value = unicodedata.normalize("NFKC", value)
    value = re.sub(r"[\ue000-\uf8ff]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def unique_strings(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def unique_links(values: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for value in values:
        key = (value.get("label", ""), value.get("url", ""))
        if key[1] and key not in seen:
            seen.add(key)
            output.append({"label": key[0], "url": key[1]})
    return output


def number(value: str | None) -> float | None:
    if not value:
        return None
    match = re.search(r"(?<![A-Za-z])(-?[0-9][0-9,]*(?:\.[0-9]+)?)", value)
    return float(match.group(1).replace(",", "")) if match else None


def integer(value: str | None) -> int | None:
    parsed = number(value)
    return int(parsed) if parsed is not None else None


def money(value: str | None) -> float | None:
    if value and re.search(r"\bno annual fee\b|\bfree\b", value, re.I):
        return 0.0
    if not value:
        return None
    match = re.search(r"S\$\s*([0-9][0-9,]*(?:\.[0-9]+)?)", value, re.I)
    return float(match.group(1).replace(",", "")) if match else number(value)


def percent(value: str | None) -> float | None:
    return number(value) if value and "%" in value else None


def build_http_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=4, connect=4, read=4, backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}), respect_retry_after_header=True,
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-SG,en;q=0.9",
    })
    return session


def fetch_html(session: requests.Session, url: str, timeout: float) -> tuple[str, int]:
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    if len(response.text) < 1_000:
        raise RuntimeError(f"Unexpectedly short response from {url}")
    return response.text, response.status_code


def walk_json(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_json(child)


def schema_products(soup: BeautifulSoup) -> dict[str, dict[str, Any]]:
    products: dict[str, dict[str, Any]] = {}
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            value = json.loads(script.get_text())
        except (json.JSONDecodeError, TypeError):
            continue
        for item in walk_json(value):
            if item.get("@type") == "Product" and item.get("@id"):
                products[str(item["@id"])] = item
    return products


def product_url(row: Tag) -> str | None:
    for anchor in row.find_all("a", href=True):
        href = anchor.get("href", "")
        if "/credit-card/products/" in href:
            return urljoin(BASE_URL, href)
        aliases = parse_qs(urlsplit(href).fragment).get("cms_modalProductUrlAlias", [])
        if aliases:
            return urljoin(BASE_URL, unquote(aliases[0]))
    return None


def parse_listing(html: str) -> list[ListingCard]:
    soup = BeautifulSoup(html, "html.parser")
    products = schema_products(soup)
    cards: dict[str, ListingCard] = {}
    for row in soup.select("tr[data-uid]"):
        product_id = clean_text(row.get("data-uid"))
        if not product_id:
            continue
        structured = products.get(product_id, {})
        image = row.find("img", alt=True)
        name = clean_text(image.get("alt")) if image else ""
        name = name or clean_text(str(structured.get("name", ""))) or product_id
        parts = product_id.split(".")
        issuer_code = parts[2].upper() if len(parts) > 2 else name.split()[0].upper()
        links = []
        for anchor in row.find_all("a", href=True):
            href = anchor.get("href", "")
            absolute = f"{LISTING_URL}{href}" if href.startswith("#") else urljoin(BASE_URL, href)
            links.append({"label": clean_text(anchor.get_text(" ", strip=True)), "url": absolute})
        apply_urls = unique_strings(
            urljoin(BASE_URL, anchor.get("href", ""))
            for anchor in row.select('a[data-testid="apply-cta"][href]')
        )
        image_url = clean_text(image.get("src")) if image else ""
        image_url = image_url or clean_text(str(structured.get("image", ""))) or None
        cards[product_id] = ListingCard(
            product_id=product_id, name=name, issuer_code=issuer_code,
            detail_url=product_url(row), apply_urls=apply_urls,
            links=unique_links(links), image_url=image_url,
            text=clean_text(row.get_text(" | ", strip=True)), schema_data=structured,
        )
    if not cards:
        raise RuntimeError("No SingSaver card rows found; the page structure may have changed")
    return list(cards.values())


def heading_tokens(heading: Tag, stop_tag: str) -> list[str]:
    tokens: list[str] = []
    for element in heading.next_elements:
        if element is heading:
            continue
        if isinstance(element, Tag) and element.name == stop_tag:
            break
        if not isinstance(element, NavigableString):
            continue
        if element.parent and element.parent.name in {"script", "style", "noscript"}:
            continue
        value = clean_text(str(element))
        if value:
            tokens.append(value)
    return tokens


def is_field_label(value: str) -> bool:
    return any(value.casefold() == label.casefold() for label in FIELD_LABELS)


def next_value(tokens: list[str], index: int) -> str | None:
    for token in tokens[index + 1:index + 6]:
        if token in VALUE_NOISE:
            continue
        if is_field_label(token):
            return None
        return token
    return None


def extract_fields(section_tokens: dict[str, list[str]]) -> dict[str, str]:
    fields: dict[str, str] = {}
    for tokens in section_tokens.values():
        for index, token in enumerate(tokens):
            label = next((item for item in FIELD_LABELS if token.casefold() == item.casefold()), None)
            if label and label not in fields:
                value = next_value(tokens, index)
                if value:
                    fields[label] = value
    return fields


def parse_page(html: str, url: str, listing: ListingCard, status_code: int) -> CardPage:
    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("main") or soup.body
    if not main:
        raise RuntimeError(f"No product content found at {url}")
    h1 = main.find("h1")
    name = clean_text(h1.get_text(" ", strip=True)) if h1 else listing.name
    section_tokens: dict[str, list[str]] = {
        "Overview": heading_tokens(h1, "h2") if h1 else [listing.text]
    }
    for heading in main.find_all("h2"):
        title = clean_text(heading.get_text(" ", strip=True))
        if title in CARD_SECTIONS:
            section_tokens.setdefault(title, []).extend(heading_tokens(heading, "h2"))
    sections = {title: " | ".join(tokens) for title, tokens in section_tokens.items() if tokens}
    links = []
    for anchor in main.find_all("a", href=True):
        href = anchor.get("href", "").strip()
        if href and not href.startswith(("javascript:", "mailto:", "tel:")):
            links.append({
                "label": clean_text(anchor.get_text(" ", strip=True)),
                "url": urljoin(url, href),
            })
    links = unique_links([*listing.links, *links])
    apply_urls = unique_strings([
        *listing.apply_urls,
        *(link["url"] for link in links if "/apply" in link["url"].casefold()
          or link["label"].casefold() in {"apply", "apply now"}),
    ])
    description = soup.find("meta", attrs={"name": "description"})
    summary = clean_text(description.get("content")) if description else ""
    if not summary:
        paragraphs = [clean_text(item.get_text(" ", strip=True)) for item in main.find_all("p")]
        summary = next((item for item in paragraphs if len(item) >= 80 and name not in item), "")
    image = main.find("img", alt=lambda value: value and clean_text(value) == name)
    image_url = urljoin(url, image.get("src")) if image and image.get("src") else listing.image_url
    return CardPage(
        name=name, source_url=url, summary=summary or None, image_url=image_url,
        sections=sections, section_tokens=section_tokens,
        fields=extract_fields(section_tokens), links=links,
        apply_urls=apply_urls, status_code=status_code,
    )


def fallback_page(listing: ListingCard) -> CardPage:
    url = listing.detail_url or f"{LISTING_URL}#{quote(listing.product_id, safe='.-')}"
    return CardPage(
        name=listing.name, source_url=url,
        summary=clean_text(str(listing.schema_data.get("description", ""))) or None,
        image_url=listing.image_url, sections={"Listing": listing.text},
        section_tokens={"Listing": [listing.text]}, fields={},
        links=listing.links, apply_urls=listing.apply_urls, status_code=200,
    )


def field_value(fields: dict[str, str], *labels: str) -> str | None:
    return next((fields[label] for label in labels if label in fields), None)


def benefit_kind(label: str) -> str | None:
    lowered = label.casefold()
    if lowered.startswith("cashback"):
        return "cashback"
    if lowered.startswith(("airmiles", "air miles", "miles")):
        return "miles"
    if lowered.startswith(("rewards", "points")):
        return "points"
    return None


def benefit_category(label: str) -> str:
    value = re.sub(
        r"^(cashback|air\s*miles|miles|rewards points|rewards|points)\s*",
        "", label, flags=re.I,
    ).strip(" ()") or "all"
    aliases = {
        "baseline": "all", "base rate": "all",
        "department store": "shopping",
        "local online shopping": "online_shopping",
        "taxi ride sharing": "transport",
    }
    value = aliases.get(value.casefold(), value.casefold())
    return re.sub(r"[^a-z0-9]+", "_", value).strip("_") or "all"


def benefit_unit(value: str, kind: str) -> str:
    lowered = value.casefold()
    if "%" in value:
        return "%"
    if re.search(r"\bpoints?\b", lowered) and "month" in lowered:
        return "points/month"
    if re.search(r"\bpoints?\b", lowered) and "dollar" in lowered:
        return "points/dollar"
    if "miles" in lowered and "dollar" in lowered:
        return "miles/dollar"
    if "miles" in lowered and "month" in lowered:
        return "miles/month"
    return kind


def extract_benefits(page: CardPage) -> list[dict[str, Any]]:
    tokens = page.section_tokens.get("Benefits", [])
    benefits: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for index, label in enumerate(tokens):
        kind = benefit_kind(label)
        if not kind or label.casefold() in {"cashback", "airmiles", "air miles", "rewards points"}:
            continue
        if "fee" in label.casefold():
            continue
        value = next_value(tokens, index)
        if not value or number(value) is None or (label, value) in seen:
            continue
        seen.add((label, value))
        benefits.append({
            "label": label, "value": value, "kind": kind,
            "category": benefit_category(label), "amount": number(value),
            "unit": benefit_unit(value, kind),
        })
    if not benefits:
        headline = field_value(page.fields, "Card benefit")
        if headline:
            benefits.append({"label": "Card benefit", "value": headline})
    return benefits


def infer_network(page: CardPage) -> str | None:
    value = field_value(page.fields, "Supported Payment Network") or ""
    combined = f"{value} {page.name}".casefold()
    for needle, network in (
        ("mastercard", "Mastercard"), ("master card", "Mastercard"),
        ("visa", "Visa"), ("american express", "Amex"),
        ("amex", "Amex"), ("unionpay", "UnionPay"),
    ):
        if needle in combined:
            return network
    return clean_text(value) or None


def infer_card_type(page: CardPage, benefits: list[dict[str, Any]]) -> str:
    name = page.name.casefold()
    overview = page.sections.get("Overview", "").casefold()
    if "student" in name:
        return "student"
    if "business" in name or "corporate" in name:
        return "business"
    if "prepaid" in name:
        return "prepaid"
    if "miles / dollar" in overview or "mile / dollar" in overview:
        return "miles"
    if "points / dollar" in overview:
        return "rewards_points"
    if "cashback" in overview or "cash back" in name:
        return "cashback"
    kinds = {item.get("kind") for item in benefits}
    if "miles" in kinds:
        return "miles"
    if "points" in kinds:
        return "rewards_points"
    return "cashback"


def find_best_for(page: CardPage, listing: ListingCard) -> str | None:
    direct = field_value(page.fields, "Best for", "Ideal for")
    if direct:
        return direct
    text = f"{listing.text} {page.sections.get('Overview', '')}"
    match = re.search(r"\bBest for\s+([^|]{2,100})", text, re.I)
    return clean_text(match.group(1)) if match else None


def find_rating(page: CardPage, listing: ListingCard) -> float | None:
    text = f"{listing.text} {' '.join(page.sections.values())}"
    match = re.search(r"(?:Seedly\s+)?rating\s*[: ]\s*([0-5](?:\.\d+)?)\s*/\s*5", text, re.I)
    return float(match.group(1)) if match else None


def find_promo_code(page: CardPage, listing: ListingCard) -> str | None:
    direct = field_value(page.fields, "Promo Code", "Promo_Code")
    if direct:
        return direct
    text = f"{listing.text} {page.sections.get('Overview', '')}"
    match = re.search(r"Promo[_ ]Code\s*:\s*([A-Z0-9_-]+)", text, re.I)
    return match.group(1) if match else None


def json_section(page: CardPage, name: str) -> list[dict[str, str]]:
    text = page.sections.get(name)
    return [{"text": text}] if text else []


def build_payload(listing: ListingCard, page: CardPage, partial_error: str | None) -> dict[str, Any]:
    benefits = extract_benefits(page)
    fields = page.fields
    raw_details = {
        "listing_text": listing.text,
        "listing_schema": listing.schema_data,
        "fields": fields,
        "sections": page.sections,
        "http_status": page.status_code,
        "partial_error": partial_error,
    }
    hash_input = json.dumps({
        "product_id": listing.product_id, "name": page.name,
        "benefits": benefits, "links": page.links, "raw_details": raw_details,
    }, ensure_ascii=False, sort_keys=True)
    payload: dict[str, Any] = {
        "singsaver_id": listing.product_id,
        "name": page.name,
        "bank": BANK_NAMES.get(listing.issuer_code, listing.issuer_code),
        "card_type": infer_card_type(page, benefits),
        "network": infer_network(page),
        "best_for": find_best_for(page, listing),
        "summary": page.summary,
        "image_url": page.image_url,
        "rating": find_rating(page, listing),
        "promo_code": find_promo_code(page, listing),
        "benefits": benefits,
        "minimum_payment_pct": percent(field_value(fields, "Minimum Payment", "Minimum Monthly Repayment")),
        "late_payment_fee_sgd": money(field_value(fields, "Late Payment Charge", "Late Payment Fee")),
        "purchase_interest_pa": percent(field_value(fields, "Interest on Purchase", "Purchase Interest Rate", "Interest Rate")),
        "cash_advance_interest_pa": percent(field_value(fields, "Interest on Cash Advance", "Cash Advance Interest Rate")),
        "interest_free_days": integer(field_value(fields, "Interest Free Period", "Interest Free Days")),
        "annual_fee_sgd": money(field_value(fields, "Annual Fee")),
        "foreign_currency_fee_pct": percent(field_value(fields, "Foreign Currency Transaction Fee")),
        "miles_conversion_fee_sgd": money(field_value(fields, "Air Miles Conversion Fee", "Miles Conversion Fee")),
        "cash_advance_fee_sgd": money(field_value(fields, "Cash Advance Service Charge", "Cash Advance Fee")),
        "monthly_spend_sgd": money(field_value(fields, "Monthly Spend Required")),
        "minimum_annual_income_sgd": integer(field_value(fields, "Minimum Annual Income")),
        "minimum_age": integer(field_value(fields, "Minimum Age")),
        "offers": json_section(page, "Offers"),
        "highlights": json_section(page, "Highlights"),
        "all_links": page.links,
        "raw_details": raw_details,
        "detail_url": page.source_url,
        "apply_url": page.apply_urls[0] if page.apply_urls else None,
        "source_type": "singsaver",
        "last_scraped_at": now_iso(),
        "is_active": True,
        "data_hash": hashlib.sha256(hash_input.encode("utf-8")).hexdigest(),
    }
    return {key: value for key, value in payload.items() if value is not None}


def jwt_role(key: str) -> str | None:
    if key.startswith("sb_publishable_"):
        return "anon"
    if key.startswith("sb_secret_"):
        return "service_role"
    parts = key.split(".")
    if len(parts) != 3:
        return None
    try:
        padded = parts[1] + "=" * (-len(parts[1]) % 4)
        return json.loads(base64.urlsafe_b64decode(padded)).get("role")
    except (ValueError, json.JSONDecodeError):
        return None


class SupabaseREST:
    def __init__(self, url: str, key: str, timeout: float) -> None:
        if jwt_role(key) == "anon":
            raise ConfigurationError(
                "SUPABASE_SERVICE_ROLE_KEY contains an anon/publishable key. "
                "Use the service_role JWT or an sb_secret_ key for scraper writes."
            )
        self.base_url = url.rstrip("/") + "/rest/v1"
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "apikey": key, "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        })

    def request(
        self, method: str, table: str, *, params: dict[str, str] | None = None,
        payload: Any = None, prefer: str = "return=minimal",
    ) -> Any:
        response = self.session.request(
            method, f"{self.base_url}/{quote(table, safe='')}", params=params,
            json=payload, headers={"Prefer": prefer}, timeout=self.timeout,
        )
        if not response.ok:
            raise SupabaseError(
                response.status_code,
                f"Supabase {method} {table} failed ({response.status_code}): {response.text[:1500]}",
            )
        return response.json() if response.content else []

    def upsert_card(self, payload: dict[str, Any]) -> dict[str, Any]:
        rows = self.request(
            "POST", "credit_cards", params={"on_conflict": "singsaver_id"},
            payload=payload, prefer="resolution=merge-duplicates,return=representation",
        )
        if not rows:
            raise RuntimeError(f"Supabase returned no row for {payload['name']}")
        return rows[0]

    def preflight(self) -> None:
        """Fail before scraping when the required tables are not deployed."""
        try:
            self.request(
                "GET",
                "credit_cards",
                params={"select": "singsaver_id", "limit": "1"},
            )
            self.request(
                "GET",
                "scrape_logs",
                params={"select": "id", "limit": "1"},
            )
        except SupabaseError as exc:
            if exc.status_code == 404 or "PGRST205" in str(exc):
                raise ConfigurationError(
                    "Supabase is missing public.credit_cards or public.scrape_logs. "
                    "Run backend/scraper/credit_card_schema.sql in the Supabase SQL Editor, "
                    "then retry."
                ) from exc
            raise

    def log_scrape(
        self, url: str, status: str, *, linked_id: str | None = None,
        http_status: int | None = None, error: str | None = None,
    ) -> None:
        data = {
            "source_url": url, "source_type": "singsaver", "linked_id": linked_id,
            "status": status, "http_status": http_status,
            "error_message": error[:2000] if error else None,
        }
        self.request("POST", "scrape_logs", payload={k: v for k, v in data.items() if v is not None})


def create_db(args: argparse.Namespace) -> SupabaseREST | None:
    if args.dry_run:
        return None
    load_dotenv(args.env_file)
    url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise ConfigurationError(f"Missing Supabase URL or service key in {args.env_file}")
    return SupabaseREST(url, key, args.timeout)


def run(args: argparse.Namespace) -> int:
    db = create_db(args)  # validate the key before downloading the large listing
    if db:
        db.preflight()
    session = build_http_session()
    LOG.info("Fetching %s", LISTING_URL)
    listing_html, listing_status = fetch_html(session, LISTING_URL, args.timeout)
    cards = parse_listing(listing_html)
    discovered = len(cards)
    if args.only:
        search = args.only.casefold()
        cards = [card for card in cards if search in card.name.casefold() or search in card.product_id.casefold()]
    if args.limit:
        cards = cards[:args.limit]
    if not cards:
        raise RuntimeError("No cards matched the supplied filters")
    LOG.info("Discovered %d cards; processing %d", discovered, len(cards))

    stats = {"success": 0, "partial": 0, "failed": 0}
    for index, listing in enumerate(cards, start=1):
        LOG.info("[%d/%d] %s", index, len(cards), listing.name)
        partial_error: str | None = None
        if listing.detail_url and not args.skip_details:
            try:
                html, status = fetch_html(session, listing.detail_url, args.timeout)
                page = parse_page(html, listing.detail_url, listing, status)
            except Exception as exc:
                partial_error = str(exc)
                LOG.warning("Using listing-only data for %s: %s", listing.name, exc)
                page = fallback_page(listing)
        else:
            page = fallback_page(listing)
            if not args.skip_details and not listing.detail_url:
                partial_error = "No SingSaver product-detail URL was exposed"
        try:
            payload = build_payload(listing, page, partial_error)
            result = "partial" if partial_error else "success"
            if args.dry_run:
                preview = payload if args.verbose else {
                    "singsaver_id": payload["singsaver_id"],
                    "name": payload["name"],
                    "bank": payload["bank"],
                    "card_type": payload["card_type"],
                    "best_for": payload.get("best_for"),
                    "detail_url": payload["detail_url"],
                    "apply_url": payload.get("apply_url"),
                    "benefits_found": len(payload["benefits"]),
                    "fields_found": len(payload["raw_details"]["fields"]),
                    "result": result,
                }
                print(json.dumps(preview, ensure_ascii=False, indent=2))
            else:
                assert db is not None
                saved = db.upsert_card(payload)
                db.log_scrape(
                    page.source_url, result, linked_id=str(saved["id"]),
                    http_status=page.status_code, error=partial_error,
                )
            stats[result] += 1
        except SupabaseError as exc:
            stats["failed"] += 1
            LOG.error("Database write failed for %s: %s", listing.name, exc)
            if (
                exc.is_authorization_error
                or exc.status_code in {400, 404}
                or "42501" in str(exc)
                or "PGRST" in str(exc)
                or "schema cache" in str(exc).casefold()
            ):
                raise ConfigurationError(
                    "Supabase rejected the schema/write operation. Apply credit_card_schema.sql "
                    "and use a service-role/secret key, then retry."
                ) from exc
        except Exception as exc:
            stats["failed"] += 1
            LOG.exception("Failed to process %s", listing.name)
            if db:
                try:
                    db.log_scrape(page.source_url, "failed", error=str(exc))
                except Exception:
                    LOG.warning("Could not write failure log")
        if index < len(cards) and args.delay:
            time.sleep(args.delay)

    if db:
        db.log_scrape(
            LISTING_URL, "success" if not stats["failed"] else "partial",
            http_status=listing_status,
            error=f"Run summary: {json.dumps(stats, sort_keys=True)}",
        )
    LOG.info("Finished: %s", json.dumps(stats, sort_keys=True))
    return 1 if stats["failed"] else 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape SingSaver credit cards into Supabase")
    parser.add_argument("--env-file", type=Path, default=Path(__file__).resolve().parent.parent / ".env")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--only", help="Card name or SingSaver product-ID substring")
    parser.add_argument("--delay", type=float, default=0.5)
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-details", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    try:
        return run(args)
    except KeyboardInterrupt:
        LOG.warning("Interrupted")
        return 130
    except ConfigurationError as exc:
        LOG.error("%s", exc)
        return 1
    except Exception:
        LOG.exception("Scrape failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
