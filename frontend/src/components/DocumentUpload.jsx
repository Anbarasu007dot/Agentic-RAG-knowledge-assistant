import { useCallback, useEffect, useRef, useState } from 'react'
import { deleteDocument, fetchDocuments, uploadDocument } from '../api'

const ALLOWED_EXTENSIONS = ['txt', 'pdf', 'docx']

function DocumentUpload() {
  const inputRef = useRef(null)
  const [file, setFile] = useState(null)
  const [isUploading, setIsUploading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [documents, setDocuments] = useState([])
  const [documentsLoading, setDocumentsLoading] = useState(true)
  const [documentsError, setDocumentsError] = useState('')
  const [confirmingId, setConfirmingId] = useState(null)
  const [deletingId, setDeletingId] = useState(null)
  const [deleteNotice, setDeleteNotice] = useState('')

  const loadDocuments = useCallback(async () => {
    setDocumentsLoading(true)
    setDocumentsError('')
    try {
      setDocuments(await fetchDocuments())
    } catch (loadError) {
      setDocumentsError(loadError instanceof Error ? loadError.message : 'Unable to load documents.')
    } finally {
      setDocumentsLoading(false)
    }
  }, [])

  useEffect(() => {
    const timeoutId = setTimeout(loadDocuments, 0)
    return () => clearTimeout(timeoutId)
  }, [loadDocuments])

  const chooseFile = (selectedFile) => {
    setResult(null)
    setError('')

    if (!selectedFile) {
      setFile(null)
      return
    }

    const extension = selectedFile.name.split('.').pop()?.toLowerCase()
    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      setFile(null)
      setError('Please select a TXT, PDF, or DOCX file.')
      if (inputRef.current) inputRef.current.value = ''
      return
    }

    setFile(selectedFile)
  }

  const handleUpload = async () => {
    if (!file || isUploading) return

    setIsUploading(true)
    setError('')
    setResult(null)

    try {
      const data = await uploadDocument(file)
      setResult(data)
      await loadDocuments()
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : 'Unable to upload the document.')
    } finally {
      setIsUploading(false)
    }
  }

  const handleDelete = async (document) => {
    if (deletingId !== null) return
    setDeletingId(document.id)
    setDocumentsError('')
    setDeleteNotice('')
    try {
      await deleteDocument(document.id)
      setDocuments((current) => current.filter((item) => item.id !== document.id))
      setConfirmingId(null)
      setDeleteNotice(`${document.filename} was deleted.`)
    } catch (deleteError) {
      setDocumentsError(deleteError instanceof Error ? deleteError.message : 'Unable to delete the document.')
    } finally {
      setDeletingId(null)
    }
  }

  const formatDate = (value) => new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))

  return (
    <article className="panel upload-panel">
      <div className="panel-heading">
        <span className="section-number">01</span>
        <div>
          <h2>Add knowledge</h2>
          <p>Upload a source for the assistant to learn from.</p>
        </div>
      </div>

      <div
        className={`drop-zone ${file ? 'has-file' : ''}`}
        onClick={() => !isUploading && inputRef.current?.click()}
        onKeyDown={(event) => {
          if ((event.key === 'Enter' || event.key === ' ') && !isUploading) {
            event.preventDefault()
            inputRef.current?.click()
          }
        }}
        role="button"
        tabIndex={0}
        aria-label="Choose a document to upload"
      >
        <input
          ref={inputRef}
          type="file"
          accept=".txt,.pdf,.docx"
          onChange={(event) => chooseFile(event.target.files?.[0])}
          disabled={isUploading}
        />
        <span className="upload-icon" aria-hidden="true">↑</span>
        {file ? (
          <>
            <strong className="selected-name">{file.name}</strong>
            <span>{(file.size / 1024).toFixed(1)} KB · Click to replace</span>
          </>
        ) : (
          <>
            <strong>Choose a document</strong>
            <span>or drop it here</span>
          </>
        )}
        <div className="file-types">
          <span>TXT</span><span>PDF</span><span>DOCX</span>
        </div>
      </div>

      {isUploading && (
        <div className="upload-progress" role="status">
          <div className="progress-track"><span /></div>
          <p>Uploading and indexing your document…</p>
        </div>
      )}

      {result && (
        <div className="notice success" role="status">
          <span className="notice-icon" aria-hidden="true">✓</span>
          <div>
            <strong>Document indexed</strong>
            <p>{result.filename} · {result.indexed_chunks} chunks ready</p>
          </div>
        </div>
      )}

      {error && <div className="notice error" role="alert">{error}</div>}

      <button
        className="button secondary-button"
        type="button"
        onClick={handleUpload}
        disabled={!file || isUploading}
      >
        {isUploading ? 'Indexing…' : 'Upload & index'}
        {!isUploading && <span aria-hidden="true">→</span>}
      </button>

      <section className="document-library" aria-labelledby="document-library-title">
        <div className="library-heading">
          <h3 id="document-library-title">Your documents</h3>
          <button type="button" className="text-button" onClick={loadDocuments} disabled={documentsLoading}>
            Refresh
          </button>
        </div>
        {deleteNotice && <div className="notice success compact" role="status">{deleteNotice}</div>}
        {documentsError && <div className="notice error compact" role="alert">{documentsError}</div>}
        {documentsLoading ? (
          <p className="library-state" role="status">Loading documents…</p>
        ) : documents.length === 0 ? (
          <p className="library-state">No uploaded documents yet.</p>
        ) : (
          <ul className="document-list">
            {documents.map((document) => (
              <li key={document.id} className="document-item">
                <div className="document-summary">
                  <strong title={document.filename}>{document.filename}</strong>
                  <span>{document.source_type?.toUpperCase() || 'DOCUMENT'} · {formatDate(document.upload_time)}</span>
                  <span className={`status-badge ${document.status}`}>{document.status}</span>
                </div>
                {confirmingId === document.id ? (
                  <div className="delete-confirmation" role="alertdialog" aria-label={`Delete ${document.filename}`}>
                    <p>Delete its metadata, uploaded file, and ChromaDB vectors?</p>
                    <div>
                      <button type="button" className="text-button danger" onClick={() => handleDelete(document)} disabled={deletingId === document.id}>
                        {deletingId === document.id ? 'Deleting…' : 'Delete'}
                      </button>
                      <button type="button" className="text-button" onClick={() => setConfirmingId(null)} disabled={deletingId === document.id}>Cancel</button>
                    </div>
                  </div>
                ) : (
                  <button type="button" className="delete-button" aria-label={`Delete ${document.filename}`} onClick={() => setConfirmingId(document.id)} disabled={deletingId !== null}>×</button>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>
    </article>
  )
}

export default DocumentUpload
