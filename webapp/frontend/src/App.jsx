import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Nav from './components/Nav'
import Panel from './components/Panel'
import { useApi } from './hooks/useApi'
import ForceGraph from './components/graph/ForceGraph'
import TopOperators from './components/charts/TopOperators'
import ChainBar from './components/charts/ChainBar'
import DistrictBar from './components/charts/DistrictBar'
import CorporateBar from './components/charts/CorporateBar'
import TypePie from './components/charts/TypePie'
import QualitySummary from './components/QualitySummary'
import PropertyMap from './components/map/PropertyMap'
import OperatorMap from './components/map/OperatorMap'
import EvidencePanel from './components/explain/EvidencePanel'
import ReasoningLab from './components/reasoning/ReasoningLab'
import EvolutionSummary from './components/evolution/EvolutionSummary'
import ChangeTable from './components/evolution/ChangeTable'
import SnapshotSelector from './components/evolution/SnapshotSelector'
import QueryAssistant from './components/assistant/QueryAssistant'
import FinancialKGComparison from './components/case-studies/FinancialKGComparison'

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

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
        <Panel title="Evidence for selected operator">
          <EvidencePanel operatorId={selected?.operatorId} />
        </Panel>
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
            Operators are linked by their unique Airbnb host ID rather than by name,
            so units belonging to the same host are correctly grouped even when names appear inconsistent.
            The force graph is an operator-centric projection of the KG rather than a raw rendering of every accommodation-unit node at once,
            so the full unit layer is explored by clicking an operator.
          </p>
        </motion.div>
      </div>
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
      <Panel title="About this data" className="h-full">
        <div className="h-full overflow-y-auto pr-1">
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
        </div>
      </Panel>
      <Panel title="Financial KG comparison" className="xl:col-span-3">
        <FinancialKGComparison />
      </Panel>
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

function ReasoningTab({ selected, inspectedLink, onInspectLink }) {
  return (
    <motion.div {...fadeVariant} className="grid grid-cols-1 gap-5 xl:grid-cols-2">
      <Panel title="Reasoning lab - rules, embeddings, candidate links" className="xl:col-span-2">
        <ReasoningLab
          selectedOperatorId={selected?.operatorId}
          selectedOperatorName={selected?.name}
          onInspectLink={(row) =>
            onInspectLink({
              listingId: row.canonical_id,
              establishmentId: row.candidate_establishment_id,
            })
          }
        />
      </Panel>
      <Panel title="Evidence for selected operator">
        <EvidencePanel operatorId={selected?.operatorId} />
      </Panel>
      <Panel title="Link evidence for inspected candidate">
        <EvidencePanel link={inspectedLink} />
      </Panel>
    </motion.div>
  )
}

function EvolutionTab() {
  const { data: snapshotData, error: snapshotError, isLoading: snapshotLoading } = useApi('/api/evolution/snapshots')
  const snapshots = snapshotData?.snapshots || []
  const [previousSnapshot, setPreviousSnapshot] = useState('')
  const [currentSnapshot, setCurrentSnapshot] = useState('')

  useEffect(() => {
    if (!snapshots.length) return
    const fallbackPrevious = snapshotData?.default_previous || snapshots[Math.max(snapshots.length - 2, 0)] || ''
    const fallbackCurrent = snapshotData?.default_current || snapshots[snapshots.length - 1] || ''
    setPreviousSnapshot((value) => (snapshots.includes(value) ? value : fallbackPrevious))
    setCurrentSnapshot((value) => (snapshots.includes(value) ? value : fallbackCurrent))
  }, [snapshotData, snapshots])

  function handlePreviousChange(nextValue) {
    setPreviousSnapshot(nextValue)
    const nextIndex = snapshots.indexOf(nextValue)
    const currentIndex = snapshots.indexOf(currentSnapshot)
    if (currentIndex <= nextIndex) {
      setCurrentSnapshot(snapshots[nextIndex + 1] || snapshots[snapshots.length - 1] || '')
    }
  }

  function handleCurrentChange(nextValue) {
    setCurrentSnapshot(nextValue)
    const nextIndex = snapshots.indexOf(nextValue)
    const previousIndex = snapshots.indexOf(previousSnapshot)
    if (previousIndex >= nextIndex) {
      setPreviousSnapshot(snapshots[nextIndex - 1] || snapshots[0] || '')
    }
  }

  return (
    <motion.div {...fadeVariant} className="flex flex-col gap-5">
      <Panel title="Choose snapshots to compare">
        <SnapshotSelector
          snapshots={snapshots}
          previousSnapshot={previousSnapshot}
          currentSnapshot={currentSnapshot}
          onPreviousChange={handlePreviousChange}
          onCurrentChange={handleCurrentChange}
          isLoading={snapshotLoading}
          error={snapshotError}
        />
      </Panel>
      <Panel title="Snapshot evolution summary">
        <EvolutionSummary
          previousSnapshot={previousSnapshot}
          currentSnapshot={currentSnapshot}
        />
      </Panel>
      <Panel title="Selected snapshot changes">
        <ChangeTable
          previousSnapshot={previousSnapshot}
          currentSnapshot={currentSnapshot}
        />
      </Panel>
    </motion.div>
  )
}

function AssistantTab() {
  return (
    <motion.div {...fadeVariant}>
      <Panel title="Natural language query interface to the knowledge graph">
        <QueryAssistant />
      </Panel>
    </motion.div>
  )
}

export default function App() {
  const [tab, setTab] = useState('graph')
  const [selected, setSelected] = useState(null)
  const [inspectedLink, setInspectedLink] = useState(null)

  function navigateToGraph(name, type, operatorId) {
    setSelected({ name, type, operatorId })
    setTab('graph')
  }

  let activeTabView = null
  switch (tab) {
    case 'analytics':
      activeTabView = <AnalyticsTab key="analytics" onNavigate={navigateToGraph} />
      break
    case 'map':
      activeTabView = <MapTab key="map" />
      break
    case 'reasoning':
      activeTabView = (
        <ReasoningTab
          key="reasoning"
          selected={selected}
          inspectedLink={inspectedLink}
          onInspectLink={setInspectedLink}
        />
      )
      break
    case 'evolution':
      activeTabView = <EvolutionTab key="evolution" />
      break
    case 'assistant':
      activeTabView = <AssistantTab key="assistant" />
      break
    case 'graph':
    default:
      activeTabView = (
        <GraphTab
          key="graph"
          selected={selected}
          onForceGraphSelect={(name, type, operatorId) => setSelected({ name, type, operatorId })}
        />
      )
      break
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
        <AnimatePresence mode="wait">{activeTabView}</AnimatePresence>
      </main>

      <footer className="pb-2 text-center text-xs text-white/20">
        Knowledge Graph Dashboard - Vienna Accommodation Operator Analysis
      </footer>
    </div>
  )
}
