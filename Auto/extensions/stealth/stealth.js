// Stealth Script - Hide antidetect browser fingerprint
// Injected at document_start in MAIN world

(function() {
    'use strict';

    // ==================== WEBDRIVER ====================
    // Hide navigator.webdriver
    try {
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
            configurable: true
        });
    } catch (e) {}

    // Delete webdriver property
    try {
        delete navigator.__proto__.webdriver;
    } catch (e) {}

    // ==================== CHROME RUNTIME ====================
    // Fake chrome runtime object
    if (!window.chrome) {
        window.chrome = {};
    }
    if (!window.chrome.runtime) {
        window.chrome.runtime = {
            connect: function() {},
            sendMessage: function() {},
            onMessage: { addListener: function() {} },
            id: undefined
        };
    }

    // ==================== PLUGINS ====================
    // Create realistic plugins array
    const pluginData = [
        { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
        { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
        { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' }
    ];

    try {
        const pluginArray = pluginData.map(p => {
            const plugin = Object.create(Plugin.prototype);
            Object.defineProperties(plugin, {
                name: { value: p.name, enumerable: true },
                filename: { value: p.filename, enumerable: true },
                description: { value: p.description, enumerable: true },
                length: { value: 0, enumerable: true }
            });
            return plugin;
        });

        Object.defineProperty(navigator, 'plugins', {
            get: () => {
                const arr = Object.create(PluginArray.prototype);
                pluginArray.forEach((p, i) => { arr[i] = p; });
                Object.defineProperty(arr, 'length', { value: pluginArray.length });
                arr.item = (i) => pluginArray[i] || null;
                arr.namedItem = (name) => pluginArray.find(p => p.name === name) || null;
                arr.refresh = () => {};
                return arr;
            },
            configurable: true
        });
    } catch (e) {}

    // ==================== LANGUAGES ====================
    try {
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
            configurable: true
        });
    } catch (e) {}

    // ==================== PERMISSIONS ====================
    // Override permissions query
    try {
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = function(parameters) {
            if (parameters.name === 'notifications') {
                return Promise.resolve({ state: Notification.permission });
            }
            return originalQuery.call(this, parameters);
        };
    } catch (e) {}

    // ==================== AUTOMATION FLAGS ====================
    // Remove automation-related properties
    try {
        Object.defineProperty(navigator, 'automationController', {
            get: () => undefined,
            configurable: true
        });
    } catch (e) {}

    // ==================== HEADLESS DETECTION ====================
    // Fix userAgent if contains HeadlessChrome
    try {
        const originalUA = navigator.userAgent;
        if (originalUA.includes('HeadlessChrome')) {
            Object.defineProperty(navigator, 'userAgent', {
                get: () => originalUA.replace('HeadlessChrome', 'Chrome'),
                configurable: true
            });
        }
    } catch (e) {}

    // ==================== WEBGL VENDOR/RENDERER ====================
    // Don't override - let Orbita handle this with its own spoofing
    // Overriding here would conflict with Orbita's fingerprint

    // ==================== IFRAME CONTENTWINDOW ====================
    // Prevent iframe detection
    try {
        const originalContentWindow = Object.getOwnPropertyDescriptor(HTMLIFrameElement.prototype, 'contentWindow');
        Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
            get: function() {
                const win = originalContentWindow.get.call(this);
                if (win) {
                    try {
                        Object.defineProperty(win.navigator, 'webdriver', {
                            get: () => undefined,
                            configurable: true
                        });
                    } catch (e) {}
                }
                return win;
            }
        });
    } catch (e) {}

    // ==================== CONSOLE.DEBUG ====================
    // Some sites check console.debug
    try {
        const originalDebug = console.debug;
        console.debug = function() {
            // Filter out automation-related messages
            const args = Array.from(arguments);
            const str = args.join(' ').toLowerCase();
            if (str.includes('automation') || str.includes('webdriver')) {
                return;
            }
            return originalDebug.apply(console, arguments);
        };
    } catch (e) {}

    // ==================== ERROR STACK TRACE ====================
    // Clean error stack traces
    try {
        const originalError = Error;
        window.Error = function(...args) {
            const error = new originalError(...args);
            if (error.stack) {
                error.stack = error.stack.replace(/chrome-extension:\/\/[^\s]+/g, '');
            }
            return error;
        };
        window.Error.prototype = originalError.prototype;
    } catch (e) {}

    // ==================== DOCUMENT PROPERTIES ====================
    // Hide $cdc_ and $wdc_ properties (ChromeDriver markers)
    try {
        const props = Object.getOwnPropertyNames(document);
        props.forEach(prop => {
            if (prop.startsWith('$cdc_') || prop.startsWith('$wdc_')) {
                delete document[prop];
            }
        });
    } catch (e) {}

    // ==================== WINDOW PROPERTIES ====================
    // Clean window object
    try {
        const windowProps = ['__nightmare', '__selenium_unwrapped', '__webdriver_evaluate', 
                           '__driver_evaluate', '__webdriver_unwrapped', '__driver_unwrapped',
                           '__selenium_evaluate', '_Selenium_IDE_Recorder', '_selenium',
                           'callSelenium', 'calledSelenium', '__webdriver_script_fn',
                           '__webdriver_script_func', '__webdriver_script_function',
                           'webdriver', '__fxdriver_evaluate', '__fxdriver_unwrapped'];
        
        windowProps.forEach(prop => {
            try {
                if (prop in window) {
                    delete window[prop];
                }
                Object.defineProperty(window, prop, {
                    get: () => undefined,
                    configurable: true
                });
            } catch (e) {}
        });
    } catch (e) {}

    // ==================== NOTIFICATION ====================
    // Ensure Notification is properly defined
    try {
        if (!window.Notification) {
            window.Notification = {
                permission: 'default',
                requestPermission: () => Promise.resolve('default')
            };
        }
    } catch (e) {}

})();
