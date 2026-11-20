
import { useState } from 'react'
import {
  UserRound, HeartPulse, ShieldAlert, Phone,
  Languages, Save, CheckCircle2, ArrowLeft
} from 'lucide-react'

const initialProfile = {
  full_name: '',
  date_of_birth: '',
  gender: '',
  conditions: '',
  allergies: '',
  emergency_name: '',
  emergency_phone: '',
  preferred_language: 'English',
  accessibility_notes: '',
}

export default function HealthProfile() {
  const [profile, setProfile] = useState(initialProfile)
  const [saved, setSaved] = useState(false)

  const update = (field, value) => {
    setProfile(previous => ({ ...previous, [field]: value }))
    setSaved(false)
  }

  const handleSubmit = (event) => {
    event.preventDefault()

    // Temporary browser storage for UI testing only.
    // Replace with authenticated backend API later.
    localStorage.setItem('medbuddy_demo_profile', JSON.stringify(profile))
    setSaved(true)
  }

  const inputClass =
    'w-full rounded-xl border border-[#e6ede7] bg-white px-4 py-3 text-sm text-[#40564a] outline-none transition placeholder:text-[#b0bbb2] focus:border-[#8fbaa0]'

  const labelClass =
    'mb-2 block text-xs font-semibold text-[#586e5e]'

  const sectionClass =
    'panel p-5 sm:p-6'

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="mb-1 text-xs font-medium text-[#8ba092]">
            YOUR PERSONAL INFORMATION
          </p>
          <h2 className="text-2xl font-bold text-[#344c41]">
            Health Profile
          </h2>
          <p className="mt-2 text-sm text-[#93a198]">
            Keep your health information organised in one place.
          </p>
        </div>
        <span className="rounded-full bg-[#eaf5ed] px-3 py-2 text-xs font-semibold text-[#578469]">
          <ShieldAlert className="mr-1 inline" size={14} />
          Private health information
        </span>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <section className={sectionClass}>
          <div className="mb-5 flex items-center gap-3">
            <div className="rounded-xl bg-[#e8f4ec] p-3 text-[#609577]">
              <UserRound size={21} />
            </div>
            <div>
              <h3 className="font-bold text-[#40564a]">Personal details</h3>
              <p className="text-xs text-[#9aa79e]">Basic information about you</p>
            </div>
          </div>

          <div className="grid gap-5 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <label className={labelClass}>Full name</label>
              <input
                className={inputClass}
                placeholder="Enter your full name"
                value={profile.full_name}
                onChange={e => update('full_name', e.target.value)}
              />
            </div>

            <div>
              <label className={labelClass}>Date of birth</label>
              <input
                type="date"
                className={inputClass}
                value={profile.date_of_birth}
                onChange={e => update('date_of_birth', e.target.value)}
              />
            </div>

            <div>
              <label className={labelClass}>Gender (optional)</label>
              <select
                className={inputClass}
                value={profile.gender}
                onChange={e => update('gender', e.target.value)}
              >
                <option value="">Prefer not to say</option>
                <option value="Female">Female</option>
                <option value="Male">Male</option>
                <option value="Other">Other</option>
              </select>
            </div>
          </div>
        </section>

        <section className={sectionClass}>
          <div className="mb-5 flex items-center gap-3">
            <div className="rounded-xl bg-[#fff1e7] p-3 text-[#c38b66]">
              <HeartPulse size={21} />
            </div>
            <div>
              <h3 className="font-bold text-[#40564a]">Medical information</h3>
              <p className="text-xs text-[#9aa79e]">Information you want to keep on record</p>
            </div>
          </div>

          <div className="space-y-5">
            <div>
              <label className={labelClass}>Existing medical conditions</label>
              <textarea
                rows={3}
                className={inputClass}
                placeholder="List any known conditions, or leave blank if none"
                value={profile.conditions}
                onChange={e => update('conditions', e.target.value)}
              />
            </div>

            <div>
              <label className={labelClass}>Allergies and sensitivities</label>
              <textarea
                rows={3}
                className={inputClass}
                placeholder="List known allergies, reactions or sensitivities"
                value={profile.allergies}
                onChange={e => update('allergies', e.target.value)}
              />
              <p className="mt-2 text-[11px] text-[#9aa79e]">
                If you have no known allergies, explicitly record that information.
              </p>
            </div>
          </div>
        </section>

        <section className={sectionClass}>
          <div className="mb-5 flex items-center gap-3">
            <div className="rounded-xl bg-[#eef3fc] p-3 text-[#7894c0]">
              <Phone size={21} />
            </div>
            <div>
              <h3 className="font-bold text-[#40564a]">Emergency contact</h3>
              <p className="text-xs text-[#9aa79e]">Someone to contact when needed</p>
            </div>
          </div>

          <div className="grid gap-5 sm:grid-cols-2">
            <div>
              <label className={labelClass}>Contact name</label>
              <input
                className={inputClass}
                placeholder="Enter contact name"
                value={profile.emergency_name}
                onChange={e => update('emergency_name', e.target.value)}
              />
            </div>

            <div>
              <label className={labelClass}>Contact phone</label>
              <input
                type="tel"
                className={inputClass}
                placeholder="Enter phone number"
                value={profile.emergency_phone}
                onChange={e => update('emergency_phone', e.target.value)}
              />
            </div>
          </div>
        </section>

        <section className={sectionClass}>
          <div className="mb-5 flex items-center gap-3">
            <div className="rounded-xl bg-[#f1eafa] p-3 text-[#947eb7]">
              <Languages size={21} />
            </div>
            <div>
              <h3 className="font-bold text-[#40564a]">Preferences</h3>
              <p className="text-xs text-[#9aa79e]">Make MedBuddy comfortable to use</p>
            </div>
          </div>

          <div className="space-y-5">
            <div>
              <label className={labelClass}>Preferred language</label>
              <select
                className={inputClass}
                value={profile.preferred_language}
                onChange={e => update('preferred_language', e.target.value)}
              >
                <option>English</option>
                <option>Kannada</option>
                <option>Hindi</option>
                <option>Tulu</option>
              </select>
            </div>

            <div>
              <label className={labelClass}>Accessibility notes (optional)</label>
              <textarea
                rows={2}
                className={inputClass}
                placeholder="Any accessibility preferences you'd like to record?"
                value={profile.accessibility_notes}
                onChange={e => update('accessibility_notes', e.target.value)}
              />
            </div>
          </div>
        </section>

        {saved && (
          <div role="status" className="flex items-center gap-2 rounded-xl bg-[#eaf5ed] p-4 text-sm font-medium text-[#4d8564]">
            <CheckCircle2 size={18} />
            Demo profile saved in this browser.
          </div>
        )}

        <div className="flex justify-end">
          <button
            type="submit"
            className="inline-flex items-center gap-2 rounded-xl bg-[#559574] px-6 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-[#427f61]"
          >
            <Save size={17} />
            Save profile
          </button>
        </div>
      </form>
    </div>
  )
}
