import { useEffect, useState } from 'react'
import {
  Plus, Pill, Trash2, Pencil, X, AlertCircle, CheckCircle2,
  AlertTriangle, ShieldCheck, Loader2
} from 'lucide-react'
import { api } from '../services/api'

const emptyForm = {
  name: '',
  strength: '',
  dosage: '',
  route: 'Oral',
  active_ingredients: '',
  frequency: '',
}

export default function Medications() {
  const [medications, setMedications] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState(emptyForm)
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [message, setMessage] = useState('')
  const [conflictError, setConflictError] = useState(null)
  const [successNotice, setSuccessNotice] = useState('')

  const loadMedications = async () => {
    setLoading(true)
    try {
      const data = await api.getMedications()
      setMedications(data || [])
    } catch (err) {
      setMessage(err.message || 'Failed to load medications from server.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let mounted = true
    async function load() {
      try {
        const data = await api.getMedications()
        if (mounted) setMedications(data || [])
      } catch (err) {
        if (mounted) setMessage(err.message || 'Failed to load medications from server.')
      } finally {
        if (mounted) setLoading(false)
      }
    }
    load()
    return () => { mounted = false }
  }, [])

  const updateField = (event) => {
    setForm({ ...form, [event.target.name]: event.target.value })
    setMessage('')
    setConflictError(null)
  }

  const openAddForm = () => {
    setForm(emptyForm)
    setEditingId(null)
    setShowForm(true)
    setMessage('')
    setConflictError(null)
    setSuccessNotice('')
  }

  const openEditForm = (medication) => {
    setForm({
      name: medication.name || '',
      strength: medication.strength || '',
      dosage: medication.dosage || '',
      route: medication.route || 'Oral',
      active_ingredients: Array.isArray(medication.active_ingredients)
        ? medication.active_ingredients.join(', ')
        : (medication.active_ingredients || ''),
      frequency: medication.frequency || '',
    })
    setEditingId(medication.id)
    setShowForm(true)
    setMessage('')
    setConflictError(null)
    setSuccessNotice('')
  }

  const parseIngredients = (text) => {
    if (!text || !text.trim()) return []
    return text
      .split(/[\n,]+/)
      .map((item) => item.trim())
      .filter(Boolean)
  }

  const saveMedication = async (event) => {
    event.preventDefault()
    setMessage('')
    setConflictError(null)
    setSuccessNotice('')

    if (!form.name.trim() || !form.dosage.trim() || !form.strength.trim()) {
      setMessage('Please fill in the medication name, dosage and strength.')
      return
    }

    setSaving(true)

    const payload = {
      name: form.name.trim(),
      strength: form.strength.trim(),
      dosage: form.dosage.trim(),
      route: form.route || 'Oral',
      active_ingredients: parseIngredients(form.active_ingredients),
      frequency: form.frequency?.trim() || null,
      status: 'active',
    }

    try {
      if (editingId) {
        await api.updateMedication(editingId, payload)
        setSuccessNotice('Medication updated successfully!')
      } else {
        const created = await api.createMedication(payload)
        if (created.medication_warnings?.length) {
          setSuccessNotice('Medication saved with safety warnings recorded.')
        } else {
          setSuccessNotice('Medication added and verified through Safety Engine!')
        }
      }

      await loadMedications()
      setShowForm(false)
      setForm(emptyForm)
      setEditingId(null)
    } catch (err) {
      if (err.code === 'ERR_CONFLICT' || err.status === 409) {
        setConflictError({
          message: err.message || 'Exact duplicate medication detected.',
          details: err.details,
        })
      } else {
        setMessage(err.message || 'An error occurred while saving the medication.')
      }
    } finally {
      setSaving(false)
    }
  }

  const deleteMedication = async (id) => {
    if (window.confirm('Are you sure you want to remove this medication?')) {
      try {
        await api.deleteMedication(id)
        setMedications((current) => current.filter((item) => item.id !== id))
        setSuccessNotice('Medication removed.')
      } catch (err) {
        setMessage(err.message || 'Failed to remove medication.')
      }
    }
  }

  const hasWarnings = medications.some(m => m.medication_warnings?.length > 0)

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm text-[#84928c]">Your medication records</p>
          <h1 className="mt-1 text-2xl font-bold text-[#29433b]">Medications</h1>
          <p className="mt-1 text-sm text-[#84928c]">
            Track your medications with automatic safety-engine duplicate & allergy verification.
          </p>
        </div>

        <button
          onClick={openAddForm}
          className="flex items-center gap-2 rounded-xl bg-[#39866f] px-4 py-3 text-sm font-semibold text-white transition hover:bg-[#2e725e]"
        >
          <Plus size={18} /> Add medication
        </button>
      </div>

      {successNotice && (
        <div className="flex items-center gap-2 rounded-xl bg-[#eaf5ed] p-4 text-sm font-medium text-[#4d8564]">
          <CheckCircle2 size={18} />
          {successNotice}
        </div>
      )}

      {message && (
        <div className="flex items-start gap-2 rounded-xl bg-[#fdf5f4] p-4 text-sm text-[#9e4438]">
          <AlertCircle size={18} className="mt-0.5 shrink-0" />
          <p>{message}</p>
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="panel flex items-center gap-4 p-5">
          <div className="rounded-2xl bg-[#e5f5ed] p-3 text-[#39866f]">
            <Pill size={23} />
          </div>
          <div>
            <p className="text-sm text-[#84928c]">Total medications</p>
            <p className="text-2xl font-bold text-[#29433b]">{medications.length}</p>
          </div>
        </div>

        <div className="panel flex items-center gap-4 p-5">
          <div className={`rounded-2xl p-3 ${hasWarnings ? 'bg-[#fff0e6] text-[#d58b55]' : 'bg-[#e5f5ed] text-[#39866f]'}`}>
            {hasWarnings ? <AlertTriangle size={23} /> : <ShieldCheck size={23} />}
          </div>
          <div>
            <p className="text-sm text-[#84928c]">Safety Engine Status</p>
            <p className={`text-sm font-semibold ${hasWarnings ? 'text-[#a66a3b]' : 'text-[#2e725e]'}`}>
              {hasWarnings ? 'Warnings Recorded on Records' : 'Active & Verified'}
            </p>
          </div>
        </div>
      </div>

      {showForm && (
        <div className="panel p-6">
          <div className="mb-5 flex items-center justify-between">
            <h2 className="text-lg font-bold text-[#29433b]">
              {editingId ? 'Edit medication' : 'Add a medication'}
            </h2>
            <button
              onClick={() => setShowForm(false)}
              className="rounded-lg p-2 text-[#84928c] hover:bg-[#f3f8f5]"
            >
              <X size={20} />
            </button>
          </div>

          {conflictError && (
            <div className="mb-5 rounded-2xl border border-[#f3d0ca] bg-[#fff6f5] p-4 text-sm text-[#a03b30]">
              <div className="flex items-center gap-2 font-bold">
                <AlertCircle size={18} />
                <span>Duplicate Conflict Detected (409)</span>
              </div>
              <p className="mt-1 text-xs leading-5">
                {conflictError.message}
              </p>
              {conflictError.details?.matched_item && (
                <p className="mt-1 text-xs">
                  Matched item: <span className="font-semibold">{conflictError.details.matched_item}</span>
                </p>
              )}
            </div>
          )}

          <form onSubmit={saveMedication} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="text-sm font-medium text-[#52665e]">
                Medication name *
                <input
                  name="name"
                  value={form.name}
                  onChange={updateField}
                  placeholder="e.g. Lisinopril"
                  className="mt-2 w-full rounded-xl border border-[#e4ebe6] bg-[#fbfdfb] px-4 py-3 outline-none focus:border-[#78b9a1]"
                  required
                />
              </label>

              <label className="text-sm font-medium text-[#52665e]">
                Strength *
                <input
                  name="strength"
                  value={form.strength}
                  onChange={updateField}
                  placeholder="e.g. 10 mg"
                  className="mt-2 w-full rounded-xl border border-[#e4ebe6] bg-[#fbfdfb] px-4 py-3 outline-none focus:border-[#78b9a1]"
                  required
                />
              </label>

              <label className="text-sm font-medium text-[#52665e]">
                Dosage *
                <input
                  name="dosage"
                  value={form.dosage}
                  onChange={updateField}
                  placeholder="e.g. 1 tablet"
                  className="mt-2 w-full rounded-xl border border-[#e4ebe6] bg-[#fbfdfb] px-4 py-3 outline-none focus:border-[#78b9a1]"
                  required
                />
              </label>

              <label className="text-sm font-medium text-[#52665e]">
                Route
                <select
                  name="route"
                  value={form.route}
                  onChange={updateField}
                  className="mt-2 w-full rounded-xl border border-[#e4ebe6] bg-[#fbfdfb] px-4 py-3 outline-none focus:border-[#78b9a1]"
                >
                  <option value="Oral">Oral</option>
                  <option value="Topical">Topical</option>
                  <option value="Injection">Injection</option>
                  <option value="Inhalation">Inhalation</option>
                  <option value="Other">Other</option>
                </select>
              </label>

              <label className="text-sm font-medium text-[#52665e]">
                Active ingredients (comma-separated)
                <input
                  name="active_ingredients"
                  value={form.active_ingredients}
                  onChange={updateField}
                  placeholder="e.g. Lisinopril, Hydrochlorothiazide"
                  className="mt-2 w-full rounded-xl border border-[#e4ebe6] bg-[#fbfdfb] px-4 py-3 outline-none focus:border-[#78b9a1]"
                />
              </label>

              <label className="text-sm font-medium text-[#52665e]">
                Frequency
                <input
                  name="frequency"
                  value={form.frequency}
                  onChange={updateField}
                  placeholder="e.g. Once daily in morning"
                  className="mt-2 w-full rounded-xl border border-[#e4ebe6] bg-[#fbfdfb] px-4 py-3 outline-none focus:border-[#78b9a1]"
                />
              </label>
            </div>

            <div className="flex flex-wrap gap-3 pt-2">
              <button
                type="submit"
                disabled={saving}
                className="flex items-center gap-2 rounded-xl bg-[#39866f] px-5 py-3 text-sm font-semibold text-white hover:bg-[#2e725e] disabled:opacity-60"
              >
                {saving && <Loader2 className="animate-spin" size={16} />}
                {editingId ? 'Save changes' : 'Save medication'}
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="rounded-xl border border-[#e4ebe6] px-5 py-3 text-sm font-semibold text-[#60736a] hover:bg-[#f7faf8]"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="panel p-6">
        <h2 className="text-lg font-bold text-[#29433b]">Your medication list</h2>
        <p className="mt-1 text-sm text-[#84928c]">
          Medication records retrieved from the backend persistent storage.
        </p>

        {loading ? (
          <div className="flex min-h-[160px] items-center justify-center gap-2">
            <Loader2 className="animate-spin text-[#39866f]" size={24} />
            <span className="text-sm text-[#798e83]">Loading medications...</span>
          </div>
        ) : medications.length === 0 ? (
          <div className="py-14 text-center">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-[#eaf6f0] text-[#39866f]">
              <Pill size={30} />
            </div>
            <h3 className="font-semibold text-[#39544a]">No medications added yet</h3>
            <p className="mx-auto mt-2 max-w-sm text-sm text-[#84928c]">
              Add your medication details to start building your health record.
            </p>
            <button
              onClick={openAddForm}
              className="mt-5 rounded-xl bg-[#e7f5ef] px-4 py-3 text-sm font-semibold text-[#28745f] hover:bg-[#d9eee4]"
            >
              + Add your first medication
            </button>
          </div>
        ) : (
          <div className="mt-5 space-y-3">
            {medications.map((medication) => (
              <div
                key={medication.id}
                className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-[#edf1ee] p-4 transition hover:border-[#d9e6df]"
              >
                <div className="flex min-w-0 items-start gap-3">
                  <div className="mt-0.5 rounded-xl bg-[#eaf6f0] p-3 text-[#39866f]">
                    <Pill size={21} />
                  </div>
                  <div className="min-w-0">
                    <h3 className="truncate font-semibold text-[#29433b]">
                      {medication.name}
                    </h3>
                    <p className="mt-1 text-sm text-[#84928c]">
                      {medication.strength} · {medication.dosage} · {medication.route}
                    </p>
                    {medication.frequency && (
                      <p className="mt-1 text-xs text-[#84928c]">
                        Frequency: {medication.frequency}
                      </p>
                    )}
                    {medication.active_ingredients?.length > 0 && (
                      <p className="mt-1 text-xs text-[#84928c]">
                        Ingredients: {Array.isArray(medication.active_ingredients) ? medication.active_ingredients.join(', ') : medication.active_ingredients}
                      </p>
                    )}

                    {/* Safety Warnings attached to medication */}
                    {medication.medication_warnings?.length > 0 && (
                      <div className="mt-2 space-y-1">
                        {medication.medication_warnings.map((w, idx) => (
                          <div
                            key={idx}
                            className="inline-flex items-center gap-1.5 rounded-lg bg-[#fff5ec] px-2.5 py-1 text-xs font-medium text-[#ad652e]"
                          >
                            <AlertTriangle size={13} />
                            <span>{w.message || w.code}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => openEditForm(medication)}
                    title="Edit medication"
                    className="rounded-lg p-2 text-[#66877a] hover:bg-[#edf7f1]"
                  >
                    <Pencil size={18} />
                  </button>
                  <button
                    onClick={() => deleteMedication(medication.id)}
                    title="Delete medication"
                    className="rounded-lg p-2 text-[#c17b72] hover:bg-[#fff0ed]"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="flex items-start gap-3 rounded-2xl border border-[#f1e7d8] bg-[#fffaf2] p-4">
        <ShieldCheck className="mt-0.5 shrink-0 text-[#c18b4c]" size={20} />
        <div>
          <p className="text-sm font-semibold text-[#80643f]">Safety Engine Protection</p>
          <p className="mt-1 text-sm leading-6 text-[#927d61]">
            Candidate entries are validated by MedBuddy's Safety Engine before saving. Exact duplicates (matching name, dosage, route, strength) are blocked, and ingredient overlaps or allergy alerts are recorded. Absence of a warning does not guarantee clinical safety; always follow your healthcare provider's direction.
          </p>
        </div>
      </div>
    </div>
  )
}
