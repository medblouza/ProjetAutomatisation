"""
CDC Schema — structured representation of a client's Cahier des Charges (CDC)
after analysis by the CDCAnalyzerAgent.

This shape was calibrated on a real CDC (L'ART DE NANA — service évènementiel),
which turned out to already be pre-structured (brief créatif, pages avec
URL/SEO individuels, charte graphique avec couleurs/style, réseaux sociaux,
CTA, conformité, livrables). The schema below captures all of that so no
information is lost between the raw CDC and the JSON.

This agent still does NOT make visual/layout decisions (no component choice,
no exact font stack). It captures WHAT the client needs and WHAT constraints
they already gave (colors, style keywords, fonts) — the DesignDirectorAgent
(Phase 2) turns those constraints into a full design_system.
"""

from __future__ import annotations

from typing import Dict, List, Optional
#from pydantic import BaseModel, Field, field_validator
from pydantic import Field, field_validator
from app.schema.lenient_base import LenientBaseModel as BaseModel


class BusinessInfo(BaseModel):
    company_name: str
    sector: str = Field(..., description="Industry / business sector")
    city: Optional[str] = Field(default=None, description="Main city/location")
    service_area: Optional[str] = Field(
        default=None, description="Geographic area served, e.g. 'Dol-de-Bretagne et environs'"
    )
    target_audience: Optional[str] = None
    differentiators: List[str] = Field(
        default_factory=list, description="Points différenciants vs competitors"
    )
    experience: Optional[str] = Field(
        default=None, description="Experience/history, e.g. '5 ans d'expérience...'"
    )
    value_proposition: Optional[str] = None
    positioning: Optional[str] = Field(
        default=None, description="Positioning statement (Positionnement)"
    )

    @field_validator("differentiators")
    @classmethod
    def _clean_list(cls, v: List[str]) -> List[str]:
        return [x.strip() for x in v if x and x.strip()]


class MarketingInfo(BaseModel):
    objectives: List[str] = Field(default_factory=list, description="Objectifs du site web")
    key_messages: List[str] = Field(default_factory=list, description="Messages clés à communiquer")
    editorial_tone: Optional[str] = Field(default=None, description="Ton éditorial")
    primary_cta: Optional[str] = None
    secondary_cta: Optional[str] = None
    seo_angle: Optional[str] = Field(default=None, description="Angle SEO principal")


class BrandIdentity(BaseModel):
    existing_logo: bool = Field(default=False)
    brand_colors: List[str] = Field(
        default_factory=list, description="Hex colors from the charte graphique, e.g. '#e9dfe9'"
    )
    style_keywords: List[str] = Field(
        default_factory=list, description="Style descriptors, e.g. ['Epuré', 'Vintage']"
    )
    typography_hints: List[str] = Field(
        default_factory=list, description="Font names explicitly requested, e.g. ['Playfair Display', 'Lato']"
    )

    @field_validator("brand_colors")
    @classmethod
    def _validate_hex(cls, v: List[str]) -> List[str]:
        cleaned = []
        for c in v:
            c = c.strip()
            if c and not c.startswith("#"):
                c = f"#{c}"
            cleaned.append(c)
        return cleaned


class SectionRequest(BaseModel):
    """A section type requested for a page (from 'Sections à intégrer')."""

    type: str = Field(..., description="Functional section type, e.g. 'hero', 'cta_devis'")
    title: Optional[str] = None
    description: Optional[str] = None


class PageSEO(BaseModel):
    title: Optional[str] = Field(default=None, description="Titre SEO / <title>")
    meta_description: Optional[str] = None


class PageSpec(BaseModel):
    name: str
    url: Optional[str] = Field(default=None, description="e.g. '/accueil'")
    priority: Optional[int] = None
    seo: PageSEO = Field(default_factory=PageSEO)
    sections: List[SectionRequest] = Field(default_factory=list)
    content: Optional[str] = Field(
        default=None, description="Full marketing copy generated for this page, verbatim from the CDC"
    )


class SEOInfo(BaseModel):
    keywords: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=lambda: ["fr"])


class TechnicalRequirements(BaseModel):
    needs_cms: bool = Field(default=False)
    integrations: List[str] = Field(
        default_factory=list,
        description="e.g. 'Google Maps', 'formulaire de contact', 'boutons de partage', 'Google Analytics'",
    )
    responsive_required: bool = Field(default=True)
    images_needed: List[str] = Field(default_factory=list)
    social_links: Dict[str, Optional[str]] = Field(
        default_factory=dict, description="e.g. {'facebook': 'https://...', 'instagram': 'https://...'}"
    )
    compliance: List[str] = Field(
        default_factory=list, description="e.g. 'RGPD', 'mentions légales', 'politique de confidentialité'"
    )
    deliverables: List[str] = Field(
        default_factory=list, description="e.g. 'maquettes desktop+mobile', 'formation CMS'"
    )


class CDCAnalysis(BaseModel):
    """Full output of the CDC Analyzer Agent."""

    business_info: BusinessInfo
    marketing: MarketingInfo = Field(default_factory=MarketingInfo)
    brand_identity: BrandIdentity = Field(default_factory=BrandIdentity)
    pages: List[PageSpec] = Field(default_factory=list)
    seo: SEOInfo = Field(default_factory=SEOInfo)
    technical_requirements: TechnicalRequirements = Field(default_factory=TechnicalRequirements)
    raw_summary: Optional[str] = None

    @field_validator("pages")
    @classmethod
    def _must_have_at_least_one_page(cls, v: List[PageSpec]) -> List[PageSpec]:
        if not v:
            raise ValueError("CDCAnalysis must contain at least one page")
        return v

