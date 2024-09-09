module.exports = {
  scanner: {
    include: [
      "/",
      "/about",
      "/foia",
      "/inspector",
      "/privacy",
      "/search",
      "/sitemap",
      "/accessibility",
      "/contact",
      "/fear",
      "/espanol",
      "/es",
      "/sitemap",
      "/sitemap.xml",
      "/blog",
      "/*"
    ],
    samples: 1,
    device: 'desktop',
    throttle: true,
    maxRoutes: 300,
    skipJavascript: false,
    sitemap: true,
  },
  chrome: {
    useSystem: true
  },
  debug: false,
};