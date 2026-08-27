'use client'

import { useEffect, useRef, useState } from 'react'

interface RevealProps {
  children: React.ReactNode
  className?: string
  delay?: number
  variant?: 'up' | 'down' | 'fade' | 'scale' | 'right'
}

const animations: Record<NonNullable<RevealProps['variant']>, string> = {
  up: 'fade-in-up',
  down: 'fade-in-down',
  fade: 'fade-in',
  scale: 'scale-in',
  right: 'slide-in-right',
}

export function Reveal({ children, className = '', delay = 0, variant = 'up' }: RevealProps) {
  const ref = useRef<HTMLDivElement>(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const node = ref.current
    if (!node) return
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true)
          observer.disconnect()
        }
      },
      { threshold: 0.12 },
    )
    observer.observe(node)
    return () => observer.disconnect()
  }, [])

  return (
    <div
      ref={ref}
      className={className}
      style={{
        opacity: visible ? 1 : 0,
        transition: `opacity 0.6s ease-out ${delay}ms, transform 0.6s ease-out ${delay}ms`,
        transform: visible ? 'none' : undefined,
      }}
    >
      <div className={`${visible ? `animate-${animations[variant]}` : 'opacity-0'}`}>
        {children}
      </div>
    </div>
  )
}
