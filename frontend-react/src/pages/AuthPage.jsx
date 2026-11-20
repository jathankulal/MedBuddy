
import { useState } from 'react'
import {
  HeartPulse, Mail, Lock, Eye, EyeOff, ArrowRight,
  ShieldCheck, Leaf, UserRound, Sparkles
} from 'lucide-react'

export default function AuthPage({ onLogin }) {
  const [mode, setMode] = useState('login')
  const [showPassword, setShowPassword] = useState(false)
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    setError('')

    if (mode === 'signup' && !name.trim()) {
      setError('Please enter your name.')
      return
    }

    if (!email.trim() || !/^\S+@\S+\.\S+$/.test(email)) {
      setError('Please enter a valid email address.')
      return
    }

    if (password.length < 8) {
      setError('Password must contain at least 8 characters.')
      return
    }

    // Demo only: real authentication will be connected later.
    onLogin?.()
  }

  return (
    <div className="min-h-screen bg-[#f5faf6] p-4 sm:p-8">
      <div className="mx-auto grid min-h-[calc(100vh-64px)] max-w-6xl overflow-hidden rounded-[28px] bg-white shadow-[0_12px_50px_rgba(53,91,68,0.08)] lg:grid-cols-2">

        <section className="relative hidden overflow-hidden bg-gradient-to-br from-[#e1f3e8] via-[#edf6ee] to-[#f9eee5] p-12 lg:flex lg:flex-col lg:justify-between">
          <div className="relative z-10 flex items-center gap-3">
            <div className="rounded-2xl bg-white p-3 text-[#4d9273] shadow-sm">
              <HeartPulse size={28} />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-[#315343]">MedBuddy</h1>
              <p className="text-xs text-[#829b89]">Your health companion</p>
            </div>
          </div>

          <div className="relative z-10 max-w-md">
            <div className="mb-5 inline-flex items-center gap-2 rounded-full bg-white/70 px-4 py-2 text-xs font-semibold text-[#54866a]">
              <Sparkles size={15} />
              Your health, organised
            </div>

            <h2 className="text-4xl font-bold leading-tight text-[#345746]">
              A little more care for your everyday health.
            </h2>

            <p className="mt-5 text-sm leading-7 text-[#789182]">
              Keep your health information together, understand your records,
              and make more informed conversations with your healthcare team.
            </p>

            <div className="mt-9 flex items-center gap-4 rounded-2xl border border-white/70 bg-white/60 p-4">
              <div className="rounded-xl bg-[#e2f2e7] p-3 text-[#5d9874]">
                <ShieldCheck size={23} />
              </div>
              <div>
                <p className="text-sm font-semibold text-[#486a55]">Your health matters</p>
                <p className="mt-1 text-xs text-[#8ba092]">A space designed with care and clarity.</p>
              </div>
            </div>
          </div>

          <div className="relative z-10 flex items-center gap-2 text-xs text-[#8aa091]">
            <Leaf size={16} /> Small steps towards better health awareness.
          </div>

          <div className="pointer-events-none absolute -bottom-20 -right-20 h-80 w-80 rounded-full border-[45px] border-white/30" />
          <div className="pointer-events-none absolute right-12 top-28 h-32 w-32 rounded-full bg-white/25" />
        </section>

        <section className="flex items-center justify-center px-5 py-12 sm:px-12 lg:px-16">
          <div className="w-full max-w-md">

            <div className="mb-9 flex items-center gap-3 lg:hidden">
              <div className="rounded-xl bg-[#e5f4e9] p-2.5 text-[#4d9273]">
                <HeartPulse size={25} />
              </div>
              <div>
                <h1 className="text-xl font-bold text-[#315343]">MedBuddy</h1>
                <p className="text-xs text-[#8ba092]">Your health companion</p>
              </div>
            </div>

            <div className="mb-6 rounded-2xl border border-[#d6ecde] bg-[#f0f9f3] p-4 text-xs leading-5 text-[#3d6e53]">
              <div className="flex items-center gap-2 font-bold text-[#2e5942]">
                <ShieldCheck size={16} />
                <span>Single-User Prototype Demo</span>
              </div>
              <p className="mt-1">
                Real multi-user authentication is not implemented on the backend yet. You can click below to enter directly into the persistent demo environment.
              </p>
              <button
                type="button"
                onClick={() => onLogin?.()}
                className="mt-3 flex w-full items-center justify-center gap-2 rounded-xl bg-[#39866f] py-2.5 text-xs font-semibold text-white shadow-sm transition hover:bg-[#2d6f5b]"
              >
                <span>Enter Demo Workspace</span>
                <ArrowRight size={14} />
              </button>
            </div>

            <div className="mb-8">
              <p className="mb-3 text-xs font-semibold uppercase tracking-[0.15em] text-[#72a084]">
                Welcome to MedBuddy
              </p>
              <h2 className="text-3xl font-bold tracking-tight text-[#304b3d]">
                {mode === 'login' ? 'Welcome back!' : 'Create your account'}
              </h2>
              <p className="mt-2 text-sm leading-6 text-[#94a39a]">
                {mode === 'login'
                  ? 'Sign in to continue to your personal health space.'
                  : 'Start organising your personal health information.'}
              </p>
            </div>

            <div className="mb-7 grid grid-cols-2 rounded-xl bg-[#f3f7f3] p-1">
              <button
                onClick={() => { setMode('login'); setError('') }}
                className={`rounded-lg py-2.5 text-sm font-semibold transition ${
                  mode === 'login'
                    ? 'bg-white text-[#477c5e] shadow-sm'
                    : 'text-[#91a097]'
                }`}
              >
                Sign in
              </button>
              <button
                onClick={() => { setMode('signup'); setError('') }}
                className={`rounded-lg py-2.5 text-sm font-semibold transition ${
                  mode === 'signup'
                    ? 'bg-white text-[#477c5e] shadow-sm'
                    : 'text-[#91a097]'
                }`}
              >
                Create account
              </button>
            </div>

            <button
              type="button"
              onClick={() => setError('Google sign-in will be enabled when authentication is connected.')}
              className="flex w-full items-center justify-center gap-3 rounded-xl border border-[#e7ede8] py-3 text-sm font-semibold text-[#52685a] transition hover:bg-[#f8fbf8]"
            >
              <svg viewBox="0 0 48 48" className="h-5 w-5" aria-hidden="true">
                <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z" transform="translate(0 5)"/>
                <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.25 5.48-4.73 7.18l7.65 5.93c4.47-4.13 7.12-10.21 7.12-17.58z"/>
                <path fill="#FBBC05" d="M10.53 28.59a14.4 14.4 0 0 1 0-9.18l-7.98-6.19a24 24 0 0 0 0 21.56z"/>
                <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.9-5.87l-7.65-5.93c-2.12 1.42-4.84 2.27-8.25 2.27-6.26 0-11.57-4.22-13.46-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
              </svg>
              Continue with Google
            </button>

            <div className="my-6 flex items-center gap-4">
              <div className="h-px flex-1 bg-[#edf1ed]" />
              <span className="text-xs text-[#a5b0a8]">OR CONTINUE WITH EMAIL</span>
              <div className="h-px flex-1 bg-[#edf1ed]" />
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {mode === 'signup' && (
                <div>
                  <label className="mb-2 block text-xs font-semibold text-[#586d5e]">Full name</label>
                  <div className="flex items-center gap-3 rounded-xl border border-[#e7ede8] px-4 py-3 focus-within:border-[#91bba0]">
                    <UserRound size={18} className="text-[#9bad9f]" />
                    <input
                      value={name}
                      onChange={e => setName(e.target.value)}
                      placeholder="Enter your name"
                      className="w-full bg-transparent text-sm outline-none placeholder:text-[#b1bcb4]"
                    />
                  </div>
                </div>
              )}

              <div>
                <label className="mb-2 block text-xs font-semibold text-[#586d5e]">Email address</label>
                <div className="flex items-center gap-3 rounded-xl border border-[#e7ede8] px-4 py-3 focus-within:border-[#91bba0]">
                  <Mail size={18} className="text-[#9bad9f]" />
                  <input
                    type="email"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    placeholder="you@example.com"
                    className="w-full bg-transparent text-sm outline-none placeholder:text-[#b1bcb4]"
                  />
                </div>
              </div>

              <div>
                <div className="mb-2 flex items-center justify-between">
                  <label className="text-xs font-semibold text-[#586d5e]">Password</label>
                  {mode === 'login' && (
                    <button
                      type="button"
                      onClick={() => setError('Password recovery will be available after authentication is connected.')}
                      className="text-xs font-semibold text-[#629879] hover:underline"
                    >
                      Forgot password?
                    </button>
                  )}
                </div>
                <div className="flex items-center gap-3 rounded-xl border border-[#e7ede8] px-4 py-3 focus-within:border-[#91bba0]">
                  <Lock size={18} className="text-[#9bad9f]" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    placeholder="At least 8 characters"
                    className="w-full bg-transparent text-sm outline-none placeholder:text-[#b1bcb4]"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="text-[#9bad9f]"
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              {error && (
                <p role="alert" className="rounded-xl bg-[#fff0ed] px-4 py-3 text-xs leading-5 text-[#b35d50]">
                  {error}
                </p>
              )}

              <button
                type="submit"
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#559574] py-3.5 text-sm font-semibold text-white shadow-sm transition hover:bg-[#427f61]"
              >
                {mode === 'login' ? 'Sign in to MedBuddy' : 'Create my account'}
                <ArrowRight size={17} />
              </button>
            </form>

            <p className="mt-7 text-center text-xs leading-6 text-[#9ba89f]">
              By continuing, you acknowledge that MedBuddy is a health information
              organisation tool, not a substitute for professional medical advice.
            </p>
          </div>
        </section>
      </div>
    </div>
  )
}
