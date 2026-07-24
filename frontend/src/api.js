
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

export async function sendChatMessage(question, threadId) {
  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, thread_id: threadId }),
    })

    const data = await parseResponse(response)
    if (!data?.answer) throw new Error('The assistant returned an empty response.')
    return data
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error('Unable to reach the assistant. Make sure the API is running.', {
        cause: error,
      })
    }
    throw error
  }
}

// Keep both names available so existing and older components remain compatible.
export const askQuestion = sendChatMessage

export async function uploadDocument(file) {
  const formData = new FormData()
  formData.append('file', file)

  try {
    const response = await fetch(`${API_BASE_URL}/documents/upload`, {
      method: 'POST',
      body: formData,
    })
    return await parseResponse(response)
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error('Unable to upload. Make sure the API is running.', {
        cause: error,
      })
    }
    throw error
  }
}
