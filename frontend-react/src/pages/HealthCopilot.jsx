
import { useState } from 'react'
import {
  Bot, Send, UserRound, ShieldCheck, HeartPulse,
  AlertTriangle, Sparkles, Plus, MessageCircle,
  Trash2
} from 'lucide-react'

const suggestions = [
  'What should I know about my medications?',
  'Help me understand my health records.',
  'What information should I share with my doctor?',
  'Can you explain a medical term?',
]

export default function HealthCopilot() {
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState([])
  const [notice, setNotice] = useState('')

  const sendMessage = (event) => {
    event.preventDefault()

    const trimmed = question.trim()
    if (!trimmed) return

    setMessages((current) => [
      ...current,
      {
        id: crypto.randomUUID(),
        text: trimmed,
      },
    ])

    setQuestion('')
    setNotice(
      'Your question is displayed in this demo. AI responses and safety checks will become available after the secure backend connection is configured.'
    )
  }

  const clearChat = () => {
    setMessages([])
    setNotice('')
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm text-[#84928c]">Your personal health assistant</p>
        <h1 className="mt-1 text-2xl font-bold text-[#29433b]">
          Health Copilot
        </h1>
        <p className="mt-1 text-sm text-[#84928c]">
          Ask questions and understand your health information.
        </p>
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
                Health information support
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

        <div className="min-h-[420px] space-y-6 bg-[#fbfdfb] p-5 sm:p-7">
          {messages.length === 0 ? (
            <div className="mx-auto max-w-xl py-8 text-center">
              <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-3xl bg-[#e7f5ef] text-[#39866f]">
                <HeartPulse size={38} />
              </div>

              <h2 className="mt-5 text-xl font-bold text-[#29433b]">
                Hello! How can I help you?
              </h2>
              <p className="mt-2 text-sm leading-6 text-[#84928c]">
                Ask about health information, medications or your medical
                records. MedBuddy is designed to help you understand your
                health context.
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
                      onClick={() => setQuestion(item)}
                      className="rounded-2xl border border-[#e7eee8] bg-white p-4 text-left text-sm text-[#52665e] transition hover:border-[#a8d2bd] hover:bg-[#f4faf6]"
                    >
                      {item}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            messages.map((message) => (
              <div key={message.id} className="flex justify-end gap-3">
                <div className="max-w-[85%] rounded-2xl rounded-tr-sm bg-[#39866f] px-4 py-3 text-sm leading-6 text-white">
                  {message.text}
                </div>
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[#e9edf5] text-[#63799e]">
                  <UserRound size={19} />
                </div>
              </div>
            ))
          )}

          {notice && (
            <div className="flex items-start gap-3 rounded-2xl border border-[#f1e7d8] bg-[#fffaf2] p-4">
              <AlertTriangle size={19} className="mt-0.5 shrink-0 text-[#bd8849]" />
              <p className="text-sm leading-6 text-[#927d61]">{notice}</p>
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
                placeholder="Ask MedBuddy a health question..."
                className="max-h-32 min-h-12 flex-1 resize-none bg-transparent px-3 py-3 text-sm text-[#39544a] outline-none placeholder:text-[#a0aaa4]"
              />

              <button
                type="submit"
                disabled={!question.trim()}
                className="mb-1 rounded-xl bg-[#39866f] p-3 text-white transition hover:bg-[#2e725e] disabled:cursor-not-allowed disabled:opacity-40"
                aria-label="Send message"
              >
                <Send size={19} />
              </button>
            </div>
            <p className="mt-2 text-center text-xs text-[#a0aaa4]">
              Press Enter to send · Shift + Enter for a new line
            </p>
          </form>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="flex items-start gap-3 rounded-2xl border border-[#e4eee7] bg-[#f5faf6] p-4">
          <ShieldCheck size={21} className="mt-0.5 shrink-0 text-[#39866f]" />
          <div>
            <p className="text-sm font-semibold text-[#39544a]">
              Safety-first approach
            </p>
            <p className="mt-1 text-xs leading-5 text-[#84928c]">
              Safety checks are designed to run before AI-generated responses.
            </p>
          </div>
        </div>

        <div className="flex items-start gap-3 rounded-2xl border border-[#e8e9f3] bg-[#f7f7fc] p-4">
          <MessageCircle size={21} className="mt-0.5 shrink-0 text-[#8585b5]" />
          <div>
            <p className="text-sm font-semibold text-[#555779]">
              Health context
            </p>
            <p className="mt-1 text-xs leading-5 text-[#85859b]">
              Personalized context will be available after account and backend integration.
            </p>
          </div>
        </div>
      </div>

      <p className="text-center text-xs leading-5 text-[#a0aaa4]">
        MedBuddy provides health information support, not a medical diagnosis.
        For emergencies, contact local emergency services immediately.
      </p>
    </div>
  )
}
