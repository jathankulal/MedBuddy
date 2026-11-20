import { useEffect, useRef, useState } from 'react'
import {
  Upload, FileText, Trash2, FolderOpen, AlertCircle,
  CheckCircle2, Loader2, ShieldCheck, Database
} from 'lucide-react'
import { api } from '../services/api'

const MAX_FILE_SIZE = 10 * 1024 * 1024 // 10 MB per backend specification

export default function Documents() {
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const fileInput = useRef(null)

  const loadDocuments = async () => {
    setLoading(true)
    try {
      const data = await api.getDocuments()
      setDocuments(data || [])
    } catch (err) {
      setError(err.message || 'Failed to load documents from backend.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let mounted = true
    async function load() {
      try {
        const data = await api.getDocuments()
        if (mounted) setDocuments(data || [])
      } catch (err) {
        if (mounted) setError(err.message || 'Failed to load documents from backend.')
      } finally {
        if (mounted) setLoading(false)
      }
    }
    load()
    return () => { mounted = false }
  }, [])

  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0]
    if (!file) return

    setError('')
    setSuccess('')

    if (file.size > MAX_FILE_SIZE) {
      setError('File size must be 10 MB or less.')
      event.target.value = ''
      return
    }

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('MedBuddy currently indexes PDF documents. Please upload a PDF file.')
      event.target.value = ''
      return
    }

    setUploading(true)
    setUploadProgress(10)

    try {
      const result = await api.uploadDocument(file, (progressEvent) => {
        if (progressEvent.total) {
          const percent = Math.round((progressEvent.loaded * 90) / progressEvent.total)
          setUploadProgress(percent)
        }
      })

      setUploadProgress(100)
      setSuccess(`Document "${result.filename}" uploaded, parsed (${result.page_count} pages), and indexed into ChromaDB!`)
      await loadDocuments()
    } catch (err) {
      setError(err.message || 'Failed to upload and index PDF.')
    } finally {
      setUploading(false)
      setUploadProgress(0)
      if (event.target) event.target.value = ''
    }
  }

  const deleteDocument = async (id, filename) => {
    if (window.confirm(`Are you sure you want to delete "${filename}"? This will remove its chunks from the vector database.`)) {
      try {
        setError('')
        setSuccess('')
        await api.deleteDocument(id)
        setDocuments((current) => current.filter((doc) => doc.id !== id))
        setSuccess(`Document "${filename}" and its vector embeddings deleted.`)
      } catch (err) {
        setError(err.message || 'Failed to delete document.')
      }
    }
  }

  const formatSize = (bytes) => {
    if (!bytes) return '0 B'
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm text-[#84928c]">Your medical records & RAG knowledge base</p>
        <h1 className="mt-1 text-2xl font-bold text-[#29433b]">Documents</h1>
        <p className="mt-1 text-sm text-[#84928c]">
          Upload medical PDFs. MedBuddy extracts pages, generates embeddings, and indexes them in ChromaDB for grounded Health Copilot answers.
        </p>
      </div>

      {success && (
        <div className="flex items-center gap-2 rounded-xl bg-[#eaf5ed] p-4 text-sm font-medium text-[#4d8564]">
          <CheckCircle2 size={18} />
          {success}
        </div>
      )}

      {error && (
        <div className="flex items-start gap-2 rounded-xl bg-[#fdf5f4] p-4 text-sm text-[#9e4438]">
          <AlertCircle size={18} className="mt-0.5 shrink-0" />
          <p>{error}</p>
        </div>
      )}

      <div className="panel p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-[#29433b]">Upload a PDF document</h2>
            <p className="mt-1 text-sm text-[#84928c]">
              PDF format · Maximum 10 MB · Up to 100 pages
            </p>
          </div>
          <FolderOpen size={30} className="text-[#39866f]" />
        </div>

        <button
          onClick={() => fileInput.current?.click()}
          disabled={uploading}
          className="mt-5 flex w-full flex-col items-center justify-center rounded-2xl border-2 border-dashed border-[#b9d9ca] bg-[#f7fbf8] px-5 py-10 text-center transition hover:bg-[#edf7f1] disabled:opacity-60"
        >
          <div className="rounded-2xl bg-[#e3f3e9] p-4 text-[#39866f]">
            {uploading ? <Loader2 size={28} className="animate-spin" /> : <Upload size={28} />}
          </div>
          <p className="mt-3 font-semibold text-[#39544a]">
            {uploading ? 'Uploading and indexing in ChromaDB...' : 'Click to select and index a medical PDF'}
          </p>
          <p className="mt-1 text-xs text-[#84928c]">
            {uploading ? `Processing... ${uploadProgress}%` : 'PyMuPDF page-by-page extraction & Sentence-Transformers embedding'}
          </p>
        </button>

        <input
          ref={fileInput}
          type="file"
          accept=".pdf,application/pdf"
          onChange={handleFileUpload}
          className="hidden"
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="panel p-5">
          <p className="text-sm text-[#84928c]">Total documents</p>
          <p className="mt-2 text-2xl font-bold text-[#29433b]">{documents.length}</p>
        </div>
        <div className="panel p-5">
          <p className="text-sm text-[#84928c]">ChromaDB Indexed Chunks</p>
          <p className="mt-2 text-2xl font-bold text-[#39866f]">
            {documents.reduce((acc, d) => acc + (d.chunk_count || 0), 0)}
          </p>
        </div>
        <div className="panel p-5">
          <p className="text-sm text-[#84928c]">Vector Backend</p>
          <div className="mt-2 flex items-center gap-2 font-bold text-[#29433b]">
            <Database size={18} className="text-[#39866f]" />
            <span>Persistent ChromaDB</span>
          </div>
        </div>
      </div>

      <div className="panel p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-bold text-[#29433b]">Indexed documents</h2>
            <p className="mt-1 text-sm text-[#84928c]">
              Documents available for Health Copilot retrieval context.
            </p>
          </div>
        </div>

        {loading ? (
          <div className="flex min-h-[160px] items-center justify-center gap-2">
            <Loader2 className="animate-spin text-[#39866f]" size={24} />
            <span className="text-sm text-[#798e83]">Loading documents...</span>
          </div>
        ) : documents.length === 0 ? (
          <div className="py-14 text-center">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-[#eaf6f0] text-[#39866f]">
              <FolderOpen size={30} />
            </div>
            <h3 className="mt-4 font-semibold text-[#39544a]">No documents uploaded yet</h3>
            <p className="mt-2 text-sm text-[#84928c]">
              Upload a medical PDF to enable grounded retrieval in Health Copilot.
            </p>
          </div>
        ) : (
          <div className="mt-5 space-y-3">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-[#edf1ee] p-4 transition hover:border-[#d7e6de]"
              >
                <div className="flex min-w-0 items-center gap-3">
                  <div className="rounded-xl bg-[#eaf6f0] p-3 text-[#39866f]">
                    <FileText size={22} />
                  </div>
                  <div className="min-w-0">
                    <p className="truncate font-semibold text-[#29433b]">
                      {doc.filename}
                    </p>
                    <p className="mt-1 text-xs text-[#84928c]">
                      {formatSize(doc.size_bytes)} · {doc.page_count} {doc.page_count === 1 ? 'page' : 'pages'} · {doc.chunk_count} indexed chunks
                    </p>
                    <div className="mt-1.5 flex items-center gap-2">
                      <span className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-semibold ${doc.status === 'indexed' ? 'bg-[#e7f5ef] text-[#28745f]' : 'bg-[#fff0ed] text-[#b0483c]'}`}>
                        {doc.status === 'indexed' ? <CheckCircle2 size={12} /> : <AlertCircle size={12} />}
                        {doc.status}
                      </span>
                      <span className="text-[11px] text-[#9ba8a0]">
                        Uploaded {doc.uploaded_at?.slice(0, 10)}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => deleteDocument(doc.id, doc.filename)}
                    title="Delete document and vector chunks"
                    className="rounded-lg p-2 text-[#c17b72] hover:bg-[#fff0ed]"
                  >
                    <Trash2 size={19} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="flex items-start gap-3 rounded-2xl border border-[#d6ecde] bg-[#f0f9f3] p-4 text-sm leading-6 text-[#356149]">
        <ShieldCheck className="mt-0.5 shrink-0 text-[#39866f]" size={20} />
        <div>
          <p className="font-semibold text-[#294937]">Real RAG Ingestion Pipeline</p>
          <p className="mt-0.5 text-xs text-[#4c725c]">
            PDFs uploaded to MedBuddy are validated (checking magic bytes), extracted page-by-page, chunked, and embedded into local ChromaDB storage. When asking queries in Health Copilot, relevant excerpts are retrieved and cited with exact page numbers.
          </p>
        </div>
      </div>
    </div>
  )
}
