module.exports = {
  puppeteerOptions: {
        args: ["--no-sandbox", '--disable-dev-shm-usage'],
        concurrency: 1,
      },
  lighthouseOptions: {
    onlyCategories: ['best-practices'],
  },
  server: {
        open: false,
  site: 'sec.gov',
  scanner: {
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
    }
  },
  debug: false,
};
