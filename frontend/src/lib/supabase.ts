import { createClient } from "@supabase/supabase-js"

import { getSupabasePublishableKey, getSupabaseUrl } from "@/config"

export const supabase = createClient(
  getSupabaseUrl(),
  getSupabasePublishableKey(),
  {
    auth: {
      autoRefreshToken: true,
      detectSessionInUrl: true,
      persistSession: true,
    },
  },
)

export async function getSupabaseAccessToken(): Promise<string> {
  const { data } = await supabase.auth.getSession()
  return data.session?.access_token ?? ""
}

export async function hasSupabaseSession(): Promise<boolean> {
  const { data } = await supabase.auth.getSession()
  return Boolean(data.session)
}

export async function signOutSupabase(): Promise<void> {
  try {
    await supabase.auth.signOut()
  } finally {
    await supabase.auth.signOut({ scope: "local" })
  }
}
