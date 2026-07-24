import { useState } from 'react'
import { sendChatMessage } from './api'
import ChatWindow from './components/ChatWindow'
import DocumentUpload from './components/DocumentUpload'
import './App.css'

function createId() {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID()
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

function App() {
  const [threadId] = useState(createId)
  const [messages, setMessages] = useState([])
  const [isReplying, setIsReplying] = useState(false)
  const [chatError, setChatError] = useState('')

  const handleSend = async (question) => {
    const userMessage = { id: createId(), role: 'user', content: question }

    setMessages((current) => [...current, userMessage])
    setChatError('')
    setIsReplying(true)

    try {
      const response = await sendChatMessage(question, threadId)
      setMessages((current) => [
        ...current,
        { id: createId(), role: 'assistant', content: response.answer },
      ])
    } catch (error) {
      setChatError(error instanceof Error ? error.message : 'Unable to send the question.')
    } finally {
      setIsReplying(false)
    }
  }

  return (
    <main className="app-shell">
      <header className="app-header">
        <a className="brand" href="/" aria-label="Knowledge Assistant home">
          <span className="brand-mark" aria-hidden="true">K</span>
          <span>
            <strong>Knowledge Assistant</strong>
            <small>Agentic RAG Workspace</small>
          </span>
        </a>
        <div className="status-pill">
          <span className="status-dot" aria-hidden="true" />
          Ready to assist
        </div>
      </header>

      <section className="hero-copy">
        <p className="eyebrow">YOUR KNOWLEDGE, AMPLIFIED</p>
        <h1>Ask better questions.<br />Get grounded answers.</h1>
        <p className="hero-description">
          Upload your documents and chat with an assistant that answers from the
          knowledge you provide.
        </p>
      </section>

      <section className="workspace" aria-label="Knowledge assistant workspace">
        <DocumentUpload />
        <ChatWindow
          messages={messages}
          isReplying={isReplying}
          error={chatError}
          onSend={handleSend}
        />
      </section>

      <footer>
        <span>Built for focused research</span>
        <span className="footer-separator" aria-hidden="true">•</span>
        <span>Session secured with a private thread</span>
      </footer>
    </main>
  )
}

export default App
