'use client'

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-red-500 to-red-700 text-2xl text-white shadow-glow">
        ⚠️
      </span>
      <h1 className="mt-5 text-2xl font-bold text-slate-900">Something went wrong</h1>
      <p className="mt-2 max-w-md text-center text-slate-600">{error.message}</p>
      <button
        onClick={() => reset()}
        type="button"
        className="mt-6 rounded-xl bg-gradient-to-r from-genome-600 to-genome-500 px-6 py-2.5 text-sm font-semibold text-white shadow-glow transition hover:brightness-110"
      >
        Try again
      </button>
    </main>
  )
}
