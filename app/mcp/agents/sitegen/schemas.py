from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# CDC (sortie de cdc_parser_agent)
# ---------------------------------------------------------------------------

class Company(BaseModel):
    name: str = ""
    activity: str = ""
    location: str = ""


class Branding(BaseModel):
    colors: List[str] = Field(default_factory=list)
    style: str = ""
    typography: str = ""


class Section(BaseModel):
    name: str = ""
    # Champ optionnel : si le CDC contient du contenu explicite pour cette
    # section, l'agent d'extraction peut le remplir. Sinon laisser vide
    # (interdiction d'inventer du contenu).
    content: Optional[str] = ""


class Page(BaseModel):
    name: str = ""
    sections: List[Section] = Field(default_factory=list)


class CDCData(BaseModel):
    company: Company = Field(default_factory=Company)
    branding: Branding = Field(default_factory=Branding)
    pages: List[Page] = Field(default_factory=list)
    features: List[str] = Field(default_factory=list)
    seo: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Design system (sortie de design_system_agent)
# ---------------------------------------------------------------------------

class ColorPalette(BaseModel):
    primary: str = "#2563eb"
    secondary: str = "#64748b"
    background: str = "#ffffff"


class Fonts(BaseModel):
    main: str = "Inter"


class Spacing(BaseModel):
    base: str = "8px"


class Radius(BaseModel):
    small: str = "4px"
    medium: str = "8px"


class DesignSystem(BaseModel):
    colors: ColorPalette = Field(default_factory=ColorPalette)
    fonts: Fonts = Field(default_factory=Fonts)
    spacing: Spacing = Field(default_factory=Spacing)
    radius: Radius = Field(default_factory=Radius)


# ---------------------------------------------------------------------------
# Structure du site (sortie de site_structure_agent)
# ---------------------------------------------------------------------------

class Route(BaseModel):
    page: str
    url: str
    sections: List[Section] = Field(default_factory=list)


class SiteStructure(BaseModel):
    routes: List[Route] = Field(default_factory=list)
