# app/services/design_schema.py
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class FontWeight(str, Enum):
    LIGHT = "300"
    REGULAR = "400"
    MEDIUM = "500"
    BOLD = "700"

class ColorToken(BaseModel):
    hex: str
    role: str    # "primary" | "secondary" | "accent" | "background" | "text"
    name: str

class TypographyToken(BaseModel):
    family: str
    weight: FontWeight
    size_desktop: int
    size_mobile: int
    role: str    # "heading1" | "body" | "caption"

class Branding(BaseModel):
    colors: list[ColorToken]
    typography: list[TypographyToken]
    border_radius: int = 8

class ComponentType(str, Enum):
    HERO = "hero"
    NAVBAR = "navbar"
    CARD_GRID = "card_grid"
    TESTIMONIALS = "testimonials"
    CTA = "cta"
    FOOTER = "footer"
    CONTACT_FORM = "contact_form"
    GALLERY = "gallery"
    FAQ = "faq"
    TEAM = "team"

class Section(BaseModel):
    id: str
    type: ComponentType
    order: int
    headline: Optional[str] = None
    subheadline: Optional[str] = None
    cta_text: Optional[str] = None
    content_hints: list[str] = Field(default_factory=list)

class Page(BaseModel):
    id: str
    title: str
    slug: str
    sections: list[Section]
    is_priority: bool = False

class DesignJSON(BaseModel):
    version: str = "1.0"
    client_id: str
    client_name: str
    branding: Branding
    pages: list[Page]
    global_notes: list[str] = Field(default_factory=list)