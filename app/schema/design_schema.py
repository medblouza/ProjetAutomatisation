"""
DesignJSON — the UI-generation contract consumed by the Figma plugin (and
later by React/Tailwind/HTML generators). Distinct from CDCAnalysis:
CDCAnalysis describes WHAT the client needs, DesignJSON describes HOW the
UI is built (components, layout, design tokens). No business language here —
only design language.
"""

from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Optional
#from pydantic import BaseModel, Field, field_validator
from pydantic import Field, field_validator
from app.schema.lenient_base import LenientBaseModel as BaseModel


class DesignTokens(BaseModel):
    primary: str
    secondary: Optional[str] = None
    accent: Optional[str] = None
    surface: str = "#FFFFFF"
    background: str = "#FFFFFF"
    text_primary: str = "#1A1A1A"
    text_secondary: str = "#6B7280"
    success: str = "#22C55E"
    warning: str = "#F59E0B"
    error: str = "#EF4444"

    @field_validator(
        "primary", "secondary", "accent", "surface", "background",
        "text_primary", "text_secondary", "success", "warning", "error"
    )
    @classmethod
    def _hex(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v.startswith("#"):
            v = f"#{v}"
        if len(v) not in (4, 7):
            raise ValueError(f"'{v}' is not a valid hex color")
        return v.upper()


class TypographyScale(BaseModel):
    h1: int = 48
    h2: int = 36
    h3: int = 28
    h4: int = 22
    body: int = 16
    small: int = 13


class Typography(BaseModel):
    heading_font: str = "Inter"
    body_font: str = "Inter"
    accent_font: Optional[str] = None
    heading_weight: str = "700"
    body_weight: str = "400"
    scale: TypographyScale = Field(default_factory=TypographyScale)


class SpacingScale(BaseModel):
    base_unit: int = 8
    scale: List[int] = Field(default_factory=lambda: [4, 8, 16, 24, 32, 48, 64, 96])


class BorderRadius(BaseModel):
    sm: str = "4px"
    md: str = "8px"
    lg: str = "16px"
    full: str = "9999px"


class Shadows(BaseModel):
    sm: str = "0 1px 2px rgba(0,0,0,0.05)"
    md: str = "0 4px 12px rgba(0,0,0,0.08)"
    lg: str = "0 12px 32px rgba(0,0,0,0.12)"


class IconStyle(BaseModel):
    style: str = "outline"
    default_size: int = 24


class ButtonStyle(BaseModel):
    variants: List[str] = Field(default_factory=lambda: ["primary", "secondary", "ghost", "outline"])
    radius: str = "8px"
    padding: str = "12px 24px"


class CardStyle(BaseModel):
    radius: str = "12px"
    shadow: str = "md"
    padding: str = "24px"
    border: bool = False


class FormStyle(BaseModel):
    input_radius: str = "8px"
    input_border: str = "1px solid #E5E7EB"
    label_style: str = "sm-bold"


class NavbarStyle(BaseModel):
    position: str = "sticky"
    background: str = "surface"
    height: str = "72px"


class FooterStyle(BaseModel):
    layout: str = "columns"
    background: str = "dark"


class DesignSystem(BaseModel):
    theme: str
    tokens: DesignTokens
    typography: Typography = Field(default_factory=Typography)
    spacing: SpacingScale = Field(default_factory=SpacingScale)
    radius: BorderRadius = Field(default_factory=BorderRadius)
    shadows: Shadows = Field(default_factory=Shadows)
    icons: IconStyle = Field(default_factory=IconStyle)
    buttons: ButtonStyle = Field(default_factory=ButtonStyle)
    cards: CardStyle = Field(default_factory=CardStyle)
    forms: FormStyle = Field(default_factory=FormStyle)
    navbar: NavbarStyle = Field(default_factory=NavbarStyle)
    footer: FooterStyle = Field(default_factory=FooterStyle)


class GridConfig(BaseModel):
    columns: int
    gutter: int = 24
    margin: int = 24


class Breakpoints(BaseModel):
    mobile: int = 375
    tablet: int = 768
    desktop: int = 1440


class LayoutConfig(BaseModel):
    container_max_width: int = 1280
    section_spacing: int = 96
    grid_desktop: GridConfig = Field(default_factory=lambda: GridConfig(columns=12))
    grid_tablet: GridConfig = Field(default_factory=lambda: GridConfig(columns=8))
    grid_mobile: GridConfig = Field(default_factory=lambda: GridConfig(columns=4))
    breakpoints: Breakpoints = Field(default_factory=Breakpoints)


class ComponentType(str, Enum):
    NAVBAR = "navbar"
    HERO = "hero"
    FEATURES = "features"
    SERVICES_GRID = "services_grid"
    GALLERY = "gallery"
    TESTIMONIALS = "testimonials"
    FAQ = "faq"
    PRICING = "pricing"
    CTA = "cta"
    MAP = "map"
    CONTACT_FORM = "contact_form"
    FOOTER = "footer"
    IMAGE_BANNER = "image_banner"
    CARDS = "cards"
    STATISTICS = "statistics"
    TIMELINE = "timeline"
    LOGO_CLOUD = "logo_cloud"


class Asset(BaseModel):
    type: str
    description: str
    alt_text: Optional[str] = None
    placeholder_url: Optional[str] = None


class ComponentStyle(BaseModel):
    alignment: str = "left"
    padding: str = "lg"
    background: str = "background"
    variant: Optional[str] = None


class ComponentInstance(BaseModel):
    id: str
    type: ComponentType
    variant: Optional[str] = None
    order: int = 0
    content: Dict[str, Any] = Field(default_factory=dict)
    style: ComponentStyle = Field(default_factory=ComponentStyle)
    assets: List[Asset] = Field(default_factory=list)


class NavLink(BaseModel):
    label: str
    url: str


class Navigation(BaseModel):
    navbar_links: List[NavLink] = Field(default_factory=list)
    navbar_cta: Optional[NavLink] = None
    footer_links: List[NavLink] = Field(default_factory=list)
    footer_social_links: Dict[str, str] = Field(default_factory=dict)


class PageSEO(BaseModel):
    title: Optional[str] = None
    meta_description: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)


class PageDesign(BaseModel):
    id: str
    title: str
    url: str
    layout_type: str = "standard"
    seo: PageSEO = Field(default_factory=PageSEO)
    components: List[ComponentInstance] = Field(default_factory=list)

    @field_validator("components")
    @classmethod
    def _sorted(cls, v: List[ComponentInstance]) -> List[ComponentInstance]:
        return sorted(v, key=lambda c: c.order)


class Animation(BaseModel):
    scroll_animations: bool = True
    hover_effects: bool = True
    transition_speed: str = "normal"


class Accessibility(BaseModel):
    contrast_ratio_min: float = 4.5
    aria_required: bool = True
    keyboard_navigable: bool = True
    wcag_level: str = "AA"


class ProjectMeta(BaseModel):
    name: str
    description: Optional[str] = None
    industry: Optional[str] = None


class DesignJSON(BaseModel):
    project: ProjectMeta
    design_system: DesignSystem
    layout: LayoutConfig = Field(default_factory=LayoutConfig)
    navigation: Navigation = Field(default_factory=Navigation)
    pages: List[PageDesign]
    assets: List[Asset] = Field(default_factory=list)
    animation: Animation = Field(default_factory=Animation)
    accessibility: Accessibility = Field(default_factory=Accessibility)

    @field_validator("pages")
    @classmethod
    def _at_least_one_page(cls, v: List[PageDesign]) -> List[PageDesign]:
        if not v:
            raise ValueError("DesignJSON must contain at least one page")
        return v

