import { useEffect, useState } from 'react'
import Medications from './pages/Medications'
import HealthProfile from './pages/HealthProfile'
import HealthCopilot from './pages/HealthCopilot'
import AuthPage from './pages/AuthPage'
import CareEpisodes from './pages/CareEpisodes'
import Documents from './pages/Documents'
import MobileNav from './components/MobileNav';
import { api } from './services/api'
import {
  Activity, LayoutDashboard, UserRound, Pill, FileText,
  HeartPulse, MessageCircle, Settings, Bell, Search,
  Plus, ArrowUpRight, CalendarDays,
  Leaf, Menu, X, ChevronRight, ShieldCheck, Sparkles,
  WifiOff
} from 'lucide-react'

const navigation = [
  { label: 'Dashboard', icon: LayoutDashboard },
  { label: 'Health Profile', icon: UserRound },
  { label: 'Medications', icon: Pill },
  { label: 'Care Episodes', icon: HeartPulse },
  { label: 'Documents', icon: FileText },
  { label: 'Health Copilot', icon: MessageCircle },
]

function App() {
  const [active, setActive] = useState('Dashboard')
  const [mobileMenu, setMobileMenu] = useState(false)
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [backendStatus, setBackendStatus] = useState('checking') // 'checking' | 'connected' | 'disconnected'
  const [notice, setNotice] = useState(null)

  const showNotice = (msg) => {
    setNotice(msg)
    setTimeout(() => {
      setNotice((prev) => (prev === msg ? null : prev))
    }, 3500)
  }

  // Summary counts for Dashboard
  const [profileName, setProfileName] = useState(null)
  const [medicationsList, setMedicationsList] = useState([])
  const [documentsCount, setDocumentsCount] = useState(0)
  const [episodesCount, setEpisodesCount] = useState(0)

  useEffect(() => {
    let mounted = true
    async function syncData() {
      try {
        await api.checkHealth()
        if (mounted) setBackendStatus('connected')
      } catch {
        if (mounted) setBackendStatus('disconnected')
        return
      }

      try {
        const [prof, meds, docs, eps] = await Promise.allSettled([
          api.getProfile(),
          api.getMedications(),
          api.getDocuments(),
          api.getEpisodes(),
        ])

        if (!mounted) return

        if (prof.status === 'fulfilled' && prof.value?.full_name) {
          setProfileName(prof.value.full_name)
        }
        if (meds.status === 'fulfilled' && Array.isArray(meds.value)) {
          setMedicationsList(meds.value)
        }
        if (docs.status === 'fulfilled' && Array.isArray(docs.value)) {
          setDocumentsCount(docs.value.length)
        }
        if (eps.status === 'fulfilled' && Array.isArray(eps.value)) {
          setEpisodesCount(eps.value.length)
        }
      } catch {
        // non-critical dashboard sync
      }
    }

    syncData()
    return () => { mounted = false }
  }, [active, isLoggedIn])

  const selectPage = (label) => {
    setActive(label)
    setMobileMenu(false)
  }

  if (!isLoggedIn) {
    return <AuthPage onLogin={() => setIsLoggedIn(true)} />
  }

  return (
    <div className="min-h-screen flex bg-[#f7faf8]">
      {mobileMenu && (
        <button
          className="fixed inset-0 z-30 bg-black/20 sm:hidden"
          onClick={() => setMobileMenu(false)}
          aria-label="Close menu"
        />
      )}

      <aside className={`sidebar fixed z-40 flex flex-col p-5 transition-transform sm:static ${mobileMenu ? 'translate-x-0' : '-translate-x-full sm:translate-x-0'}`}>
        <div className="mb-10 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#dff3e9] text-[#347c66]">
              <HeartPulse size={25} />
            </div>
            <div className="brand-name">
              <h1 className="text-xl font-bold tracking-tight text-[#29463d]">MedBuddy</h1>
              <p className="text-xs text-[#91a39a]">Your health companion</p>
            </div>
          </div>
          <button className="sm:hidden text-gray-500" onClick={() => setMobileMenu(false)}>
            <X size={20} />
          </button>
        </div>

        <p className="nav-label mb-3 px-3 text-[10px] font-bold uppercase tracking-[0.16em] text-[#a3b0a9]">
          Workspace
        </p>

        <nav className="flex flex-col gap-1">
          {navigation.map(({ label, icon: Icon }) => (
            <button
              key={label}
              onClick={() => selectPage(label)}
              className={`nav-link ${active === label ? 'active' : ''}`}
            >
              <Icon size={19} strokeWidth={1.9} />
              <span className="nav-label">{label}</span>
            </button>
          ))}
        </nav>

        <div className="mt-auto">
          <div className="sidebar-footer mb-5 rounded-2xl bg-[#f1f8f3] p-4">
            <div className="mb-2 flex items-center gap-2 text-[#4d8b72]">
              <ShieldCheck size={18} />
              <span className="text-xs font-semibold">Safety Engine Active</span>
            </div>
            <p className="text-xs leading-5 text-[#81968a]">
              All queries and medications are verified with fail-closed safety checks.
            </p>
          </div>
          <button
            type="button"
            onClick={() => showNotice('System settings are pre-configured for this prototype demo.')}
            className="nav-link w-full text-left"
            aria-label="Open settings"
          >
            <Settings size={19} />
            <span className="nav-label">Settings</span>
          </button>
          <button
            type="button"
            onClick={() => selectPage('Health Profile')}
            className="sidebar-footer mt-5 flex w-full items-center gap-3 border-t border-[#edf1ee] pt-5 text-left transition hover:opacity-80"
            aria-label="View user profile"
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#fce9df] text-sm font-bold text-[#a76e51]">
              {profileName ? profileName.charAt(0).toUpperCase() : 'M'}
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-[#40564d]">
                {profileName || 'Demo User'}
              </p>
              <p className="text-xs text-[#9aa9a0]">Personal space</p>
            </div>
          </button>
        </div>
      </aside>

      <main className="min-w-0 flex-1">
        <header className="sticky top-0 z-20 flex h-[76px] items-center justify-between border-b border-[#edf1ee] bg-white/90 px-5 backdrop-blur-md sm:px-8">
          <div className="flex items-center gap-3">
            <button className="rounded-xl p-2 text-[#526d61] hover:bg-[#f1f7f3] sm:hidden" onClick={() => setMobileMenu(true)}>
              <Menu size={22} />
            </button>
            <div>
              <p className="text-xs text-[#98a79e]">Your personal health space</p>
              <h2 className="text-lg font-bold text-[#30483e]">{active}</h2>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Backend Connectivity Status Pill */}
            {backendStatus === 'connected' ? (
              <div className="flex items-center gap-2 rounded-full border border-[#d3eddc] bg-[#eef8f2] px-3 py-1.5 text-xs font-semibold text-[#2f7556]">
                <span className="h-2 w-2 rounded-full bg-[#34a853] animate-pulse" />
                <span>Backend Connected</span>
              </div>
            ) : backendStatus === 'disconnected' ? (
              <div className="flex items-center gap-2 rounded-full border border-[#f5d9d4] bg-[#fdf5f4] px-3 py-1.5 text-xs font-semibold text-[#b34033]">
                <WifiOff size={13} />
                <span>Backend Offline</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 rounded-full border border-[#edf1ee] bg-[#f9faf9] px-3 py-1.5 text-xs font-semibold text-[#8b9b92]">
                <span className="h-2 w-2 rounded-full bg-[#bcc7c0]" />
                <span>Connecting...</span>
              </div>
            )}

            <button
              type="button"
              onClick={() => showNotice('Global search (⌘ K) will be enabled in a future release.')}
              className="hidden items-center gap-2 rounded-xl border border-[#edf1ee] bg-[#fbfdfb] px-3 py-2 text-xs text-[#8b9b92] transition hover:bg-[#f4f7f5] md:flex"
              aria-label="Quick search"
            >
              <Search size={15} /> Search
              <span className="rounded bg-[#f0f3f0] px-1.5 py-0.5">⌘ K</span>
            </button>
            <button
              type="button"
              onClick={() => showNotice('You have no unread notifications at this time.')}
              className="relative rounded-xl border border-[#edf1ee] p-2.5 text-[#71877b] transition hover:bg-[#f7faf8]"
              aria-label="Notifications"
            >
              <Bell size={18} />
              <span className="absolute right-2 top-2 h-2 w-2 rounded-full border-2 border-white bg-[#ef9e79]" />
            </button>
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#e8f1ff] text-sm font-bold text-[#6484b4]">
              {profileName ? profileName.charAt(0).toUpperCase() : 'M'}
            </div>
          </div>
        </header>

        <div className="mx-auto max-w-[1440px] p-5 pb-28 sm:p-8">
          {active === 'Health Copilot' ? (
            <HealthCopilot />
          ) : active === 'Documents' ? (
            <Documents />
          ) : active === 'Care Episodes' ? (
            <CareEpisodes />
          ) : active === 'Medications' ? (
            <Medications />
          ) : active === 'Health Profile' ? (
            <HealthProfile />
          ) : active === 'Dashboard' ? (
            <>
              <section className="relative mb-7 overflow-hidden rounded-[24px] bg-gradient-to-r from-[#e5f5ec] via-[#edf7f0] to-[#f8eee6] p-6 sm:p-8">
                <div className="relative z-10 max-w-xl">
                  <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-white/70 px-3 py-1.5 text-xs font-semibold text-[#54836c]">
                    <Sparkles size={14} /> Your Personal Health Context Copilot
                  </div>
                  <h2 className="mb-2 text-2xl font-bold tracking-tight text-[#304c40] sm:text-3xl">
                    Welcome to MedBuddy 🌿
                  </h2>
                  <p className="max-w-md text-sm leading-6 text-[#71877a]">
                    Keep your medicines, health details and medical reports together in one simple place.
                  </p>
                  <button
                    onClick={() => selectPage('Health Profile')}
                    className="mt-5 inline-flex items-center gap-2 rounded-xl bg-[#4c9477] px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-[#397e62]"
                  >
                    {profileName ? 'Review your profile' : 'Complete your profile'} <ArrowUpRight size={16} />
                  </button>
                </div>
                <div className="pointer-events-none absolute -right-5 -top-12 hidden h-64 w-64 rounded-full border-[35px] border-white/30 sm:block" />
                <div className="pointer-events-none absolute bottom-[-65px] right-28 hidden h-48 w-48 rounded-full bg-[#d1e9d8]/50 sm:block" />
                <Leaf className="absolute bottom-8 right-12 hidden text-[#8dbb9c]/50 sm:block" size={75} strokeWidth={1} />
              </section>

              <div className="mb-5 flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-[#344c41]">Your health overview</h3>
                  <p className="mt-1 text-xs text-[#97a69d]">Live data retrieved from your backend persistent storage</p>
                </div>
                <span className="rounded-full bg-white px-3 py-1.5 text-xs text-[#8b9c92]">
                  <CalendarDays className="mr-1 inline" size={13} /> Today
                </span>
              </div>

              <section className="mb-7 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <div
                  onClick={() => selectPage('Health Profile')}
                  className="stat-card cursor-pointer border border-[#e5f0e8] bg-[#f0f8f2] transition hover:shadow-sm"
                >
                  <div className="mb-5 flex items-center justify-between">
                    <span className="text-sm font-medium text-[#71877a]">Health profile</span>
                    <span className="rounded-xl bg-white p-2 text-[#65a17d]"><UserRound size={19} /></span>
                  </div>
                  <p className="truncate text-xl font-bold text-[#3f6951]">
                    {profileName || 'Not set up'}
                  </p>
                  <p className="mt-2 text-xs text-[#8ca494]">
                    {profileName ? 'Profile configured' : 'Add your health details'}
                  </p>
                </div>

                <div
                  onClick={() => selectPage('Medications')}
                  className="stat-card cursor-pointer border border-[#f1e9df] bg-[#fff7ef] transition hover:shadow-sm"
                >
                  <div className="mb-5 flex items-center justify-between">
                    <span className="text-sm font-medium text-[#927e6b]">Medications</span>
                    <span className="rounded-xl bg-white p-2 text-[#d49a69]"><Pill size={19} /></span>
                  </div>
                  <p className="text-2xl font-bold text-[#876b50]">
                    {medicationsList.length} added
                  </p>
                  <p className="mt-2 text-xs text-[#ad9984]">Safety engine verified</p>
                </div>

                <div
                  onClick={() => selectPage('Documents')}
                  className="stat-card cursor-pointer border border-[#ebe6f5] bg-[#f6f2fc] transition hover:shadow-sm"
                >
                  <div className="mb-5 flex items-center justify-between">
                    <span className="text-sm font-medium text-[#827899]">Health documents</span>
                    <span className="rounded-xl bg-white p-2 text-[#9a84c6]"><FileText size={19} /></span>
                  </div>
                  <p className="text-2xl font-bold text-[#756395]">
                    {documentsCount} indexed
                  </p>
                  <p className="mt-2 text-xs text-[#a399b7]">ChromaDB vector store</p>
                </div>

                <div
                  onClick={() => selectPage('Care Episodes')}
                  className="stat-card cursor-pointer border border-[#e2edf5] bg-[#eff7fc] transition hover:shadow-sm"
                >
                  <div className="mb-5 flex items-center justify-between">
                    <span className="text-sm font-medium text-[#728b9c]">Care episodes</span>
                    <span className="rounded-xl bg-white p-2 text-[#77a4c4]"><Activity size={19} /></span>
                  </div>
                  <p className="text-2xl font-bold text-[#557d9b]">
                    {episodesCount} recorded
                  </p>
                  <p className="mt-2 text-xs text-[#91a8b7]">History and recovery updates</p>
                </div>
              </section>

              <section className="mb-7 grid grid-cols-1 gap-5 xl:grid-cols-[1.25fr_0.75fr]">
                <div className="panel p-5 sm:p-6">
                  <div className="mb-5 flex items-center justify-between">
                    <div>
                      <h3 className="font-bold text-[#344c41]">Current medication records</h3>
                      <p className="mt-1 text-xs text-[#9aa89f]">Your active medication overview</p>
                    </div>
                    <button onClick={() => selectPage('Medications')} className="text-xs font-semibold text-[#559477] hover:underline">
                      Manage <ChevronRight className="inline" size={14} />
                    </button>
                  </div>

                  {medicationsList.length === 0 ? (
                    <div className="rounded-2xl border border-dashed border-[#dce9df] bg-[#fbfdfb] px-4 py-8 text-center">
                      <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-[#eaf5ed] text-[#6b9d7c]">
                        <Pill size={22} />
                      </div>
                      <p className="text-sm font-semibold text-[#526b5b]">No medications added yet</p>
                      <p className="mt-1 text-xs text-[#9aa99e]">Add your medications to enable safety duplicate and allergy checking.</p>
                      <button onClick={() => selectPage('Medications')} className="mt-4 inline-flex items-center gap-2 rounded-xl bg-[#e8f4ec] px-4 py-2 text-xs font-semibold text-[#4c8765] hover:bg-[#dcefe2]">
                        <Plus size={15} /> Add medication
                      </button>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {medicationsList.slice(0, 3).map((med) => (
                        <div key={med.id} className="flex items-center justify-between rounded-xl border border-[#edf1ee] p-3.5">
                          <div className="flex items-center gap-3">
                            <div className="rounded-lg bg-[#eaf6f0] p-2 text-[#39866f]">
                              <Pill size={17} />
                            </div>
                            <div>
                              <p className="text-sm font-semibold text-[#30483e]">{med.name}</p>
                              <p className="text-xs text-[#84928c]">{med.strength} · {med.dosage} · {med.route}</p>
                            </div>
                          </div>
                          <span className="rounded-md bg-[#edf5f0] px-2 py-1 text-xs font-medium text-[#3b7558]">
                            {med.frequency || 'Active'}
                          </span>
                        </div>
                      ))}
                      {medicationsList.length > 3 && (
                        <p className="text-center text-xs text-[#84928c]">
                          + {medicationsList.length - 3} more medications
                        </p>
                      )}
                    </div>
                  )}
                  <p className="mt-3 text-[11px] leading-5 text-[#a1aaa4]">
                    MedBuddy is a context organization tool, not a replacement for professional clinical care.
                  </p>
                </div>

                <div className="panel p-5 sm:p-6">
                  <div className="mb-5">
                    <h3 className="font-bold text-[#344c41]">Health Copilot Quick Ask</h3>
                    <p className="mt-1 text-xs text-[#9aa89f]">Direct consultation grounded in your data</p>
                  </div>
                  <div className="flex flex-col gap-3">
                    <button
                      onClick={() => selectPage('Health Copilot')}
                      className="rounded-xl border border-[#e5ece7] bg-[#fbfdfb] p-3.5 text-left transition hover:border-[#9ecdb4] hover:bg-[#f4f9f6]"
                    >
                      <p className="text-xs font-semibold text-[#30483e]">Review medication interactions</p>
                      <p className="mt-1 text-[11px] text-[#84928c]">Check your current medications against known allergies</p>
                    </button>
                    <button
                      onClick={() => selectPage('Health Copilot')}
                      className="rounded-xl border border-[#e5ece7] bg-[#fbfdfb] p-3.5 text-left transition hover:border-[#9ecdb4] hover:bg-[#f4f9f6]"
                    >
                      <p className="text-xs font-semibold text-[#30483e]">Ask about uploaded documents</p>
                      <p className="mt-1 text-[11px] text-[#84928c]">Retrieve cited excerpts from indexed medical PDFs</p>
                    </button>
                    <button
                      onClick={() => selectPage('Health Copilot')}
                      className="rounded-xl border border-[#e5ece7] bg-[#fbfdfb] p-3.5 text-left transition hover:border-[#9ecdb4] hover:bg-[#f4f9f6]"
                    >
                      <p className="text-xs font-semibold text-[#30483e]">Safety & emergency detection</p>
                      <p className="mt-1 text-[11px] text-[#84928c]">Immediate red-alert bypass for urgent symptoms</p>
                    </button>
                  </div>
                </div>
              </section>

              <section className="panel flex flex-col items-start justify-between gap-4 bg-gradient-to-r from-white to-[#f4f8ff] p-5 sm:flex-row sm:items-center sm:p-6">
                <div className="flex items-start gap-3">
                  <div className="rounded-2xl bg-[#e9effc] p-3 text-[#8197c1]">
                    <MessageCircle size={22} />
                  </div>
                  <div>
                    <h3 className="font-bold text-[#43546d]">Ready to ask your Health Copilot?</h3>
                    <p className="mt-1 max-w-lg text-xs leading-5 text-[#91a0b4]">
                      Ask questions in plain language. Answers are cited with document page numbers and verified through our Safety Engine.
                    </p>
                  </div>
                </div>
                <button onClick={() => selectPage('Health Copilot')} className="shrink-0 rounded-xl bg-[#718bb8] px-4 py-2.5 text-xs font-semibold text-white hover:bg-[#617ba8]">
                  Explore Copilot <ArrowUpRight className="ml-1 inline" size={14} />
                </button>
              </section>
            </>
          ) : null}

          <footer className="mt-8 flex flex-col justify-between gap-2 border-t border-[#eaf0eb] pt-5 text-[11px] text-[#a2afa6] sm:flex-row">
            <span>© 2026 MedBuddy · YOUR HEALTH COMPANION</span>
            <span className="flex items-center gap-1"><ShieldCheck size={13} /> Designed with care for your health information</span>
          </footer>
        </div>

        {notice && (
          <div
            role="status"
            aria-live="polite"
            className="fixed bottom-6 right-6 z-50 flex items-center gap-2 rounded-xl border border-[#cbe2d6] bg-[#f0f8f4] px-4 py-3 text-xs font-medium text-[#2f5c49] shadow-lg"
          >
            <Sparkles size={16} className="text-[#347c66]" />
            <span>{notice}</span>
            <button
              type="button"
              onClick={() => setNotice(null)}
              className="ml-2 text-[#718e81] hover:text-[#2f5c49]"
              aria-label="Dismiss notice"
            >
              <X size={14} />
            </button>
          </div>
          
        )}
      </main>
      <div className="md:hidden">
  <MobileNav
    active={active}
    onNavigate={setActive}
  />
</div>
    </div>
  )
}

export default App
