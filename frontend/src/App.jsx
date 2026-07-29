import { useCallback, useEffect, useState } from 'react'
import { fetchChatSessions, fetchSessionMessages, sendChatMessage } from './api'
import ChatWindow from './components/ChatWindow'
import DocumentUpload from './components/DocumentUpload'
import './App.css'

function createId() {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID()
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

function App() {
  const [threadId, setThreadId] = useState(createId)
  const [messages, setMessages] = useState([])
  const [sessions, setSessions] = useState([])
  const [sessionsLoading, setSessionsLoading] = useState(true)
  const [sessionsError, setSessionsError] = useState('')
  const [historyLoading, setHistoryLoading] = useState(false)
  const [isReplying, setIsReplying] = useState(false)
  const [chatError, setChatError] = useState('')

  const loadSessions = useCallback(async () => {
    setSessionsLoading(true)
    setSessionsError('')
    try {
      setSessions(await fetchChatSessions())
    } catch (error) {
      setSessionsError(error instanceof Error ? error.message : 'Unable to load previous chats.')
    } finally {
      setSessionsLoading(false)
    }
  }, [])

  useEffect(() => {
    const timeoutId = setTimeout(loadSessions, 0)
    return () => clearTimeout(timeoutId)
  }, [loadSessions])

  const handleSelectSession = async (sessionId) => {
    if (historyLoading || isReplying || sessionId === threadId) return
    setHistoryLoading(true)
    setChatError('')
    try {
      const history = await fetchSessionMessages(sessionId)
      setMessages(history.map((message) => ({
        id: message.id,
        role: message.role,
        content: message.content,
      })))
      setThreadId(sessionId)
    } catch (error) {
      setChatError(error instanceof Error ? error.message : 'Unable to load this chat.')
    } finally {
      setHistoryLoading(false)
    }
  }

  const handleNewChat = () => {
    if (isReplying || historyLoading) return
    setThreadId(createId())
    setMessages([])
    setChatError('')
  }

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
      await loadSessions()
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
          sessions={sessions}
          activeSessionId={threadId}
          sessionsLoading={sessionsLoading}
          sessionsError={sessionsError}
          historyLoading={historyLoading}
          onSelectSession={handleSelectSession}
          onNewChat={handleNewChat}
          onRetrySessions={loadSessions}
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
