'use client'

import { motion } from 'framer-motion'

interface SkeletonProps {
  className?: string
  variant?: 'text' | 'circular' | 'rectangular'
  width?: string | number
  height?: string | number
}

export function Skeleton({ 
  className = '', 
  variant = 'rectangular',
  width,
  height 
}: SkeletonProps) {
  const baseClasses = 'animate-pulse bg-gray-800'
  
  const variantClasses = {
    text: 'rounded-sm h-4',
    circular: 'rounded-full',
    rectangular: 'rounded-lg',
  }

  const style: React.CSSProperties = {
    width: width || '100%',
    height: height || (variant === 'text' ? '1rem' : '100%'),
  }

  return (
    <motion.div
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      style={style}
      animate={{ opacity: [0.4, 0.8, 0.4] }}
      transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
    />
  )
}

// Pre-built skeleton components for common use cases
export function ChatMessageSkeleton() {
  return (
    <div className="flex gap-3 p-4">
      <Skeleton variant="circular" width={40} height={40} />
      <div className="flex-1 space-y-2">
        <Skeleton variant="text" width="60%" />
        <Skeleton variant="rectangular" height={80} />
      </div>
    </div>
  )
}

export function MediaCardSkeleton() {
  return (
    <div className="rounded-lg overflow-hidden bg-gray-900 p-4">
      <Skeleton variant="rectangular" height={200} className="mb-3" />
      <Skeleton variant="text" width="80%" />
      <Skeleton variant="text" width="40%" />
    </div>
  )
}

export function DashboardCardSkeleton() {
  return (
    <div className="rounded-lg bg-gray-900 p-6 space-y-3">
      <Skeleton variant="text" width="50%" />
      <Skeleton variant="rectangular" height={40} />
      <Skeleton variant="text" width="30%" />
    </div>
  )
}

export function PageSkeleton() {
  return (
    <div className="container mx-auto p-6 space-y-6">
      <Skeleton variant="text" width="40%" height={32} />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <DashboardCardSkeleton />
        <DashboardCardSkeleton />
        <DashboardCardSkeleton />
      </div>
      <Skeleton variant="rectangular" height={300} />
    </div>
  )
}