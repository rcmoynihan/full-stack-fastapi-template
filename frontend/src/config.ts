interface AppConfig {
  API_BASE_URL: string
}

declare global {
  interface Window {
    APP_CONFIG?: AppConfig
  }
}

/**
 * Get the API base URL from runtime config.
 *
 * Returns an empty string for relative URLs, which works with the Vite proxy
 * during local development.
 *
 * Returns:
 *   API base URL from runtime config, or an empty string when unset.
 */
export function getApiBaseUrl(): string {
  return window.APP_CONFIG?.API_BASE_URL || ""
}
