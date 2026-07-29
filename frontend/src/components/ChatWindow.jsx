import { useEffect, useRef, useState } from 'react'
import ChatMessage from './ChatMessage'

function ChatWindow({
  messages, isReplying, error, onSend, sessions, activeSessionId,
  sessionsLoading, sessionsError, historyLoading, onSelectSession,
  onNewChat, onRetrySessions,
}) {
  const [question, setQuestion] = useState('')
  const messagesEndRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isReplying])

  const submit = (event) => {
    event.preventDefault()
    const trimmedQuestion = question.trim()
    if (!trimmedQuestion || isReplying) return
    setQuestion('')
    onSend(trimmedQuestion)
  }

  return (
    <article className="panel chat-panel">
      <div className="panel-heading chat-heading">
        <span className="section-number">02</span>
        <div>
          <h2>Ask your knowledge</h2>
          <p>Answers grounded in your indexed documents.</p>
        </div>
      </div>

      <section className="chat-history" aria-label="Previous chats">
        <div className="history-heading">
          <strong>Previous chats</strong>
          <button type="button" className="new-chat-button" onClick={onNewChat} disabled={isReplying || historyLoading}>
            + New Chat
          </button>
        </div>
        {sessionsError && (
          <div className="history-error" role="alert">
            <span>{sessionsError}</span>
            <button type="button" className="text-button" onClick={onRetrySessions}>Retry</button>
          </div>
        )}
        {sessionsLoading ? (
          <p className="history-state" role="status">Loading chats…</p>
        ) : sessions.length === 0 ? (
          <p className="history-state">No previous chats yet.</p>
        ) : (
          <div className="session-list">
            {sessions.map((session) => (
              <button
                type="button"
                key={session.id}
                className={`session-item ${session.id === activeSessionId ? 'active' : ''}`}
                onClick={() => onSelectSession(session.id)}
                disabled={historyLoading || isReplying}
                aria-pressed={session.id === activeSessionId}
                title={session.id}
              >
                <span>{session.id.slice(0, 8)}</span>
                <small>{new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(new Date(session.updated_at))}</small>
              </button>
            ))}
          </div>
        )}
      </section>

      <div className="messages" aria-live="polite">
        {historyLoading && <p className="history-loading" role="status">Loading conversation…</p>}
        {messages.length === 0 && (
          <div className="empty-chat">
            <span className="empty-mark" aria-hidden="true">✦</span>
            <h3>What would you like to know?</h3>
            <p>Upload a document, then ask a question about its contents.</p>
          </div>
        )}

        {messages.map((message) => (
          <ChatMessage key={message.id} role={message.role} content={message.content} />
        ))}

        {isReplying && (
          <div className="message-row assistant" role="status" aria-label="Assistant is typing">
            <span className="avatar" aria-hidden="true">K</span>
            <div className="message typing">
              <span /><span /><span />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {error && <div className="chat-error" role="alert">{error}</div>}

      <form className="chat-form" onSubmit={submit}>
        <label className="sr-only" htmlFor="question">Ask a question</label>
        <input
          id="question"
          type="text"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask a question about your documents…"
          disabled={isReplying}
          autoComplete="off"
        />
        <button
          className="send-button"
          type="submit"
          disabled={!question.trim() || isReplying}
          aria-label="Send question"
        >
          <span className="send-label">Send</span>
          <span aria-hidden="true">↑</span>
        </button>
      </form>
      <p className="input-hint">Press Enter to send</p>
    </article>
  )
}

export default ChatWindow
