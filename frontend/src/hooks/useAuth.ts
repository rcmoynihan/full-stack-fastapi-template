import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { useEffect, useState } from "react"

import { type UserPublic, UsersService } from "@/client"
import { signOutSupabase, supabase } from "@/lib/supabase"
import { handleError } from "@/utils"
import useCustomToast from "./useCustomToast"

const AUTH_ERROR_MESSAGES: Record<string, string> = {
  "Invalid login credentials": "Incorrect email or password",
  "User already registered":
    "The user with this email already exists in the system",
  "A user with this email address has already been registered":
    "The user with this email already exists in the system",
}

const isLoggedIn = async () => {
  const { data } = await supabase.auth.getSession()
  return Boolean(data.session)
}

const useAuth = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showErrorToast } = useCustomToast()
  const [hasSession, setHasSession] = useState(false)

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setHasSession(Boolean(data.session))
    })
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setHasSession(Boolean(session))
      queryClient.invalidateQueries({ queryKey: ["currentUser"] })
    })
    return () => subscription.unsubscribe()
  }, [queryClient])

  const { data: user } = useQuery<UserPublic | null, Error>({
    queryKey: ["currentUser"],
    queryFn: UsersService.readUserMe,
    enabled: hasSession,
  })

  const signUpMutation = useMutation({
    mutationFn: async (data: {
      email: string
      password: string
      full_name: string
    }) => {
      const { error } = await supabase.auth.signUp({
        email: data.email,
        password: data.password,
        options: {
          data: {
            full_name: data.full_name,
          },
        },
      })
      if (error) {
        throw new Error(AUTH_ERROR_MESSAGES[error.message] ?? error.message)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["currentUser"] })
      navigate({ to: "/" })
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
    },
  })

  const login = async (data: { username: string; password: string }) => {
    const { error } = await supabase.auth.signInWithPassword({
      email: data.username,
      password: data.password,
    })
    if (error) {
      throw new Error(AUTH_ERROR_MESSAGES[error.message] ?? error.message)
    }
  }

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: () => {
      navigate({ to: "/" })
    },
    onError: handleError.bind(showErrorToast),
  })

  const logout = async () => {
    await signOutSupabase()
    queryClient.clear()
    navigate({ to: "/login" })
  }

  return {
    signUpMutation,
    loginMutation,
    logout,
    user,
  }
}

export { isLoggedIn }
export default useAuth
