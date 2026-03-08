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
import QualitySummary from './components/QualitySummary'
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

function GraphTab({ selected, onForceGraphSelect }) {
  return (
    <motion.div {...fadeVariant} className="flex flex-col gap-5">
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
        <Panel title="Operator Projection - full operator layer, click a node to inspect units">
          <SizeObserver>
            {(w, h) => (
              <ForceGraph
                width={w}
                height={h}
                onOperatorClick={(op) => onForceGraphSelect(op.name, 'operator', op.id)}
              />
            )}
          </SizeObserver>
        </Panel>

        <Panel title="Units operated by selected operator">
          <OperatorMap
            operatorName={selected?.name}
            operatorId={selected?.operatorId}
            operatorType={selected?.type}
          />
        </Panel>
      </div>

      <motion.div
        className="glass flex flex-col gap-3 p-5"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
      >
        <h2 className="text-sm font-semibold uppercase tracking-widest text-white/50">
          About this data
        </h2>
        <p className="text-xs leading-relaxed text-white/40">
          The Airbnb operator data shown here is derived from an Inside Airbnb snapshot taken in September 2025.
          Because Airbnb hosts can rename their profiles, transfer listings between accounts, or delist units at any time,
          the operator names and listing counts displayed may no longer match what is currently shown on Airbnb.
          For example, a host listed as "Daniel" in our data may now appear under a different name on the platform,
          or may have fewer listings than recorded at the time of the snapshot.
          Operators are linked by their unique Airbnb host ID rather than by name,
          so units belonging to the same host are correctly grouped even when names appear inconsistent.
          Data from other sources (data.gv.at, OpenStreetMap, Wikidata) may similarly reflect the state at the time of collection.
          The force graph is an operator-centric projection of the KG rather than a raw rendering of every accommodation-unit node at once,
          so the full unit layer is explored by clicking an operator.
        </p>
      </motion.div>
    </motion.div>
  )
}

function AnalyticsTab({ onNavigate }) {
  return (
    <motion.div {...fadeVariant} className="grid grid-cols-1 gap-5 lg:grid-cols-2 xl:grid-cols-3">
      <Panel title="Top 20 Operators by accommodation units" className="xl:col-span-2">
        <TopOperators onSelect={(op) => onNavigate(op.name, 'operator', op.id)} />
      </Panel>
      <Panel title="Chain-affiliated establishments">
        <ChainBar onSelect={(name) => onNavigate(name, 'chain')} />
      </Panel>
      <Panel title="Accommodation units by district">
        <DistrictBar />
      </Panel>
      <Panel title="Multi-listing vs single-property operators by district" className="xl:col-span-2">
        <CorporateBar />
      </Panel>
      <Panel title="Accommodation types">
        <TypePie />
      </Panel>
      <Panel title="Quality and validation signals">
        <QualitySummary />
      </Panel>
      <motion.div
        className="glass max-h-52 overflow-y-auto p-5 flex flex-col gap-3 xl:col-span-2"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
      >
        <h2 className="text-sm font-semibold uppercase tracking-widest text-white/50">
          About this data
        </h2>
        <p className="text-xs leading-relaxed text-white/40">
          The Airbnb operator data shown here is derived from an Inside Airbnb snapshot taken in September 2025.
          Because Airbnb hosts can rename their profiles, transfer listings between accounts, or delist units at any time,
          the operator names and listing counts displayed may no longer match what is currently shown on Airbnb.
          For example, a host listed as "Daniel" in our data may now appear under a different name on the platform,
          or may have fewer listings than recorded at the time of the snapshot.
          Operators are linked by their unique Airbnb host ID rather than by name,
          so units belonging to the same host are correctly grouped even when names appear inconsistent.
          Data from other sources (data.gv.at, OpenStreetMap, Wikidata) may similarly reflect the state at the time of collection.
          Listing-to-establishment links are now only asserted when proximity is backed by textual evidence;
          weaker nearby candidates are tracked in the data pipeline but intentionally excluded from the graph.
        </p>
      </motion.div>
    </motion.div>
  )
}

function MapTab() {
  return (
    <motion.div {...fadeVariant}>
      <Panel title="Vienna - all geolocated accommodation units - click to explore operator network">
        <PropertyMap />
      </Panel>
    </motion.div>
  )
}

export default function App() {
  const [tab, setTab] = useState('graph')
  const [selected, setSelected] = useState(null)

  function navigateToGraph(name, type, operatorId) {
    setSelected({ name, type, operatorId })
    setTab('graph')
  }

  return (
    <div className="min-h-screen flex flex-col gap-6 p-4 md:p-8">
      <header className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Vienna Accommodation Operator <span style={{ color: '#2dd4bf' }}>Knowledge Graph</span>
          </h1>
          <p className="mt-0.5 text-sm text-white/40">
            Public accommodation data - operator analysis - Neo4j
          </p>
        </div>
        <Nav active={tab} onChange={setTab} />
      </header>

      <main className="flex-1">
        <AnimatePresence mode="wait">
          {tab === 'graph' && (
            <GraphTab
              key="graph"
              selected={selected}
              onForceGraphSelect={(name, type, operatorId) => setSelected({ name, type, operatorId })}
            />
          )}
          {tab === 'analytics' && (
            <AnalyticsTab key="analytics" onNavigate={navigateToGraph} />
          )}
          {tab === 'map' && <MapTab key="map" />}
        </AnimatePresence>
      </main>

      <footer className="pb-2 text-center text-xs text-white/20">
        Knowledge Graph Dashboard - Vienna Accommodation Operator Analysis
      </footer>
    </div>
  )
}
