interface AppConfig {
  API_BASE_URL: string
  SUPABASE_URL: string
  SUPABASE_PUBLISHABLE_KEY: string
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

export function getSupabaseUrl(): string {
  return (
    window.APP_CONFIG?.SUPABASE_URL ||
    import.meta.env.VITE_SUPABASE_URL ||
    "http://127.0.0.1:55321"
  )
}

export function getSupabasePublishableKey(): string {
  return (
    window.APP_CONFIG?.SUPABASE_PUBLISHABLE_KEY ||
    import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY ||
    "sb_publishable_ACJWlzQHlZjBrEguHvfOxg_3BJgxAaH"
  )
}
