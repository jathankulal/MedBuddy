import { useEffect, useState } from 'react'
import {
  Bot, Send, UserRound, ShieldCheck, HeartPulse,
  AlertTriangle, Sparkles, Trash2,
  AlertCircle, Loader2, BookOpen
} from 'lucide-react'
import { api } from '../services/api'

const suggestions = [
  'What should I know about my medications and known allergies?',
  'Summarize the key findings from my uploaded lab report.',
  'What warning signs or symptoms should I watch for?',
  'I am experiencing severe chest pressure and shortness of breath.',
]

export default function HealthCopilot() {
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [documents, setDocuments] = useState([])
  const [selectedDocId, setSelectedDocId] = useState('all')

  useEffect(() => {
    api.getDocuments()
      .then(docs => setDocuments(docs || []))
      .catch(() => {})
  }, [])

  const sendMessage = async (event, overrideText) => {
    if (event) event.preventDefault()

    const textToSend = (overrideText || question).trim()
    if (!textToSend || loading) return

    const userMsgId = crypto.randomUUID()
    const newMessages = [
      ...messages,
      {
        id: userMsgId,
        sender: 'user',
        text: textToSend,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]

    setMessages(newMessages)
    if (!overrideText) setQuestion('')
    setLoading(true)

    try {
      const docIds = selectedDocId === 'all'
        ? documents.map(d => d.id)
        : (selectedDocId ? [selectedDocId] : [])

      const response = await api.sendMessage({
        message: textToSend,
        document_ids: docIds,
        episode_id: null,
      })

      const botMsg = {
        id: crypto.randomUUID(),
        sender: 'assistant',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        answer: response.answer,
        citations: response.citations || [],
        safety: response.safety || {},
        context_used: response.context_used,
        context_sources: response.context_sources || [],
        missing_information: response.missing_information || [],
        disclaimer: response.disclaimer,
        response_mode: response.response_mode || 'normal',
        isEmergency: response.response_mode === 'emergency' || Boolean(response.safety?.emergency),
      }

      setMessages([...newMessages, botMsg])
    } catch (err) {
      const isSafetyError = err.code === 'ERR_SAFETY_ENGINE'
      const errorMsg = {
        id: crypto.randomUUID(),
        sender: 'assistant',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        isError: true,
        errorType: isSafetyError ? 'safety_engine' : 'general',
        answer: isSafetyError
          ? `Safety Engine Failure: ${err.message}. Gemini generation was blocked per safety fail-closed policy.`
          : `Processing Error: ${err.message}`,
        disclaimer: 'Safety checks prevent unverified medical advice from being generated.',
      }
      setMessages([...newMessages, errorMsg])
    } finally {
      setLoading(false)
    }
  }

  const clearChat = () => {
    setMessages([])
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm text-[#84928c]">Your personal health assistant</p>
          <h1 className="mt-1 text-2xl font-bold text-[#29433b]">
            Health Copilot
          </h1>
          <p className="mt-1 text-sm text-[#84928c]">
            RAG-grounded with persistent profile, care episodes & indexed PDF context.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-xs font-semibold text-[#52665e]">
            <span>Document Scope:</span>
            <select
              value={selectedDocId}
              onChange={(e) => setSelectedDocId(e.target.value)}
              className="rounded-xl border border-[#e4ebe6] bg-white px-3 py-2 text-xs text-[#39544a] outline-none"
            >
              <option value="all">All Indexed PDFs ({documents.length})</option>
              {documents.map((d) => (
                <option key={d.id} value={d.id}>{d.filename}</option>
              ))}
            </select>
          </label>
        </div>
      </div>

      <div className="overflow-hidden rounded-3xl border border-[#e8efea] bg-white shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#edf1ee] p-5">
          <div className="flex items-center gap-3">
            <div className="rounded-2xl bg-[#e5f5ed] p-3 text-[#39866f]">
              <Bot size={25} />
            </div>
            <div>
              <h2 className="font-bold text-[#29433b]">MedBuddy Assistant</h2>
              <p className="text-xs text-[#84928c]">
                Real FastAPI backend · RAG vector retrieval · Safety Engine verified
              </p>
            </div>
          </div>

          <button
            onClick={clearChat}
            className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm text-[#84928c] hover:bg-[#f3f8f5]"
          >
            <Trash2 size={16} /> Clear chat
          </button>
        </div>

        <div className="min-h-[460px] max-h-[650px] space-y-6 overflow-y-auto bg-[#fbfdfb] p-5 sm:p-7">
          {messages.length === 0 ? (
            <div className="mx-auto max-w-xl py-8 text-center">
              <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-3xl bg-[#e7f5ef] text-[#39866f]">
                <HeartPulse size={38} />
              </div>

              <h2 className="mt-5 text-xl font-bold text-[#29433b]">
                Hello! How can I help you today?
              </h2>
              <p className="mt-2 text-sm leading-6 text-[#84928c]">
                Ask questions about your health profile, medications, care episodes, or uploaded documents.
                All responses undergo safety assessments before generation.
              </p>

              <div className="mt-8 text-left">
                <p className="mb-3 flex items-center gap-2 text-sm font-semibold text-[#52665e]">
                  <Sparkles size={16} className="text-[#d69b5d]" />
                  Try asking
                </p>

                <div className="grid gap-3 sm:grid-cols-2">
                  {suggestions.map((item) => (
                    <button
                      key={item}
                      onClick={() => sendMessage(null, item)}
                      className="rounded-2xl border border-[#e7eee8] bg-white p-4 text-left text-sm text-[#52665e] transition hover:border-[#a8d2bd] hover:bg-[#f4faf6]"
                    >
                      {item}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            messages.map((message) => {
              if (message.sender === 'user') {
                return (
                  <div key={message.id} className="flex justify-end gap-3">
                    <div className="max-w-[85%] rounded-2xl rounded-tr-sm bg-[#39866f] px-5 py-3.5 text-sm leading-6 text-white shadow-sm sm:max-w-[75%]">
                      {message.text}
                    </div>
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[#e9edf5] text-[#63799e]">
                      <UserRound size={19} />
                    </div>
                  </div>
                )
              }

              // Assistant message
              if (message.isError) {
                return (
                  <div key={message.id} className="flex justify-start gap-3">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[#fce9e6] text-[#b0483c]">
                      <AlertCircle size={19} />
                    </div>
                    <div className="max-w-[85%] space-y-2 rounded-2xl rounded-tl-sm border border-[#f3d0ca] bg-[#fff6f5] p-5 text-sm text-[#9b3a30] sm:max-w-[80%]">
                      <p className="font-bold">Safety or Processing Notice</p>
                      <p className="text-sm leading-6">{message.answer}</p>
                      {message.disclaimer && (
                        <p className="text-xs text-[#b85246]">{message.disclaimer}</p>
                      )}
                    </div>
                  </div>
                )
              }

              if (message.isEmergency) {
                return (
                  <div key={message.id} className="flex justify-start gap-3">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[#ffe4e1] text-[#c92a2a]">
                      <AlertTriangle size={20} />
                    </div>
                    <div className="max-w-[90%] space-y-3 rounded-2xl rounded-tl-sm border-2 border-[#e03131] bg-[#fff5f5] p-5 text-[#881313] sm:max-w-[85%]">
                      <div className="flex items-center gap-2 text-base font-bold text-[#c92a2a]">
                        <AlertTriangle size={20} />
                        <span>URGENT: Potential Medical Emergency Detected</span>
                      </div>

                      <p className="text-sm font-semibold leading-6 text-[#961b1b]">
                        {message.answer}
                      </p>

                      {message.safety?.emergency_reason && (
                        <div className="rounded-xl bg-[#ffe3e3] p-3 text-xs text-[#a61e1e]">
                          <strong>Triggered reason:</strong> {message.safety.emergency_reason}
                        </div>
                      )}

                      <div className="border-t border-[#fcc] pt-2 text-xs text-[#a61e1e]">
                        <strong>Immediate Action Required:</strong> Gemini AI synthesis was completely bypassed. Call 911, 112, or your local emergency number immediately.
                      </div>
                    </div>
                  </div>
                )
              }

              // Normal Assistant Response
              return (
                <div key={message.id} className="flex justify-start gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[#e5f5ed] text-[#39866f]">
                    <Bot size={20} />
                  </div>
                  <div className="max-w-[90%] space-y-4 rounded-2xl rounded-tl-sm border border-[#e7eee8] bg-white p-5 text-[#30483e] shadow-sm sm:max-w-[85%]">

                    {/* Safety Warnings Banner if present */}
                    {message.safety?.warnings?.length > 0 && (
                      <div className="space-y-1 rounded-xl border border-[#f5dfb8] bg-[#fffaf0] p-3 text-xs text-[#9c6a2c]">
                        <p className="font-semibold flex items-center gap-1.5 text-[#8a5b22]">
                          <AlertTriangle size={14} />
                          Safety Engine Advisory
                        </p>
                        {message.safety.warnings.map((w, idx) => (
                          <p key={idx} className="leading-5">
                            • <strong>{w.code}:</strong> {w.message}
                          </p>
                        ))}
                        {message.safety.requires_human_review && (
                          <p className="font-medium text-[#a06822] mt-1">
                            ⚠️ Professional healthcare human review recommended.
                          </p>
                        )}
                      </div>
                    )}

                    {/* AI Answer Text */}
                    <div className="whitespace-pre-wrap text-sm leading-7 text-[#344c41]">
                      {message.answer}
                    </div>

                    {/* Context Sources Pill */}
                    {message.context_sources?.length > 0 && (
                      <div className="flex flex-wrap items-center gap-1.5 pt-1 text-[11px] text-[#71877b]">
                        <span className="font-medium">Context used:</span>
                        {message.context_sources.map((src) => (
                          <span key={src} className="rounded-md bg-[#edf4f0] px-2 py-0.5 font-semibold text-[#3b6d57]">
                            {src}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Citations List */}
                    {message.citations?.length > 0 && (
                      <div className="rounded-xl border border-[#e4eee7] bg-[#f8fbf9] p-3 text-xs">
                        <p className="font-bold flex items-center gap-1.5 text-[#376b55] mb-2">
                          <BookOpen size={14} />
                          Document Citations ({message.citations.length})
                        </p>
                        <div className="space-y-2">
                          {message.citations.map((c, idx) => (
                            <div key={idx} className="rounded-lg border border-[#e1ece4] bg-white p-2.5">
                              <div className="flex items-center justify-between text-[#2e5944] font-semibold">
                                <span>📄 {c.filename}</span>
                                <span className="rounded bg-[#e8f4ec] px-1.5 py-0.5 text-[10px] text-[#347353]">
                                  Page {c.page_number}
                                </span>
                              </div>
                              <p className="mt-1 text-xs text-[#60756b] italic line-clamp-3">
                                "{c.excerpt}"
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Disclaimer */}
                    {message.disclaimer && (
                      <p className="border-t border-[#edf1ee] pt-2 text-[11px] leading-4 text-[#9aa89f]">
                        {message.disclaimer}
                      </p>
                    )}
                  </div>
                </div>
              )
            })
          )}

          {loading && (
            <div className="flex justify-start gap-3">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[#e5f5ed] text-[#39866f]">
                <Bot size={20} />
              </div>
              <div className="flex items-center gap-2 rounded-2xl rounded-tl-sm border border-[#e7eee8] bg-white px-5 py-4 text-xs text-[#62776c] shadow-sm">
                <Loader2 size={16} className="animate-spin text-[#39866f]" />
                <span>Consulting safety engine & retrieving document context...</span>
              </div>
            </div>
          )}
        </div>

        <div className="border-t border-[#edf1ee] bg-white p-4 sm:p-5">
          <form onSubmit={sendMessage}>
            <div className="flex items-end gap-3 rounded-2xl border border-[#e4ebe6] bg-[#fbfdfb] p-2 focus-within:border-[#91c9ad]">
              <textarea
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault()
                    event.currentTarget.form.requestSubmit()
                  }
                }}
                rows={2}
                disabled={loading}
                placeholder="Ask MedBuddy a health question (e.g. check medications or ask about uploaded PDF)..."
                className="max-h-32 min-h-12 flex-1 resize-none bg-transparent px-3 py-3 text-sm text-[#39544a] outline-none placeholder:text-[#a0aaa4] disabled:opacity-60"
              />

              <button
                type="submit"
                disabled={!question.trim() || loading}
                className="mb-1 rounded-xl bg-[#39866f] p-3 text-white transition hover:bg-[#2e725e] disabled:cursor-not-allowed disabled:opacity-40"
                aria-label="Send message"
              >
                {loading ? <Loader2 size={19} className="animate-spin" /> : <Send size={19} />}
              </button>
            </div>
            <p className="mt-2 text-center text-xs text-[#a0aaa4]">
              Press Enter to send · Shift + Enter for a new line · Safety-checked before generation
            </p>
          </form>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="flex items-start gap-3 rounded-2xl border border-[#e4eee7] bg-[#f5faf6] p-4">
          <ShieldCheck size={21} className="mt-0.5 shrink-0 text-[#39866f]" />
          <div>
            <p className="text-sm font-semibold text-[#39544a]">
              Safety-first engine verification
            </p>
            <p className="mt-1 text-xs leading-5 text-[#84928c]">
              Emergencies trigger immediate guidance bypassing LLMs. Drug-allergy conflicts and ingredient overlaps are checked against your persistent health profile.
            </p>
          </div>
        </div>

        <div className="flex items-start gap-3 rounded-2xl border border-[#e8e9f3] bg-[#f7f7fc] p-4">
          <BookOpen size={21} className="mt-0.5 shrink-0 text-[#8585b5]" />
          <div>
            <p className="text-sm font-semibold text-[#555779]">
              Grounded PDF citations
            </p>
            <p className="mt-1 text-xs leading-5 text-[#85859b]">
              Answers cite exact document filenames and page numbers from ChromaDB vector search.
            </p>
          </div>
        </div>
      </div>

      <p className="text-center text-xs leading-5 text-[#a0aaa4]">
        MedBuddy provides health information support, not a medical diagnosis. For life-threatening emergencies, seek immediate emergency medical care.
      </p>
    </div>
  )
}
