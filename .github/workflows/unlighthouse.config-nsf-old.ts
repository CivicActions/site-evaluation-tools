module.exports = {
  site: 'www.nsf.gov',
  scanner: {
    sitemap: [
        '/sitemap.xml'
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
    maxRoutes: 50,
    skipJavascript: false,
  },
  debug: false,
};