const TABS = [
  { id: 'graph', label: 'Graph Explorer' },
  { id: 'analytics', label: 'Analytics' },
  { id: 'map', label: 'Map' },
]

export default function Nav({ active, onChange }) {
  return (
    <nav className="flex items-center gap-1 p-1 glass rounded-2xl">
      {TABS.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={`px-5 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
            active === tab.id
              ? 'bg-teal-500/20 text-teal-300 border border-teal-500/30'
              : 'text-white/50 hover:text-white/80 hover:bg-white/5'
          }`}
          style={active === tab.id ? { color: '#2dd4bf' } : {}}
        >
          {tab.label}
        </button>
      ))}
    </nav>
  )
}
