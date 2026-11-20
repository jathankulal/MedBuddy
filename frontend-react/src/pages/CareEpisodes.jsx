import { useEffect, useState } from 'react'
import {
  Plus, Activity, CalendarDays, Trash2, X, ClipboardList,
  AlertCircle, CheckCircle2, Loader2, ChevronDown, ChevronUp,
  MessageSquarePlus, Clock, Info
} from 'lucide-react'
import { api } from '../services/api'

const emptyForm = {
  title: '',
  start_date: new Date().toISOString().slice(0, 10),
  expected_end_date: '',
  category: 'Illness',
  symptoms: '',
  notes: '',
  status: 'Ongoing',
}

const emptyUpdateForm = {
  update_date: new Date().toISOString().slice(0, 10),
  feeling: '',
  changes: '',
  notes: '',
}

const mapBackendToUiStatus = (status) => {
  if (status === 'active') return 'Ongoing'
  if (status === 'recovering') return 'Recovering'
  if (status === 'resolved') return 'Resolved'
  return status || 'Ongoing'
}

const mapUiToBackendStatus = (status) => {
  if (status === 'Ongoing') return 'active'
  if (status === 'Resolved') return 'resolved'
  if (status === 'Recovering') return 'recovering'
  return 'active'
}

const statusStyle = (status) =>
  status === 'Resolved'
    ? 'bg-[#e7f5ef] text-[#28745f]'
    : status === 'Ongoing'
      ? 'bg-[#fff2e5] text-[#a36e36]'
      : 'bg-[#edf1f8] text-[#63799e]'

const fmtDate = (iso) => {
  if (!iso) return null
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      year: 'numeric', month: 'short', day: 'numeric',
    })
  } catch {
    return iso
  }
}

export default function CareEpisodes() {
  const [episodes, setEpisodes] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState(emptyForm)
  const [showForm, setShowForm] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  // episode detail / expanded state
  const [expandedId, setExpandedId] = useState(null)
  const [episodeUpdates, setEpisodeUpdates] = useState({}) // { [episodeId]: updates[] }
  const [updatesLoading, setUpdatesLoading] = useState({}) // { [episodeId]: bool }
  const [showUpdateForm, setShowUpdateForm] = useState(null) // episodeId or null
  const [updateForm, setUpdateForm] = useState(emptyUpdateForm)
  const [savingUpdate, setSavingUpdate] = useState(false)
  const [updateError, setUpdateError] = useState('')

  const loadEpisodes = async () => {
    setLoading(true)
    try {
      const data = await api.getEpisodes()
      setEpisodes((data || []).map(ep => ({
        ...ep,
        _uiStatus: mapBackendToUiStatus(ep.status),
      })))
    } catch (err) {
      setError(err.message || 'Failed to load care episodes.')
    } finally {
      setLoading(false)
    }
  }

  const loadUpdatesForEpisode = async (episodeId) => {
    setUpdatesLoading(prev => ({ ...prev, [episodeId]: true }))
    try {
      const data = await api.getEpisodeUpdates(episodeId)
      setEpisodeUpdates(prev => ({ ...prev, [episodeId]: data || [] }))
    } catch (err) {
      setError(err.message || 'Failed to load progress updates.')
    } finally {
      setUpdatesLoading(prev => ({ ...prev, [episodeId]: false }))
    }
  }

  useEffect(() => {
    let mounted = true
    async function load() {
      try {
        const data = await api.getEpisodes()
        if (mounted) {
          setEpisodes((data || []).map(ep => ({
            ...ep,
            _uiStatus: mapBackendToUiStatus(ep.status),
          })))
        }
      } catch (err) {
        if (mounted) setError(err.message || 'Failed to load care episodes.')
      } finally {
        if (mounted) setLoading(false)
      }
    }
    load()
    return () => { mounted = false }
  }, [])

  const updateField = (event) => {
    setForm({ ...form, [event.target.name]: event.target.value })
    setError('')
  }

  const updateUpdateField = (event) => {
    setUpdateForm({ ...updateForm, [event.target.name]: event.target.value })
    setUpdateError('')
  }

  const openAddForm = () => {
    setForm(emptyForm)
    setShowForm(true)
    setError('')
    setSuccess('')
  }

  const saveEpisode = async (event) => {
    event.preventDefault()
    setError('')
    setSuccess('')

    if (!form.title.trim() || !form.start_date) {
      setError('Please provide a title and start date.')
      return
    }

    if (form.expected_end_date && form.expected_end_date < form.start_date) {
      setError('Expected end date must be on or after the start date.')
      return
    }

    setSaving(true)
    try {
      const payload = {
        title: form.title.trim(),
        start_date: `${form.start_date}T00:00:00Z`,
        end_date: form.expected_end_date ? `${form.expected_end_date}T00:00:00Z` : null,
        status: mapUiToBackendStatus(form.status),
        category: form.category || 'Illness',
        symptoms: form.symptoms?.trim() || null,
        notes: form.notes?.trim() || null,
        description: form.symptoms?.trim() || form.title.trim(),
      }

      await api.createEpisode(payload)
      setSuccess('Care episode saved to persistent storage.')
      setForm(emptyForm)
      setShowForm(false)
      await loadEpisodes()
    } catch (err) {
      setError(err.message || 'Failed to save care episode.')
    } finally {
      setSaving(false)
    }
  }

  const deleteEpisode = async (id) => {
    if (window.confirm('Remove this care episode and all its progress updates?')) {
      try {
        await api.deleteEpisode(id)
        setEpisodes(current => current.filter(ep => ep.id !== id))
        setEpisodeUpdates(prev => { const n = { ...prev }; delete n[id]; return n })
        if (expandedId === id) setExpandedId(null)
        setSuccess('Care episode deleted.')
      } catch (err) {
        setError(err.message || 'Failed to delete care episode.')
      }
    }
  }

  const toggleExpand = async (episodeId) => {
    if (expandedId === episodeId) {
      setExpandedId(null)
      return
    }
    setExpandedId(episodeId)
    if (!episodeUpdates[episodeId]) {
      await loadUpdatesForEpisode(episodeId)
    }
  }

  const openUpdateForm = (episodeId) => {
    setShowUpdateForm(episodeId)
    setUpdateForm(emptyUpdateForm)
    setUpdateError('')
  }

  const saveUpdate = async (event, episodeId) => {
    event.preventDefault()
    setUpdateError('')

    if (!updateForm.feeling.trim()) {
      setUpdateError('Please describe how you are feeling.')
      return
    }

    setSavingUpdate(true)
    try {
      const payload = {
        update_date: `${updateForm.update_date}T00:00:00Z`,
        feeling: updateForm.feeling.trim(),
        changes: updateForm.changes?.trim() || null,
        notes: updateForm.notes?.trim() || null,
      }
      const created = await api.createEpisodeUpdate(episodeId, payload)
      setEpisodeUpdates(prev => ({
        ...prev,
        [episodeId]: [...(prev[episodeId] || []), created].sort(
          (a, b) => a.update_date.localeCompare(b.update_date)
        ),
      }))
      setShowUpdateForm(null)
      setUpdateForm(emptyUpdateForm)
      setSuccess('Progress update saved.')
    } catch (err) {
      setUpdateError(err.message || 'Failed to save progress update.')
    } finally {
      setSavingUpdate(false)
    }
  }

  const deleteUpdate = async (episodeId, updateId) => {
    if (window.confirm('Remove this progress update?')) {
      try {
        await api.deleteEpisodeUpdate(episodeId, updateId)
        setEpisodeUpdates(prev => ({
          ...prev,
          [episodeId]: (prev[episodeId] || []).filter(u => u.id !== updateId),
        }))
        setSuccess('Progress update removed.')
      } catch (err) {
        setError(err.message || 'Failed to delete progress update.')
      }
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm text-[#84928c]">Your health journey</p>
          <h1 className="mt-1 text-2xl font-bold text-[#29433b]">Care Episodes</h1>
          <p className="mt-1 text-sm text-[#84928c]">
            Record illnesses, hospital visits, symptoms and recovery progress. Add dated updates to track your journey.
          </p>
        </div>
        <button
          onClick={openAddForm}
          className="flex items-center gap-2 rounded-xl bg-[#39866f] px-4 py-3 text-sm font-semibold text-white hover:bg-[#2e725e]"
        >
          <Plus size={18} /> Add episode
        </button>
      </div>

      {/* Notifications */}
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

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="panel p-5">
          <p className="text-sm text-[#84928c]">Total episodes</p>
          <p className="mt-2 text-2xl font-bold text-[#29433b]">{episodes.length}</p>
        </div>
        <div className="panel p-5">
          <p className="text-sm text-[#84928c]">Ongoing</p>
          <p className="mt-2 text-2xl font-bold text-[#b17b43]">
            {episodes.filter(ep => ep._uiStatus === 'Ongoing').length}
          </p>
        </div>
        <div className="panel p-5">
          <p className="text-sm text-[#84928c]">Recovered / Resolved</p>
          <p className="mt-2 text-2xl font-bold text-[#39866f]">
            {episodes.filter(ep => ep._uiStatus === 'Resolved').length}
          </p>
        </div>
      </div>

      {/* New episode form */}
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
                  placeholder="e.g. Seasonal flu, Knee strain"
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
                  <option value="Illness">Illness</option>
                  <option value="Hospital Visit">Hospital Visit</option>
                  <option value="Symptoms">Symptoms</option>
                  <option value="Check-up">Check-up</option>
                  <option value="Treatment">Treatment</option>
                  <option value="Other">Other</option>
                </select>
              </label>

              <label className="text-sm font-medium text-[#52665e]">
                Start date *
                <input
                  type="date"
                  name="start_date"
                  value={form.start_date}
                  onChange={updateField}
                  required
                  className="mt-2 w-full rounded-xl border border-[#e4ebe6] bg-[#fbfdfb] px-4 py-3 outline-none focus:border-[#78b9a1]"
                />
              </label>

              <label className="text-sm font-medium text-[#52665e]">
                Expected end date <span className="text-[#84928c] font-normal">(optional)</span>
                <input
                  type="date"
                  name="expected_end_date"
                  value={form.expected_end_date}
                  onChange={updateField}
                  className="mt-2 w-full rounded-xl border border-[#e4ebe6] bg-[#fbfdfb] px-4 py-3 outline-none focus:border-[#78b9a1]"
                />
              </label>

              <label className="text-sm font-medium text-[#52665e]">
                Status
                <select
                  name="status"
                  value={form.status}
                  onChange={updateField}
                  className="mt-2 w-full rounded-xl border border-[#e4ebe6] bg-[#fbfdfb] px-4 py-3 outline-none focus:border-[#78b9a1]"
                >
                  <option value="Ongoing">Ongoing</option>
                  <option value="Recovering">Recovering</option>
                  <option value="Resolved">Resolved</option>
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
                disabled={saving}
                className="flex items-center gap-2 rounded-xl bg-[#39866f] px-5 py-3 text-sm font-semibold text-white hover:bg-[#2e725e] disabled:opacity-60"
              >
                {saving && <Loader2 className="animate-spin" size={16} />}
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

      {/* Episode list */}
      <div className="panel p-6">
        <h2 className="text-lg font-bold text-[#29433b]">Episode history</h2>
        <p className="mt-1 text-sm text-[#84928c]">
          Your recorded health events loaded from backend persistent storage.
        </p>

        {loading ? (
          <div className="flex min-h-[160px] items-center justify-center gap-2">
            <Loader2 className="animate-spin text-[#39866f]" size={24} />
            <span className="text-sm text-[#798e83]">Loading care episodes...</span>
          </div>
        ) : episodes.length === 0 ? (
          <div className="py-14 text-center">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-[#eaf6f0] text-[#39866f]">
              <ClipboardList size={30} />
            </div>
            <h3 className="font-semibold text-[#39544a]">No care episodes yet</h3>
            <p className="mx-auto mt-2 max-w-sm text-sm text-[#84928c]">
              Add a health event to start building your care history.
            </p>
            <button
              onClick={openAddForm}
              className="mt-5 rounded-xl bg-[#e7f5ef] px-4 py-3 text-sm font-semibold text-[#28745f] hover:bg-[#d9eee4]"
            >
              + Add your first episode
            </button>
          </div>
        ) : (
          <div className="mt-5 space-y-4">
            {episodes.map((episode) => {
              const isExpanded = expandedId === episode.id
              const updates = episodeUpdates[episode.id] || []
              const updLoading = updatesLoading[episode.id] || false
              const startLabel = fmtDate(episode.start_date)
              const endLabel = episode.end_date ? fmtDate(episode.end_date) : null
              const createdLabel = fmtDate(episode.created_at)
              const updatedLabel = fmtDate(episode.updated_at)

              return (
                <div key={episode.id} className="rounded-2xl border border-[#edf1ee]">
                  {/* Episode summary row */}
                  <div className="flex flex-wrap items-start justify-between gap-3 p-5">
                    <div className="flex items-start gap-3">
                      <div className="rounded-xl bg-[#eaf6f0] p-3 text-[#39866f]">
                        <Activity size={21} />
                      </div>
                      <div>
                        <h3 className="font-semibold text-[#29433b]">{episode.title}</h3>
                        <p className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-[#84928c]">
                          <span className="flex items-center gap-1">
                            <CalendarDays size={13} />
                            Started: {startLabel}
                          </span>
                          {endLabel ? (
                            <span className="flex items-center gap-1">
                              <Clock size={13} />
                              Expected end: {endLabel}
                            </span>
                          ) : (
                            <span className="text-[#aab5b0]">Expected end: Not estimated</span>
                          )}
                          <span>{episode.category || 'Illness'}</span>
                        </p>
                        {updates.length > 0 && (
                          <p className="mt-1 text-xs text-[#84928c]">
                            {updates.length} progress update{updates.length !== 1 ? 's' : ''}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className={`rounded-full px-3 py-1 text-xs font-semibold ${statusStyle(episode._uiStatus)}`}>
                        {episode._uiStatus}
                      </span>
                      <button
                        onClick={() => toggleExpand(episode.id)}
                        title={isExpanded ? 'Collapse' : 'View details'}
                        className="rounded-lg p-2 text-[#66877a] hover:bg-[#edf7f1]"
                      >
                        {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                      </button>
                      <button
                        onClick={() => deleteEpisode(episode.id)}
                        title="Delete episode"
                        className="rounded-lg p-2 text-[#c17b72] hover:bg-[#fff0ed]"
                      >
                        <Trash2 size={17} />
                      </button>
                    </div>
                  </div>

                  {/* Expanded detail panel */}
                  {isExpanded && (
                    <div className="border-t border-[#edf1ee] px-5 pb-6 pt-4 space-y-5">

                      {/* Core info */}
                      <div className="grid gap-3 sm:grid-cols-2 text-sm">
                        {episode.symptoms && (
                          <div>
                            <p className="font-semibold text-[#52665e]">Symptoms / Concerns</p>
                            <p className="mt-1 leading-6 text-[#65766e]">{episode.symptoms}</p>
                          </div>
                        )}
                        {episode.notes && (
                          <div>
                            <p className="font-semibold text-[#52665e]">Notes</p>
                            <p className="mt-1 leading-6 text-[#65766e]">{episode.notes}</p>
                          </div>
                        )}
                      </div>

                      {/* Date metadata */}
                      <div className="flex flex-wrap gap-4 text-xs text-[#84928c]">
                        <span>Recorded: {createdLabel}</span>
                        {updatedLabel !== createdLabel && <span>Last updated: {updatedLabel}</span>}
                      </div>

                      {/* Progress timeline */}
                      <div>
                        <div className="flex items-center justify-between mb-3">
                          <h4 className="text-sm font-semibold text-[#29433b]">Recovery progress updates</h4>
                          <button
                            onClick={() =>
                              showUpdateForm === episode.id
                                ? setShowUpdateForm(null)
                                : openUpdateForm(episode.id)
                            }
                            className="flex items-center gap-1.5 rounded-lg bg-[#e7f5ef] px-3 py-2 text-xs font-semibold text-[#28745f] hover:bg-[#d9eee4]"
                          >
                            <MessageSquarePlus size={14} />
                            Add update
                          </button>
                        </div>

                        {/* Add update form */}
                        {showUpdateForm === episode.id && (
                          <form
                            onSubmit={(e) => saveUpdate(e, episode.id)}
                            className="mb-4 rounded-xl border border-[#e4ebe6] bg-[#f8fbf9] p-4 space-y-3"
                          >
                            <h5 className="text-xs font-semibold text-[#52665e] uppercase tracking-wide">New Progress Update</h5>

                            {updateError && (
                              <div className="flex items-start gap-2 rounded-lg bg-[#fdf5f4] p-3 text-xs text-[#9e4438]">
                                <AlertCircle size={14} className="mt-0.5 shrink-0" />
                                {updateError}
                              </div>
                            )}

                            <div className="grid gap-3 sm:grid-cols-2">
                              <label className="text-xs font-medium text-[#52665e]">
                                Date *
                                <input
                                  type="date"
                                  name="update_date"
                                  value={updateForm.update_date}
                                  onChange={updateUpdateField}
                                  required
                                  className="mt-1.5 w-full rounded-lg border border-[#e4ebe6] bg-white px-3 py-2 text-sm outline-none focus:border-[#78b9a1]"
                                />
                              </label>
                              <label className="text-xs font-medium text-[#52665e]">
                                How are you feeling? *
                                <input
                                  name="feeling"
                                  value={updateForm.feeling}
                                  onChange={updateUpdateField}
                                  placeholder="e.g. Much better, still tired"
                                  required
                                  className="mt-1.5 w-full rounded-lg border border-[#e4ebe6] bg-white px-3 py-2 text-sm outline-none focus:border-[#78b9a1]"
                                />
                              </label>
                            </div>

                            <label className="block text-xs font-medium text-[#52665e]">
                              Symptoms or changes noticed
                              <textarea
                                name="changes"
                                value={updateForm.changes}
                                onChange={updateUpdateField}
                                rows={2}
                                placeholder="Any new or resolved symptoms..."
                                className="mt-1.5 w-full rounded-lg border border-[#e4ebe6] bg-white px-3 py-2 text-sm outline-none focus:border-[#78b9a1]"
                              />
                            </label>

                            <label className="block text-xs font-medium text-[#52665e]">
                              Notes <span className="text-[#84928c] font-normal">(optional)</span>
                              <textarea
                                name="notes"
                                value={updateForm.notes}
                                onChange={updateUpdateField}
                                rows={2}
                                placeholder="Doctor visit, medication changes, etc."
                                className="mt-1.5 w-full rounded-lg border border-[#e4ebe6] bg-white px-3 py-2 text-sm outline-none focus:border-[#78b9a1]"
                              />
                            </label>

                            <div className="flex gap-2">
                              <button
                                type="submit"
                                disabled={savingUpdate}
                                className="flex items-center gap-1.5 rounded-lg bg-[#39866f] px-4 py-2 text-xs font-semibold text-white hover:bg-[#2e725e] disabled:opacity-60"
                              >
                                {savingUpdate && <Loader2 className="animate-spin" size={13} />}
                                Save update
                              </button>
                              <button
                                type="button"
                                onClick={() => setShowUpdateForm(null)}
                                className="rounded-lg border border-[#e4ebe6] px-4 py-2 text-xs font-semibold text-[#60736a]"
                              >
                                Cancel
                              </button>
                            </div>
                          </form>
                        )}

                        {/* Timeline */}
                        {updLoading ? (
                          <div className="flex items-center gap-2 py-4 text-sm text-[#84928c]">
                            <Loader2 className="animate-spin" size={16} />
                            Loading updates...
                          </div>
                        ) : updates.length === 0 ? (
                          <div className="rounded-xl border border-dashed border-[#d5e3da] py-8 text-center text-sm text-[#84928c]">
                            <Info size={20} className="mx-auto mb-2 text-[#b0c8bb]" />
                            No progress updates yet. Add your first update to start tracking recovery.
                          </div>
                        ) : (
                          <ol className="relative ml-3 border-l border-[#d5e3da] space-y-5">
                            {updates.map((upd) => (
                              <li key={upd.id} className="ml-5">
                                <span className="absolute -left-[9px] flex h-4 w-4 items-center justify-center rounded-full bg-[#39866f] ring-4 ring-white" />
                                <div className="rounded-xl border border-[#edf1ee] bg-white p-4">
                                  <div className="flex items-start justify-between gap-2">
                                    <div>
                                      <p className="text-xs font-semibold text-[#84928c]">
                                        {fmtDate(upd.update_date)}
                                      </p>
                                      <p className="mt-1 text-sm font-semibold text-[#29433b]">{upd.feeling}</p>
                                    </div>
                                    <button
                                      onClick={() => deleteUpdate(episode.id, upd.id)}
                                      title="Remove update"
                                      className="rounded p-1 text-[#c17b72] hover:bg-[#fff0ed]"
                                    >
                                      <Trash2 size={14} />
                                    </button>
                                  </div>
                                  {upd.changes && (
                                    <p className="mt-2 text-xs leading-5 text-[#65766e]">
                                      <strong>Changes: </strong>{upd.changes}
                                    </p>
                                  )}
                                  {upd.notes && (
                                    <p className="mt-1 text-xs leading-5 text-[#65766e]">
                                      <strong>Notes: </strong>{upd.notes}
                                    </p>
                                  )}
                                </div>
                              </li>
                            ))}
                          </ol>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Disclaimer */}
      <div className="flex items-start gap-3 rounded-2xl border border-[#f1e7d8] bg-[#fffaf2] p-4">
        <Info className="mt-0.5 shrink-0 text-[#c18b4c]" size={18} />
        <p className="text-sm leading-6 text-[#927d61]">
          These records are personal health history notes stored in backend JSON storage.
          They can be referenced by the Health Copilot to provide context-aware responses.
          Progress updates reflect your self-reported observations — they are not medical assessments.
          Always follow your healthcare provider&apos;s direction.
        </p>
      </div>
    </div>
  )
}
