import { useState } from 'react'
import Medications from './pages/Medications'
import HealthProfile from './pages/HealthProfile'
import HealthCopilot from './pages/HealthCopilot'
import AuthPage from './pages/AuthPage'
import CareEpisodes from './pages/CareEpisodes'
import Documents from './pages/Documents'
import {
  Activity, LayoutDashboard, UserRound, Pill, FileText,
  HeartPulse, MessageCircle, Settings, Bell, Search,
  Plus, ArrowUpRight, CalendarDays, Clock3, CheckCircle2,
  Leaf, Menu, X, ChevronRight, ShieldCheck, Sparkles,
} from 'lucide-react'

const navigation = [
  { label: 'Dashboard', icon: LayoutDashboard },
  { label: 'Health Profile', icon: UserRound },
  { label: 'Medications', icon: Pill },
  { label: 'Care Episodes', icon: HeartPulse },
  { label: 'Documents', icon: FileText },
  { label: 'Health Copilot', icon: MessageCircle },
]

const activities = [
  { title: 'Health profile created', detail: 'Your personal health space is ready', time: 'Today', color: '#e6f4ed', icon: UserRound },
  { title: 'Medication schedule', detail: 'Your daily schedule is available', time: 'Today', color: '#f1eaff', icon: Pill },
  { title: 'Welcome to MedBuddy', detail: 'Explore your personal health dashboard', time: 'Today', color: '#fff0e6', icon: HeartPulse },
]

function App() {
  const [active, setActive] = useState('Dashboard')
  const [mobileMenu, setMobileMenu] = useState(false)
  const [isLoggedIn, setIsLoggedIn] = useState(false)

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
              <span className="text-xs font-semibold">Your privacy matters</span>
            </div>
            <p className="text-xs leading-5 text-[#81968a]">
              Your health information deserves care and protection.
            </p>
          </div>
          <button className="nav-link">
            <Settings size={19} />
            <span className="nav-label">Settings</span>
          </button>
          <div className="sidebar-footer mt-5 flex items-center gap-3 border-t border-[#edf1ee] pt-5">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#fce9df] text-sm font-bold text-[#a76e51]">
              M
            </div>
            <div>
              <p className="text-sm font-semibold text-[#40564d]">My Account</p>
              <p className="text-xs text-[#9aa9a0]">Personal space</p>
            </div>
          </div>
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
            <button className="hidden items-center gap-2 rounded-xl border border-[#edf1ee] bg-[#fbfdfb] px-3 py-2 text-xs text-[#8b9b92] md:flex">
              <Search size={15} /> Search
              <span className="rounded bg-[#f0f3f0] px-1.5 py-0.5">⌘ K</span>
            </button>
            <button className="relative rounded-xl border border-[#edf1ee] p-2.5 text-[#71877b] hover:bg-[#f7faf8]" aria-label="Notifications">
              <Bell size={18} />
              <span className="absolute right-2 top-2 h-2 w-2 rounded-full border-2 border-white bg-[#ef9e79]" />
            </button>
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#e8f1ff] text-sm font-bold text-[#6484b4]">
              M
            </div>
          </div>
        </header>

        <div className="mx-auto max-w-[1440px] p-5 sm:p-8">
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
                    <Sparkles size={14} /> A healthier way to stay informed
                  </div>
                  <h2 className="mb-2 text-2xl font-bold tracking-tight text-[#304c40] sm:text-3xl">
                    Welcome to your health space 🌿
                  </h2>
                  <p className="max-w-md text-sm leading-6 text-[#71877a]">
                    Keep your health information organised, understand your records, and stay connected with your health journey.
                  </p>
                  <button
                    onClick={() => selectPage('Health Profile')}
                    className="mt-5 inline-flex items-center gap-2 rounded-xl bg-[#4c9477] px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-[#397e62]"
                  >
                    Complete your profile <ArrowUpRight size={16} />
                  </button>
                </div>
                <div className="pointer-events-none absolute -right-5 -top-12 hidden h-64 w-64 rounded-full border-[35px] border-white/30 sm:block" />
                <div className="pointer-events-none absolute bottom-[-65px] right-28 hidden h-48 w-48 rounded-full bg-[#d1e9d8]/50 sm:block" />
                <Leaf className="absolute bottom-8 right-12 hidden text-[#8dbb9c]/50 sm:block" size={75} strokeWidth={1} />
              </section>

              <div className="mb-5 flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-[#344c41]">Your health overview</h3>
                  <p className="mt-1 text-xs text-[#97a69d]">A quick look at your personal health space</p>
                </div>
                <span className="rounded-full bg-white px-3 py-1.5 text-xs text-[#8b9c92]">
                  <CalendarDays className="mr-1 inline" size={13} /> Today
                </span>
              </div>

              <section className="mb-7 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <div className="stat-card border border-[#e5f0e8] bg-[#f0f8f2]">
                  <div className="mb-5 flex items-center justify-between">
                    <span className="text-sm font-medium text-[#71877a]">Health profile</span>
                    <span className="rounded-xl bg-white p-2 text-[#65a17d]"><UserRound size={19} /></span>
                  </div>
                  <p className="text-2xl font-bold text-[#3f6951]">Not set up</p>
                  <p className="mt-2 text-xs text-[#8ca494]">Add your health information</p>
                </div>

                <div className="stat-card border border-[#f1e9df] bg-[#fff7ef]">
                  <div className="mb-5 flex items-center justify-between">
                    <span className="text-sm font-medium text-[#927e6b]">Medications</span>
                    <span className="rounded-xl bg-white p-2 text-[#d49a69]"><Pill size={19} /></span>
                  </div>
                  <p className="text-2xl font-bold text-[#876b50]">0 added</p>
                  <p className="mt-2 text-xs text-[#ad9984]">Keep your list organised</p>
                </div>

                <div className="stat-card border border-[#ebe6f5] bg-[#f6f2fc]">
                  <div className="mb-5 flex items-center justify-between">
                    <span className="text-sm font-medium text-[#827899]">Health documents</span>
                    <span className="rounded-xl bg-white p-2 text-[#9a84c6]"><FileText size={19} /></span>
                  </div>
                  <p className="text-2xl font-bold text-[#756395]">0 uploaded</p>
                  <p className="mt-2 text-xs text-[#a399b7]">Your records in one place</p>
                </div>

                <div className="stat-card border border-[#e2edf5] bg-[#eff7fc]">
                  <div className="mb-5 flex items-center justify-between">
                    <span className="text-sm font-medium text-[#728b9c]">Care episodes</span>
                    <span className="rounded-xl bg-white p-2 text-[#77a4c4]"><Activity size={19} /></span>
                  </div>
                  <p className="text-2xl font-bold text-[#557d9b]">0 recorded</p>
                  <p className="mt-2 text-xs text-[#91a8b7]">Track your health history</p>
                </div>
              </section>

              <section className="mb-7 grid grid-cols-1 gap-5 xl:grid-cols-[1.25fr_0.75fr]">
                <div className="panel p-5 sm:p-6">
                  <div className="mb-5 flex items-center justify-between">
                    <div>
                      <h3 className="font-bold text-[#344c41]">Today's medication schedule</h3>
                      <p className="mt-1 text-xs text-[#9aa89f]">Your daily medication overview</p>
                    </div>
                    <button onClick={() => selectPage('Medications')} className="text-xs font-semibold text-[#559477] hover:underline">
                      View all <ChevronRight className="inline" size={14} />
                    </button>
                  </div>
                  <div className="rounded-2xl border border-dashed border-[#dce9df] bg-[#fbfdfb] px-4 py-8 text-center">
                    <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-[#eaf5ed] text-[#6b9d7c]">
                      <Pill size={22} />
                    </div>
                    <p className="text-sm font-semibold text-[#526b5b]">No medications added yet</p>
                    <p className="mt-1 text-xs text-[#9aa99e]">Add your medication list to organise your schedule.</p>
                    <button onClick={() => selectPage('Medications')} className="mt-4 inline-flex items-center gap-2 rounded-xl bg-[#e8f4ec] px-4 py-2 text-xs font-semibold text-[#4c8765] hover:bg-[#dcefe2]">
                      <Plus size={15} /> Add medication
                    </button>
                  </div>
                  <p className="mt-3 text-[11px] leading-5 text-[#a1aaa4]">
                    MedBuddy is an organisation tool, not a replacement for professional medication advice.
                  </p>
                </div>

                <div className="panel p-5 sm:p-6">
                  <div className="mb-5">
                    <h3 className="font-bold text-[#344c41]">Your health activity</h3>
                    <p className="mt-1 text-xs text-[#9aa89f]">Recent updates in your space</p>
                  </div>
                  <div className="flex flex-col gap-5">
                    {activities.map(({ title, detail, time, color, icon: Icon }) => (
                      <div key={title} className="flex items-start gap-3">
                        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl" style={{ background: color }}>
                          <Icon size={18} className="text-[#6d8b78]" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-semibold text-[#4a5e52]">{title}</p>
                          <p className="mt-1 text-xs leading-5 text-[#96a49a]">{detail}</p>
                        </div>
                        <span className="text-[10px] text-[#a7b2aa]">{time}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </section>

              <section className="panel flex flex-col items-start justify-between gap-4 bg-gradient-to-r from-white to-[#f4f8ff] p-5 sm:flex-row sm:items-center sm:p-6">
                <div className="flex items-start gap-3">
                  <div className="rounded-2xl bg-[#e9effc] p-3 text-[#8197c1]">
                    <MessageCircle size={22} />
                  </div>
                  <div>
                    <h3 className="font-bold text-[#43546d]">Have questions about your health records?</h3>
                    <p className="mt-1 max-w-lg text-xs leading-5 text-[#91a0b4]">
                      Your Health Copilot will help you understand your health information in simple language.
                    </p>
                  </div>
                </div>
                <button onClick={() => selectPage('Health Copilot')} className="shrink-0 rounded-xl bg-[#718bb8] px-4 py-2.5 text-xs font-semibold text-white hover:bg-[#617ba8]">
                  Explore Copilot <ArrowUpRight className="ml-1 inline" size={14} />
                </button>
              </section>
            </>
          ) : (
            <section className="panel mx-auto mt-8 max-w-2xl p-8 text-center sm:p-12">
              <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-[#e9f5ed] text-[#629578]">
                {active === 'Health Profile' && <UserRound size={28} />}
                {active === 'Medications' && <Pill size={28} />}
                {active === 'Care Episodes' && <HeartPulse size={28} />}
                {active === 'Documents' && <FileText size={28} />}
                {active === 'Health Copilot' && <MessageCircle size={28} />}
              </div>
              <h2 className="text-xl font-bold text-[#344c41]">{active}</h2>
              <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-[#91a197]">
                This section is part of the MedBuddy frontend. We'll build its functionality and connect it to the backend in the next stages.
              </p>
              <button onClick={() => selectPage('Dashboard')} className="mt-6 rounded-xl bg-[#e8f4ec] px-5 py-2.5 text-sm font-semibold text-[#4c8765]">
                Back to dashboard
              </button>
            </section>
          )}

          <footer className="mt-8 flex flex-col justify-between gap-2 border-t border-[#eaf0eb] pt-5 text-[11px] text-[#a2afa6] sm:flex-row">
            <span>© 2026 MedBuddy · Your Personal Health Context Copilot</span>
            <span className="flex items-center gap-1"><ShieldCheck size={13} /> Designed with care for your health information</span>
          </footer>
        </div>
      </main>
    </div>
  )
}

export default App