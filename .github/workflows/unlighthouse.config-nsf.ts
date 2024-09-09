module.exports = {
  site: 'new.nsf.gov',
  scanner: {
    include: [
      "/",
      "/about",
      "/foia",
      "/search",
      "/sitemap",
      "/accessibility",
      "/contact",
      "/acronyms",
      "/about",
      "/about/budget/fy2024",
      "/about/directorates-offices",
      "/about/participant/before-your-meeting",
      "/careers",
      "/careers/nsf-supports-deia",
      "/careers/openings",
      "/careers/openings/asdf",
      "/careers/openings/od/olpa",
      "/epscor-research-infrastructure-improvement-program-track-1-rii-track-1",
      "/events",
      "/events/2023-nsf-engineering-career-proposal-workshop/2023-05-09",
      "/events/2023-solar-eclipse-viewing-events",
      "/events/build-and-broaden-30-webinar/2022-01-21",
      "/events/national-science-board-committee-external-engagement-ee-teleconference-open-5/2022-12-12",
      "/events/national-science-board-meeting-132/2023-11-29",
      "/events/past",
      "/events/solar-eclipse-2024",
      "/focus-areas",
      "/funding",
      "/funding/build-america-buy-america",
      "/funding/data-management-plan",
      "/funding/early-career-researchers",
      "/funding/getting-started",
      "/funding/graduate-students",
      "/funding/initiatives/broadening-participation/granted",
      "/funding/initiatives/convergence-accelerator",
      "/funding/initiatives/i-corps",
      "/funding/initiatives/regional-innovation-engines",
      "/funding/initiatives/regional-innovation-engines/updates/nsf-selects-34-semifinalists-inaugural-nsf",
      "/funding/learn",
      "/funding/learn/broader-impacts",
      "/funding/opportunities",
      "/funding/opportunities?query=ccf",
      "/funding/opportunities?query=prek",
      "/funding/opportunities?sort=nsf_funding_upcoming_due_dates_DESC",
      "/funding/opportunities?sort=search_api_relevance_DESC",
      "/funding/opportunities/accelerating-research-translation-art",
      "/funding/opportunities/advancing-informal-stem-learning-aisl",
      "/funding/opportunities/bio",
      "/funding/opportunities/biocomplexity-environment-integrated-research/5532/nsf03-597",
      "/funding/opportunities/building-prototype-open-knowledge-network-proto",
      "/funding/opportunities/centers-research-innovation-science-environment",
      "/funding/opportunities/civic-innovation-challenge-civic/nsf24-534/solicitation",
      "/funding/opportunities/computer-information-science-engineering-core",
      "/funding/opportunities/confronting-hazards-impacts-risks-resilient-planet",
      "/funding/opportunities/cyber-physical-systems-cps/nsf19-553",
      "/funding/opportunities/discovery-research-prek-12-drk-12",
      "/funding/opportunities/dynamics-integrated-socio-environmental-systems",
      "/funding/opportunities/eng",
      "/funding/opportunities/epscor-research-infrastructure-improvement-program-1",
      "/funding/opportunities/epscor-research-infrastructure-improvement-program-track-1-rii-track-1",
      "/funding/opportunities/faculty-early-career-development-program-career",
      "/funding/opportunities/future-manufacturing-fm",
      "/funding/opportunities/global-centers-gc",
      "/funding/opportunities/growing-research-access-nationally-transformative-0",
      "/funding/opportunities/iuse-innovation-two-year-college-stem-education",
      "/funding/opportunities/iuseprofessional-formation-engineers",
      "/funding/opportunities/nsf-graduate-research-fellowship-program-grfp",
      "/funding/opportunities/nsf-graduate-research-fellowship-program-grfp/nsf23-605/solicitation",
      "/funding/opportunities/nsf-regional-innovation-engines-nsf-engines-0",
      "/funding/opportunities/nsf-scholarships-science-technology-engineering",
      "/funding/opportunities/predictive-intelligence-pandemic-prevention-phase",
      "/funding/opportunities/research-experiences-undergraduates-reu",
      "/funding/senior-personnel-documents",
      "/funding/submitting-proposal",
      "/initiatives",
      "/new-nsf-awards",
      "/news",
      "/news/how-did-life-begin",
      "/news/nsf-announces-7-new-national-artificial",
      "/news/nsf-announces-seven-new-national-artificial",
      "/news/nsf-invests-162-million-research-centers",
      "/news/releases",
      "/od/honorary-awards/national-medal-of-science",
      "/od/honorary-awards/waterman",
      "/od/oia",
      "/policies/pappg",
      "/policies/pappg/23-1",
      "/policies/pappg/23-1/ch-2-proposal-preparation",
      "/policies/pappg/24-1",
      "/policies/pappg/24-1/ch-2-proposal-preparation",
      "/programs-small-businesses",
      "/sbwg",
      "/science-matters",
      "/science-matters/5-black-hole-facts-blow-your-mind",
      "/science-matters/ai-education-ai-education",
      "/science-matters/moment-changed-earth",
      "/staff/org/cise",
      "/staff/org/ocio",
      "/svg",
      "/tip/about-tip",
      "/tip/latest",
      "/*",
    ],
    exclude: [
      "/*.pdf",
      "/*.asp",
      "/*.aspx",
      "^/events(\?.*)?$",
      "^/events/past(\?.*)?$",
      "^/funding/(opportunities|opps)(/csvexport)?(\?.*)?$",
      "^/news/releases(\?.*)?$",
      "^/staff(\?.*)?$",
      "/staff/org/*",
      "/form/*"
    ],
    samples: 1,
    device: 'desktop',
    throttle: true,
    cache: true,
    maxRoutes: 25,
    skipJavascript: false,
    sitemap: true,
  },
  debug: false,
};
