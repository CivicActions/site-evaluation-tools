module.exports = {
  site: 'cms.gov',
  puppeteerOptions: {
    args: ["--no-sandbox", '--disable-dev-shm-usage'],
    concurrency: 1,
  },
  lighthouseOptions: {
    onlyCategories: ['performance'],
  },
  server: {
    open: false,
  },
  scanner: {
    include: [
      "/",
      "/about",
      "/foia",
      "/about-cms/web-policies-important-links/web-policies/privacy",
      "/search/cms",
      "/sitemap",
      "/accessibility",
      "/contact",
      "/marketplace/agents-brokers/registration-training",
      "/about-cms/work-with-us/careers",
      "/medicare/physician-fee-schedule/search/overview",
      "/acronyms",
      "/*",
    ],
    exclude: [
      "/*.pdf",
      "/*.asp",
      "/*.aspx",
      "/sample-pfs-searches",
      "/security-guidelines-office-location",
      "/status-indicators",
      "/blog"
    ],
    // Run Lighthouse for each URL 3 times
    samples: 3,
    // Use desktop to scan
    device: 'desktop',
    // Enable throttling mode
    throttle: true,
    // Increase the maximum number of routes
    maxRoutes: 500,
    // Do not skip the JavaScript scan
    skipJavascript: false,
    // Use sitemaps
    sitemap: true,
  },
  debug: false,
};
