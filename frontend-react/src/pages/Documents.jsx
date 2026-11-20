
import { useEffect, useRef, useState } from 'react'
import {
  Upload, FileText, FileImage, File, Trash2,
  Download, FolderOpen, X
} from 'lucide-react'

const STORAGE_KEY = 'medbuddy_demo_documents'
const MAX_FILE_SIZE = 5 * 1024 * 1024

export default function Documents() {
  const [documents, setDocuments] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY)) || []
    } catch {
      return []
    }
  })

  const [category, setCategory] = useState('Lab Report')
  const [error, setError] = useState('')
  const [filter, setFilter] = useState('All')
  const fileInput = useRef(null)

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(documents))
    } catch {
      setError('Browser storage is full. Remove some documents and try again.')
    }
  }, [documents])

  const uploadDocument = (event) => {
    const file = event.target.files?.[0]
    if (!file) return

    setError('')

    if (file.size > MAX_FILE_SIZE) {
      setError('File size must be 5 MB or less.')
      event.target.value = ''
      return
    }

    const allowedTypes = [
      'application/pdf',
      'image/jpeg',
      'image/png',
      'image/webp',
    ]

    if (!allowedTypes.includes(file.type)) {
      setError('Please upload a PDF, JPG, PNG or WEBP file.')
      event.target.value = ''
      return
    }

    const reader = new FileReader()

    reader.onload = () => {
      const newDocument = {
        id: crypto.randomUUID(),
        name: file.name,
        type: file.type,
        size: file.size,
        category,
        date: new Date().toISOString().slice(0, 10),
        data: reader.result,
      }

      setDocuments((current) => [newDocument, ...current])
    }

    reader.onerror = () => {
      setError('Could not read this file. Please try again.')
    }

    reader.readAsDataURL(file)
    event.target.value = ''
  }

  const deleteDocument = (id) => {
    if (window.confirm('Are you sure you want to delete this document?')) {
      setDocuments((current) => current.filter((doc) => doc.id !== id))
    }
  }

  const downloadDocument = (doc) => {
    const link = document.createElement('a')
    link.href = doc.data
    link.download = doc.name
    document.body.appendChild(link)
    link.click()
    link.remove()
  }

  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const categories = [
    'All',
    'Lab Report',
    'Prescription',
    'Medical Scan',
    'Discharge Summary',
    'Other',
  ]

  const filteredDocuments = filter === 'All'
    ? documents
    : documents.filter((doc) => doc.category === filter)

  const FileIcon = ({ type }) =>
    type?.startsWith('image/')
      ? <FileImage size={22} />
      : type === 'application/pdf'
        ? <FileText size={22} />
        : <File size={22} />

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm text-[#84928c]">Your medical records</p>
        <h1 className="mt-1 text-2xl font-bold text-[#29433b]">Documents</h1>
        <p className="mt-1 text-sm text-[#84928c]">
          Keep your prescriptions, reports and medical documents together.
        </p>
      </div>

      <div className="panel p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-[#29433b]">Upload a document</h2>
            <p className="mt-1 text-sm text-[#84928c]">
              PDF, JPG, PNG or WEBP · Maximum 5 MB
            </p>
          </div>
          <FolderOpen size={30} className="text-[#39866f]" />
        </div>

        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          <label className="text-sm font-medium text-[#52665e]">
            Document category
            <select
              value={category}
              onChange={(event) => setCategory(event.target.value)}
              className="mt-2 w-full rounded-xl border border-[#e4ebe6] bg-[#fbfdfb] px-4 py-3 outline-none focus:border-[#78b9a1]"
            >
              {categories.filter((item) => item !== 'All').map((item) => (
                <option key={item}>{item}</option>
              ))}
            </select>
          </label>
        </div>

        <button
          onClick={() => fileInput.current?.click()}
          className="mt-5 flex w-full flex-col items-center justify-center rounded-2xl border-2 border-dashed border-[#b9d9ca] bg-[#f7fbf8] px-5 py-10 text-center transition hover:bg-[#edf7f1]"
        >
          <div className="rounded-2xl bg-[#e3f3e9] p-4 text-[#39866f]">
            <Upload size={28} />
          </div>
          <p className="mt-3 font-semibold text-[#39544a]">
            Click to choose a document
          </p>
          <p className="mt-1 text-xs text-[#84928c]">
            Select a file from your device
          </p>
        </button>

        <input
          ref={fileInput}
          type="file"
          accept=".pdf,.jpg,.jpeg,.png,.webp"
          onChange={uploadDocument}
          className="hidden"
        />

        {error && (
          <p className="mt-3 text-sm text-red-600">{error}</p>
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="panel p-5">
          <p className="text-sm text-[#84928c]">Total documents</p>
          <p className="mt-2 text-2xl font-bold text-[#29433b]">
            {documents.length}
          </p>
        </div>
        <div className="panel p-5">
          <p className="text-sm text-[#84928c]">Storage limit per file</p>
          <p className="mt-2 text-2xl font-bold text-[#29433b]">5 MB</p>
        </div>
      </div>

      <div className="panel p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-bold text-[#29433b]">Your documents</h2>
            <p className="mt-1 text-sm text-[#84928c]">
              Uploaded medical records
            </p>
          </div>

          <select
            value={filter}
            onChange={(event) => setFilter(event.target.value)}
            className="rounded-xl border border-[#e4ebe6] bg-white px-3 py-2 text-sm text-[#52665e] outline-none"
          >
            {categories.map((item) => (
              <option key={item}>{item}</option>
            ))}
          </select>
        </div>

        {filteredDocuments.length === 0 ? (
          <div className="py-14 text-center">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-[#eaf6f0] text-[#39866f]">
              <FolderOpen size={30} />
            </div>
            <h3 className="mt-4 font-semibold text-[#39544a]">
              No documents found
            </h3>
            <p className="mt-2 text-sm text-[#84928c]">
              Upload a medical document to see it here.
            </p>
          </div>
        ) : (
          <div className="mt-5 space-y-3">
            {filteredDocuments.map((doc) => (
              <div
                key={doc.id}
                className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-[#edf1ee] p-4"
              >
                <div className="flex min-w-0 items-center gap-3">
                  <div className="rounded-xl bg-[#eaf6f0] p-3 text-[#39866f]">
                    <FileIcon type={doc.type} />
                  </div>
                  <div className="min-w-0">
                    <p className="truncate font-semibold text-[#29433b]">
                      {doc.name}
                    </p>
                    <p className="mt-1 text-xs text-[#84928c]">
                      {doc.category} · {formatSize(doc.size)}
                    </p>
                    <p className="mt-1 text-xs text-[#84928c]">
                      Uploaded: {doc.date}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => downloadDocument(doc)}
                    title="Download document"
                    className="rounded-lg p-2 text-[#39866f] hover:bg-[#edf7f1]"
                  >
                    <Download size={19} />
                  </button>
                  <button
                    onClick={() => deleteDocument(doc.id)}
                    title="Delete document"
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

      <div className="rounded-2xl border border-[#f1e7d8] bg-[#fffaf2] p-4 text-sm leading-6 text-[#927d61]">
        Demo storage only: documents are saved in this browser's local storage.
        They are not encrypted or synced to your account or backend. Avoid
        uploading real sensitive medical records until secure backend storage
        and access controls are implemented.
      </div>
    </div>
  )
}
