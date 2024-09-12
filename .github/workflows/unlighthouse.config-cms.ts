module.exports = {
  puppeteerOptions: {
        args: ["--no-sandbox"],
    },
    server: {
        open: false,  
  site: 'cms.gov',
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
    // run lighthouse for each URL 1 time(s)
    samples: 3,
    // use desktop to scan
    device: 'desktop',
    // enable the throttling mode
    throttle: true,
    // increase the maximum number of routes - https://unlighthouse.dev/api/config#scannermaxroutes
    maxRoutes: 500,
    // skip the javascript scan
    skipJavascript: false,
    // use sitemaps - arrays are possible for specific sites https://unlighthouse.dev/api/config#scannersitemap
    sitemap: true,
  },
  debug: false,
};
