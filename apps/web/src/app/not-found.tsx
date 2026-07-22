import Link from 'next/link'

export default function NotFound() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <h1 className="text-4xl font-bold">404</h1>
      <p className="mt-4 text-gray-600">Page not found</p>
      <Link href="/" className="mt-6 text-blue-600 hover:underline">
        Return home
      </Link>
    </main>
  )
}
