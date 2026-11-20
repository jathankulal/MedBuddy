
import { useEffect, useState } from 'react'
import { Plus, Activity, CalendarDays, Trash2, X, ClipboardList } from 'lucide-react'

const STORAGE_KEY = 'medbuddy_demo_episodes'

const emptyForm = {
  title: '',
  date: new Date().toISOString().slice(0, 10),
  category: 'Illness',
  symptoms: '',
  notes: '',
  status: 'Ongoing',
}

export default function CareEpisodes() {
  const [episodes, setEpisodes] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY)) || []
    } catch {
      return []
    }
  })

  const [form, setForm] = useState(emptyForm)
  const [showForm, setShowForm] = useState(false)

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(episodes))
  }, [episodes])

  const updateField = (event) => {
    setForm({ ...form, [event.target.name]: event.target.value })
  }

  const saveEpisode = (event) => {
    event.preventDefault()

    if (!form.title.trim() || !form.date) return

    setEpisodes((current) => [
      { ...form, id: crypto.randomUUID() },
      ...current,
    ])

    setForm(emptyForm)
    setShowForm(false)
  }

  const deleteEpisode = (id) => {
    if (window.confirm('Remove this care episode?')) {
      setEpisodes((current) => current.filter((episode) => episode.id !== id))
    }
  }

  const statusStyle = (status) =>
    status === 'Recovered'
      ? 'bg-[#e7f5ef] text-[#28745f]'
      : status === 'Ongoing'
        ? 'bg-[#fff2e5] text-[#a36e36]'
        : 'bg-[#edf1f8] text-[#63799e]'

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm text-[#84928c]">Your health journey</p>
          <h1 className="mt-1 text-2xl font-bold text-[#29433b]">Care Episodes</h1>
          <p className="mt-1 text-sm text-[#84928c]">
            Keep a record of illnesses, visits and recovery updates.
          </p>
        </div>

        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 rounded-xl bg-[#39866f] px-4 py-3 text-sm font-semibold text-white hover:bg-[#2e725e]"
        >
          <Plus size={18} /> Add episode
        </button>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="panel p-5">
          <p className="text-sm text-[#84928c]">Total episodes</p>
          <p className="mt-2 text-2xl font-bold text-[#29433b]">{episodes.length}</p>
        </div>
        <div className="panel p-5">
          <p className="text-sm text-[#84928c]">Ongoing</p>
          <p className="mt-2 text-2xl font-bold text-[#b17b43]">
            {episodes.filter((item) => item.status === 'Ongoing').length}
          </p>
        </div>
        <div className="panel p-5">
          <p className="text-sm text-[#84928c]">Recovered</p>
          <p className="mt-2 text-2xl font-bold text-[#39866f]">
            {episodes.filter((item) => item.status === 'Recovered').length}
          </p>
        </div>
      </div>

      {showForm && (
        <div className="panel p-6">
          <div className="mb-5 flex items-center justify-between">
            <h2 className="text-lg font-bold text-[#29433b]">New care episode</h2>
            <button
              onClick={() => setShowForm(false)}
              className="rounded-lg p-2 text-[#84928c] hover:bg-[#f3f8f5]"
            >
              <X size={20} />
            </button>
          </div>

          <form onSubmit={saveEpisode} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="text-sm font-medium text-[#52665e]">
                Episode title *
                <input
                  name="title"
                  value={form.title}
                  onChange={updateField}
                  placeholder="e.g. Fever, hospital visit"
                  required
                  className="mt-2 w-full rounded-xl border border-[#e4ebe6] bg-[#fbfdfb] px-4 py-3 outline-none focus:border-[#78b9a1]"
                />
              </label>

              <label className="text-sm font-medium text-[#52665e]">
                Date *
                <input
                  type="date"
                  name="date"
                  value={form.date}
                  onChange={updateField}
                  required
                  className="mt-2 w-full rounded-xl border border-[#e4ebe6] bg-[#fbfdfb] px-4 py-3 outline-none focus:border-[#78b9a1]"
                />
              </label>

              <label className="text-sm font-medium text-[#52665e]">
                Category
                <select
                  name="category"
                  value={form.category}
                  onChange={updateField}
                  className="mt-2 w-full rounded-xl border border-[#e4ebe6] bg-[#fbfdfb] px-4 py-3 outline-none focus:border-[#78b9a1]"
                >
                  <option>Illness</option>
                  <option>Hospital Visit</option>
                  <option>Symptoms</option>
                  <option>Check-up</option>
                  <option>Treatment</option>
                  <option>Other</option>
                </select>
              </label>

              <label className="text-sm font-medium text-[#52665e]">
                Status
                <select
                  name="status"
                  value={form.status}
                  onChange={updateField}
                  className="mt-2 w-full rounded-xl border border-[#e4ebe6] bg-[#fbfdfb] px-4 py-3 outline-none focus:border-[#78b9a1]"
                >
                  <option>Ongoing</option>
                  <option>Recovered</option>
                  <option>Monitoring</option>
                </select>
              </label>
            </div>

            <label className="block text-sm font-medium text-[#52665e]">
              Symptoms or concerns
              <textarea
                name="symptoms"
                value={form.symptoms}
                onChange={updateField}
                rows={3}
                placeholder="Describe the symptoms or concerns..."
                className="mt-2 w-full rounded-xl border border-[#e4ebe6] bg-[#fbfdfb] px-4 py-3 outline-none focus:border-[#78b9a1]"
              />
            </label>

            <label className="block text-sm font-medium text-[#52665e]">
              Additional notes
              <textarea
                name="notes"
                value={form.notes}
                onChange={updateField}
                rows={3}
                placeholder="Treatment, doctor visit details or recovery notes..."
                className="mt-2 w-full rounded-xl border border-[#e4ebe6] bg-[#fbfdfb] px-4 py-3 outline-none focus:border-[#78b9a1]"
              />
            </label>

            <div className="flex flex-wrap gap-3">
              <button
                type="submit"
                className="rounded-xl bg-[#39866f] px-5 py-3 text-sm font-semibold text-white hover:bg-[#2e725e]"
              >
                Save episode
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="rounded-xl border border-[#e4ebe6] px-5 py-3 text-sm font-semibold text-[#60736a]"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="panel p-6">
        <h2 className="text-lg font-bold text-[#29433b]">Episode history</h2>
        <p className="mt-1 text-sm text-[#84928c]">
          Your recorded health events.
        </p>

        {episodes.length === 0 ? (
          <div className="py-14 text-center">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-[#eaf6f0] text-[#39866f]">
              <ClipboardList size={30} />
            </div>
            <h3 className="font-semibold text-[#39544a]">No care episodes yet</h3>
            <p className="mx-auto mt-2 max-w-sm text-sm text-[#84928c]">
              Add a health event to start building your care history.
            </p>
            <button
              onClick={() => setShowForm(true)}
              className="mt-5 rounded-xl bg-[#e7f5ef] px-4 py-3 text-sm font-semibold text-[#28745f] hover:bg-[#d9eee4]"
            >
              + Add your first episode
            </button>
          </div>
        ) : (
          <div className="mt-5 space-y-4">
            {episodes.map((episode) => (
              <div
                key={episode.id}
                className="rounded-2xl border border-[#edf1ee] p-5"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="flex items-start gap-3">
                    <div className="rounded-xl bg-[#eaf6f0] p-3 text-[#39866f]">
                      <Activity size={21} />
                    </div>
                    <div>
                      <h3 className="font-semibold text-[#29433b]">{episode.title}</h3>
                      <p className="mt-1 flex items-center gap-2 text-xs text-[#84928c]">
                        <CalendarDays size={14} />
                        {episode.date} · {episode.category}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className={`rounded-full px-3 py-1 text-xs font-semibold ${statusStyle(episode.status)}`}>
                      {episode.status}
                    </span>
                    <button
                      onClick={() => deleteEpisode(episode.id)}
                      title="Delete episode"
                      className="rounded-lg p-2 text-[#c17b72] hover:bg-[#fff0ed]"
                    >
                      <Trash2 size={17} />
                    </button>
                  </div>
                </div>

                {episode.symptoms && (
                  <p className="mt-4 text-sm leading-6 text-[#65766e]">
                    <strong>Symptoms:</strong> {episode.symptoms}
                  </p>
                )}
                {episode.notes && (
                  <p className="mt-2 text-sm leading-6 text-[#65766e]">
                    <strong>Notes:</strong> {episode.notes}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="rounded-2xl border border-[#f1e7d8] bg-[#fffaf2] p-4 text-sm leading-6 text-[#927d61]">
        These are personal health notes, not a medical assessment or diagnosis.
        Demo records are stored in this browser until backend storage is connected.
      </div>
    </div>
  )
}
