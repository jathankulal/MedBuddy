
import { useEffect, useState } from 'react'
import { Plus, Pill, Trash2, Pencil, X, AlertCircle, CheckCircle2 } from 'lucide-react'

const STORAGE_KEY = 'medbuddy_demo_medications'

const emptyForm = {
  name: '',
  strength: '',
  dosage: '',
  route: 'Oral',
  active_ingredients: '',
  frequency: '',
}

export default function Medications() {
  const [medications, setMedications] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY)) || []
    } catch {
      return []
    }
  })

  const [form, setForm] = useState(emptyForm)
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [message, setMessage] = useState('')

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(medications))
  }, [medications])

  const updateField = (event) => {
    setForm({ ...form, [event.target.name]: event.target.value })
  }

  const openAddForm = () => {
    setForm(emptyForm)
    setEditingId(null)
    setShowForm(true)
    setMessage('')
  }

  const openEditForm = (medication) => {
    setForm({ ...medication })
    setEditingId(medication.id)
    setShowForm(true)
    setMessage('')
  }

  const saveMedication = (event) => {
    event.preventDefault()

    if (!form.name.trim() || !form.dosage.trim() || !form.strength.trim()) {
      setMessage('Please fill in the medication name, dosage and strength.')
      return
    }

    if (editingId) {
      setMedications((current) =>
        current.map((item) =>
          item.id === editingId ? { ...form, id: editingId } : item
        )
      )
    } else {
      setMedications((current) => [
        ...current,
        { ...form, id: crypto.randomUUID() },
      ])
    }

    setShowForm(false)
    setForm(emptyForm)
    setEditingId(null)
    setMessage('')
  }

  const deleteMedication = (id) => {
    if (window.confirm('Are you sure you want to remove this medication?')) {
      setMedications((current) => current.filter((item) => item.id !== id))
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm text-[#84928c]">Your medication records</p>
          <h1 className="mt-1 text-2xl font-bold text-[#29433b]">Medications</h1>
          <p className="mt-1 text-sm text-[#84928c]">
            Keep your medication information organized in one place.
          </p>
        </div>

        <button
          onClick={openAddForm}
          className="flex items-center gap-2 rounded-xl bg-[#39866f] px-4 py-3 text-sm font-semibold text-white transition hover:bg-[#2e725e]"
        >
          <Plus size={18} /> Add medication
        </button>
      </div>

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
          <div className="rounded-2xl bg-[#fff0e6] p-3 text-[#d58b55]">
            <AlertCircle size={23} />
          </div>
          <div>
            <p className="text-sm text-[#84928c]">Safety status</p>
            <p className="text-sm font-semibold text-[#9a795c]">Not assessed yet</p>
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

          <form onSubmit={saveMedication} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="text-sm font-medium text-[#52665e]">
                Medication name *
                <input
                  name="name"
                  value={form.name}
                  onChange={updateField}
                  placeholder="e.g. Medication name"
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
                  placeholder="e.g. 500 mg"
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
                  <option>Oral</option>
                  <option>Topical</option>
                  <option>Injection</option>
                  <option>Inhalation</option>
                  <option>Other</option>
                </select>
              </label>

              <label className="text-sm font-medium text-[#52665e]">
                Active ingredients
                <input
                  name="active_ingredients"
                  value={form.active_ingredients}
                  onChange={updateField}
                  placeholder="e.g. Ingredient names"
                  className="mt-2 w-full rounded-xl border border-[#e4ebe6] bg-[#fbfdfb] px-4 py-3 outline-none focus:border-[#78b9a1]"
                />
              </label>

              <label className="text-sm font-medium text-[#52665e]">
                Frequency
                <input
                  name="frequency"
                  value={form.frequency}
                  onChange={updateField}
                  placeholder="e.g. As prescribed"
                  className="mt-2 w-full rounded-xl border border-[#e4ebe6] bg-[#fbfdfb] px-4 py-3 outline-none focus:border-[#78b9a1]"
                />
              </label>
            </div>

            {message && (
              <p className="text-sm text-red-600">{message}</p>
            )}

            <div className="flex flex-wrap gap-3 pt-2">
              <button
                type="submit"
                className="rounded-xl bg-[#39866f] px-5 py-3 text-sm font-semibold text-white hover:bg-[#2e725e]"
              >
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
          Medication details you've added.
        </p>

        {medications.length === 0 ? (
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
                className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-[#edf1ee] p-4"
              >
                <div className="flex min-w-0 items-center gap-3">
                  <div className="rounded-xl bg-[#eaf6f0] p-3 text-[#39866f]">
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
                    {medication.active_ingredients && (
                      <p className="mt-1 text-xs text-[#84928c]">
                        Ingredients: {medication.active_ingredients}
                      </p>
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
        <AlertCircle className="mt-0.5 shrink-0 text-[#c18b4c]" size={20} />
        <div>
          <p className="text-sm font-semibold text-[#80643f]">Safety information</p>
          <p className="mt-1 text-sm leading-6 text-[#927d61]">
            Saving a medication here does not check whether it is safe for you.
            MedBuddy's safety engine will be connected separately. Always follow
            your healthcare professional's instructions.
          </p>
        </div>
      </div>
    </div>
  )
}
