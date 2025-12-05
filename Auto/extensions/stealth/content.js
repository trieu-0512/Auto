// Basic stealth patches to reduce automation signals

// Hide webdriver flag
Object.defineProperty(navigator, 'webdriver', {
  get: () => undefined,
});

// Mock chrome runtime object
if (!window.chrome) {
  window.chrome = { runtime: {} };
}

// Fake plugins length
Object.defineProperty(navigator, 'plugins', {
  get: () => [1, 2, 3],
});

// Fake languages
Object.defineProperty(navigator, 'languages', {
  get: () => ['en-US', 'en'],
});

// Override permissions query to avoid automation errors
const originalQuery = window.navigator.permissions && window.navigator.permissions.query;
if (originalQuery) {
  window.navigator.permissions.query = (parameters) => (
    parameters && parameters.name === 'notifications'
      ? Promise.resolve({ state: Notification.permission })
      : originalQuery(parameters)
  );
}

// Remove HeadlessChrome if present
const ua = navigator.userAgent || '';
if (ua.includes('HeadlessChrome')) {
  const clean = ua.replace('HeadlessChrome', 'Chrome');
  Object.defineProperty(navigator, 'userAgent', {
    get: () => clean,
  });
}

// Patch WebGL vendor/renderer to non-empty values
const getParameter = WebGLRenderingContext && WebGLRenderingContext.prototype.getParameter;
if (getParameter) {
  WebGLRenderingContext.prototype.getParameter = function (parameter) {
    if (parameter === 37445) { // UNMASKED_VENDOR_WEBGL
      return 'Intel Inc.';
    }
    if (parameter === 37446) { // UNMASKED_RENDERER_WEBGL
      return 'Intel(R) UHD Graphics 630';
    }
    return getParameter.apply(this, arguments);
  };
}
