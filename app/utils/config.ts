
/**
 * Global Configuration
 * Centralizes environment variables and application constants
 */

// API Configuration
export const API_CONFIG = {
    // Prefer environment variable, fallback to Railway production URL
    BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'https://syscry-production.up.railway.app',

    // WebSocket endpoint
    get WS_URL() {
        const baseUrl = this.BASE_URL;
        const isSecure = baseUrl.startsWith('https');
        // Strip protocol and trailing slash
        const host = baseUrl.replace(/^https?:\/\//, '').replace(/\/$/, '');
        return `${isSecure ? 'wss' : 'ws'}://${host}/ws/signals`;
    }
};

export const FEATURES = {
    USE_MOCK_DATA: process.env.NEXT_PUBLIC_USE_MOCK === 'true',
};
