import type { APIRequestContext } from "@playwright/test"

type MailpitAddress = {
  Address: string
  Name: string
}

type MailpitMessageSummary = {
  ID: string
  To: MailpitAddress[]
  Subject: string
}

type MailpitMessage = {
  HTML: string
  Text: string
}

async function findEmail({
  request,
  filter,
}: {
  request: APIRequestContext
  filter?: (email: MailpitMessageSummary) => boolean
}) {
  const response = await request.get(
    `${process.env.MAILPIT_HOST}/api/v1/messages`,
  )
  const payload = await response.json()
  let emails = payload.messages as MailpitMessageSummary[]

  if (filter) {
    emails = emails.filter(filter)
  }

  return emails[0] ?? null
}

export function findLastEmail({
  request,
  filter,
  timeout = 5000,
}: {
  request: APIRequestContext
  filter?: (email: MailpitMessageSummary) => boolean
  timeout?: number
}) {
  const timeoutPromise = new Promise<never>((_, reject) =>
    setTimeout(
      () => reject(new Error("Timeout while trying to get latest email")),
      timeout,
    ),
  )

  const checkEmails = async () => {
    while (true) {
      const emailData = await findEmail({ request, filter })

      if (emailData) {
        return emailData
      }
      await new Promise((resolve) => setTimeout(resolve, 100))
    }
  }

  return Promise.race([timeoutPromise, checkEmails()])
}

export async function getEmailHtml({
  request,
  id,
}: {
  request: APIRequestContext
  id: string
}) {
  const response = await request.get(
    `${process.env.MAILPIT_HOST}/api/v1/message/${id}`,
  )
  const email = (await response.json()) as MailpitMessage
  return email.HTML || email.Text
}
