import { createClient } from "@supabase/supabase-js"

const supabaseUrl =
  process.env.VITE_SUPABASE_URL ||
  process.env.SUPABASE_URL ||
  "http://127.0.0.1:55321"
const supabaseKey =
  process.env.VITE_SUPABASE_PUBLISHABLE_KEY ||
  process.env.SUPABASE_PUBLISHABLE_KEY ||
  "sb_publishable_ACJWlzQHlZjBrEguHvfOxg_3BJgxAaH"
const apiBaseUrl = process.env.API_BASE_URL || "http://localhost:8000"

const supabase = createClient(supabaseUrl, supabaseKey)

export const createUser = async ({
  email,
  password,
}: {
  email: string
  password: string
}) => {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: {
        full_name: "Test User",
      },
    },
  })
  if (error) throw error
  if (!data.session?.access_token) {
    throw new Error("Supabase did not return a session for the new test user")
  }

  const response = await fetch(`${apiBaseUrl}/api/v1/users/me`, {
    headers: {
      Authorization: `Bearer ${data.session.access_token}`,
    },
  })
  if (!response.ok) {
    throw new Error(`Failed to sync test user profile: ${response.status}`)
  }
  return await response.json()
}
