"""
DesignGeneratorAgent — orchestrates DesignDirectorAgent (theme/palette/type)
and ComponentPlannerAgent (per-page components), then assembles the final
DesignJSON. Layout grids/breakpoints and navigation are built deterministically
in plain Python — there's no real design decision in "use a 12-col desktop
grid" or "put every page in the navbar", so no LLM call is spent on it.
"""

from __future__ import annotations

import re

from app.schema.cdc_schema import CDCAnalysis
from app.schema.design_schema import (
    DesignJSON,
    LayoutConfig,
    NavLink,
    Navigation,
    PageDesign,
    PageSEO,
    ProjectMeta,
)
from app.mcp.agents.sitegen.design_director_agent import DesignDirectorAgent
from app.mcp.agents.sitegen.component_planner_agent import ComponentPlannerAgent
from app.services.llm_service import LLMTool


def _slugify(name: str) -> str:
    slug = name.strip().lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug or "page"


def _build_navigation(cdc: CDCAnalysis) -> Navigation:
    navbar_links = [
        NavLink(label=p.name, url=p.url or f"/{_slugify(p.name)}")
        for p in sorted(cdc.pages, key=lambda p: p.priority or 0)
    ]
    navbar_cta = (
        NavLink(label=cdc.marketing.primary_cta, url="/contact")
        if cdc.marketing.primary_cta
        else None
    )
    return Navigation(
        navbar_links=navbar_links,
        navbar_cta=navbar_cta,
        footer_links=navbar_links,
        footer_social_links=cdc.technical_requirements.social_links,
    )


class DesignGeneratorAgent:
    def __init__(self, llm: LLMTool | None = None):
        llm = llm or LLMTool()
        self.director = DesignDirectorAgent(llm=llm)
        self.component_planner = ComponentPlannerAgent(llm=llm)

    def generate(self, cdc: CDCAnalysis) -> DesignJSON:
        design_system = self.director.build(cdc)

        pages: list[PageDesign] = []
        for page in cdc.pages:
            components = self.component_planner.plan(page)
            pages.append(
                PageDesign(
                    id=_slugify(page.name),
                    title=page.name,
                    url=page.url or f"/{_slugify(page.name)}",
                    seo=PageSEO(
                        title=page.seo.title,
                        meta_description=page.seo.meta_description,
                        keywords=cdc.seo.keywords,
                    ),
                    components=components,
                )
            )

        project = ProjectMeta(
            name=cdc.business_info.company_name,
            description=cdc.business_info.value_proposition,
            industry=cdc.business_info.sector,
        )

        return DesignJSON(
            project=project,
            design_system=design_system,
            layout=LayoutConfig(),
            navigation=_build_navigation(cdc),
            pages=pages,
        )
