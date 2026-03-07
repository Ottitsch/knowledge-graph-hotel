import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Nav from './components/Nav'
import Panel from './components/Panel'
import ForceGraph from './components/graph/ForceGraph'
import TopOperators from './components/charts/TopOperators'
import ChainBar from './components/charts/ChainBar'
import DistrictBar from './components/charts/DistrictBar'
import CorporateBar from './components/charts/CorporateBar'
import TypePie from './components/charts/TypePie'
import PropertyMap from './components/map/PropertyMap'
import OperatorMap from './components/map/OperatorMap'

const fadeVariant = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.35, ease: 'easeOut' } },
  exit: { opacity: 0, y: -8, transition: { duration: 0.2 } },
}

function SizeObserver({ children }) {
  const ref = useRef()
  const [size, setSize] = useState({ w: 500, h: 420 })

  useEffect(() => {
    if (!ref.current) return
    const obs = new ResizeObserver(([entry]) => {
      setSize({ w: entry.contentRect.width || 500, h: 420 })
    })
    obs.observe(ref.current)
    return () => obs.disconnect()
  }, [])

  return (
    <div ref={ref} className="w-full" style={{ height: 420 }}>
      {children(size.w, size.h)}
    </div>
  )
}

function GraphTab() {
  const [selectedOperator, setSelectedOperator] = useState(null)

  return (
    <motion.div {...fadeVariant} className="grid grid-cols-1 xl:grid-cols-2 gap-5">
      <Panel title="Force Graph — click an operator node to explore">
        <SizeObserver>
          {(w, h) => (
            <ForceGraph width={w} height={h} onOperatorClick={setSelectedOperator} />
          )}
        </SizeObserver>
      </Panel>

      <Panel title="Operator Listings Map — listings by selected operator">
        <OperatorMap operatorName={selectedOperator} />
      </Panel>

    </motion.div>
  )
}

function AnalyticsTab() {
  return (
    <motion.div {...fadeVariant} className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-5">
      <Panel title="Top 20 Operators by listings" className="xl:col-span-2">
        <TopOperators />
      </Panel>
      <Panel title="Hotel Chains by property count">
        <ChainBar />
      </Panel>
      <Panel title="Properties by District">
        <DistrictBar />
      </Panel>
      <Panel title="Corporate vs Individual by District" className="xl:col-span-2">
        <CorporateBar />
      </Panel>
      <Panel title="Property Types">
        <TypePie />
      </Panel>
    </motion.div>
  )
}

function MapTab() {
  return (
    <motion.div {...fadeVariant}>
      <Panel title="Vienna — all geolocated properties">
        <PropertyMap />
      </Panel>
    </motion.div>
  )
}

export default function App() {
  const [tab, setTab] = useState('graph')

  return (
    <div className="min-h-screen p-4 md:p-8 flex flex-col gap-6">
      <header className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Vienna Hotel{' '}
            <span style={{ color: '#2dd4bf' }}>Knowledge Graph</span>
          </h1>
          <p className="text-sm text-white/40 mt-0.5">
            Airbnb listings · Neo4j · {new Date().getFullYear()}
          </p>
        </div>
        <Nav active={tab} onChange={setTab} />
      </header>

      <main className="flex-1">
        <AnimatePresence mode="wait">
          {tab === 'graph' && <GraphTab key="graph" />}
          {tab === 'analytics' && <AnalyticsTab key="analytics" />}
          {tab === 'map' && <MapTab key="map" />}
        </AnimatePresence>
      </main>

      <footer className="text-center text-white/20 text-xs pb-2">
        Knowledge Graph Dashboard · Vienna Hotel Market Analysis
      </footer>
    </div>
  )
}
