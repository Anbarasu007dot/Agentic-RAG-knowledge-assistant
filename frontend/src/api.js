
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
async function parseResponse(response) {
  let data

  try {
    data = await response.json()
  } catch {
    data = null
  }

  if (!response.ok) {
    const detail = data?.detail
    const message =
      typeof detail === 'string'
        ? detail
        : data?.message || `Request failed with status ${response.status}.`
    throw new Error(message)
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
