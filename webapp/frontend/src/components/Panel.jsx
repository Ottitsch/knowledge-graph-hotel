import { motion } from 'framer-motion'

export default function Panel({ title, children, className = '' }) {
  return (
    <motion.div
      className={`glass p-5 flex flex-col gap-3 ${className}`}
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
    >
      {title && (
        <h2 className="text-sm font-semibold uppercase tracking-widest text-white/50">
          {title}
        </h2>
      )}
      <div className="flex-1 min-h-0">{children}</div>
    </motion.div>
  )
}
