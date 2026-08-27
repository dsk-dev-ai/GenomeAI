export default function Loading() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="flex items-center gap-3">
        <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-genome-500 to-genome-700 text-xl">
          🧬
        </span>
        <div>
          <p className="font-bold text-slate-900">
            Genome<span className="text-gradient">AI</span>
          </p>
          <p className="text-sm text-slate-500">Loading…</p>
        </div>
      </div>
      <div className="mt-6 h-1 w-48 overflow-hidden rounded-full bg-slate-100">
        <div
          className="h-full w-1/3 rounded-full bg-gradient-to-r from-genome-500 to-indigo-400 animate-gradient-x"
          style={{ backgroundSize: '200% auto' }}
        />
      </div>
    </main>
  )
}
