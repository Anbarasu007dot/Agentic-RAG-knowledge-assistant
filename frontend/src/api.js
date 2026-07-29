
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

function getErrorMessage(data, status) {
  const detail = data?.detail

  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((item) => item?.msg || item?.message)
      .filter(Boolean)
      .join(' ')
  }

  return data?.message || `Request failed with status ${status}.`
}

async function parseResponse(response) {
  if (response.status === 204) {
    if (!response.ok) throw new Error(`Request failed with status ${response.status}.`)
    return null
  }

  let data

  try {
    data = await response.json()
  } catch {
    data = null
  }

  if (!response.ok) {
    throw new Error(getErrorMessage(data, response.status))
  }

  return data
}

async function request(path, options, networkMessage) {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, options)
    return await parseResponse(response)
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error(networkMessage, { cause: error })
    }
    throw error
  }
}

export async function sendChatMessage(question, threadId) {
  const data = await request(
    '/chat',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, thread_id: threadId }),
    },
    'Unable to reach the assistant. Make sure the API is running.',
  )
  if (!data?.answer) throw new Error('The assistant returned an empty response.')
  return data
}

// Keep both names available so existing and older components remain compatible.
export const askQuestion = sendChatMessage

export async function uploadDocument(file) {
  const formData = new FormData()
  formData.append('file', file)

  return request(
    '/documents/upload',
    {
      method: 'POST',
      body: formData,
    },
    'Unable to upload. Make sure the API is running.',
  )
}

export const fetchDocuments = () =>
  request('/documents', undefined, 'Unable to load documents. Make sure the API is running.')

export const deleteDocument = (documentId) =>
  request(
    `/documents/${documentId}`,
    { method: 'DELETE' },
    'Unable to delete the document. Make sure the API is running.',
  )

export const fetchChatSessions = () =>
  request('/chat/sessions', undefined, 'Unable to load previous chats.')

export const fetchSessionMessages = (sessionId) =>
  request(
    `/chat/sessions/${encodeURIComponent(sessionId)}/messages`,
    undefined,
    'Unable to load messages for this chat.',
  )
