import Link from 'next/link'

export default function NotFound() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="text-7xl font-extrabold text-gradient">404</div>
      <p className="mt-4 text-slate-600">Page not found</p>
      <Link
        href="/"
        className="mt-6 rounded-xl bg-gradient-to-r from-genome-600 to-genome-500 px-6 py-2.5 text-sm font-semibold text-white shadow-glow transition hover:brightness-110"
      >
        Return home
      </Link>
    </main>
  )
}
