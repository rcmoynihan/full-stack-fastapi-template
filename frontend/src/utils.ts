import { AxiosError } from "axios"
import type { ApiError } from "./client"

function extractErrorMessage(err: ApiError | Error): string {
  if (err instanceof AxiosError) {
    return err.message
  }

  const errDetail = "body" in err ? (err.body as any)?.detail : undefined
  if (Array.isArray(errDetail) && errDetail.length > 0) {
    return errDetail[0].msg
  }
  return errDetail || err.message || "Something went wrong."
}

export const handleError = function (
  this: (msg: string) => void,
  err: ApiError | Error,
) {
  const errorMessage = extractErrorMessage(err)
  this(errorMessage)
}

export const getInitials = (name: string): string => {
  return name
    .split(" ")
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase()
}
