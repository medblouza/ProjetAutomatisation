// mapAnalysisToViewModel.js
export function mapAnalysisToViewModel(analysis) {
  const { business_info, brand_identity, pages } = analysis;

  return {
    cdc: {
      company: {
        name: business_info.company_name,
        activity: business_info.sector,
        location: business_info.city,
      },
      branding: {
        colors: brand_identity.brand_colors,
        style: (brand_identity.style_keywords || []).join(', '),
        typography: (brand_identity.typography_hints || []).join(', '),
      },
    },
    structure: {
      routes: pages.map((p) => ({
        page: p.name,
        url: p.url,
        sections: p.sections.map((s) => ({ name: s.type })),
      })),
    },
    preview_html: null,   // pas encore généré par le backend (Phase 1 seulement)
    download_url: null,
    _raw: analysis,
  };
}