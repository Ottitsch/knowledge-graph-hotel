// ============================================================
// Vienna Accommodation Operator Knowledge Graph — Cypher Queries
// Main question: Which accommodation units in Vienna are operated
// by the same person or organization, and what other units do they operate?
//
// Run in Neo4j Browser at http://localhost:7474
// ============================================================


// --- OVERVIEW ---

// Count nodes by label
MATCH (n) RETURN labels(n) AS label, count(n) AS count ORDER BY count DESC;

// Count relationships by type
MATCH ()-[r]->() RETURN type(r) AS rel_type, count(r) AS count ORDER BY count DESC;

// Listing-level vs establishment-level counts
MATCH (u:AccommodationUnit)
RETURN u.granularity AS granularity, count(u) AS count
ORDER BY count DESC;

// Source coverage
MATCH (u:AccommodationUnit)-[:OBSERVED_IN]->(s:Source)
RETURN s.name AS source, count(u) AS units
ORDER BY units DESC;


// --- CORE OPERATOR QUESTIONS ---

// Top 20 operators by number of accommodation units
MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator)
RETURN o.name AS operator, count(u) AS unit_count
ORDER BY unit_count DESC
LIMIT 20;

// All units operated by a specific operator (replace name as needed)
MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator {name: 'Example Host'})
RETURN u.name AS unit, u.address AS address, u.granularity AS granularity,
       u.district AS district, u.unit_type AS type;

// Professional operator candidates: operators with more than 3 units
MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator)
WITH o, count(u) AS cnt
WHERE cnt > 3
RETURN o.name AS operator, cnt AS unit_count
ORDER BY unit_count DESC;

// Operators with more than 10 units (large-scale operators)
MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator)
WITH o, count(u) AS cnt
WHERE cnt > 10
RETURN o.name AS operator, cnt AS unit_count
ORDER BY unit_count DESC;

// Show all units for a top-5 operator (graph view — use in Neo4j Browser)
MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator)
WITH o, count(u) AS cnt ORDER BY cnt DESC LIMIT 5
MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o)
RETURN u, o LIMIT 100;


// --- DISTRICT ANALYSIS ---

// Units per district
MATCH (u:AccommodationUnit)-[:LOCATED_IN]->(d:District)
RETURN d.name AS district, count(u) AS units
ORDER BY units DESC;

// Professional vs smaller operators per district
MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator)
MATCH (u)-[:LOCATED_IN]->(d:District)
WITH d, o, count(u) AS unit_count
WITH d,
     sum(CASE WHEN unit_count > 3 THEN unit_count ELSE 0 END) AS professional_units,
     sum(CASE WHEN unit_count <= 3 THEN unit_count ELSE 0 END) AS smaller_units
RETURN d.name AS district, professional_units, smaller_units
ORDER BY (professional_units + smaller_units) DESC;

// Chain-affiliated establishments by district
MATCH (u:AccommodationUnit)-[:LOCATED_IN]->(d:District),
      (u)-[:OPERATED_BY]->(o:Operator)-[:AFFILIATED_WITH]->(c:HotelChain)
RETURN d.name AS district, c.name AS chain, count(u) AS units
ORDER BY district, units DESC;

// Operator network in a specific district (graph view)
MATCH path = (d:District {name: 'Innere Stadt'})<-[:LOCATED_IN]-(u:AccommodationUnit)
             -[:OPERATED_BY]->(o:Operator)
OPTIONAL MATCH (o)-[:AFFILIATED_WITH]->(c:HotelChain)
RETURN path LIMIT 80;


// --- CHAIN ANALYSIS ---

// Hotel chains by number of affiliated units
MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator)-[:AFFILIATED_WITH]->(c:HotelChain)
RETURN c.name AS chain, count(u) AS units
ORDER BY units DESC;

// All units affiliated with a specific chain
MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator)-[:AFFILIATED_WITH]->(c:HotelChain {name: 'Marriott International'})
RETURN u.name AS unit, u.address AS address, o.name AS operator;


// --- SOURCE PROVENANCE ---

// Units observed by more than one source (cross-validated records)
MATCH (u:AccommodationUnit)-[:OBSERVED_IN]->(s:Source)
WITH u, count(s) AS source_count
WHERE source_count > 1
RETURN u.name AS unit, source_count, u.merge_confidence AS confidence
ORDER BY source_count DESC
LIMIT 50;

// Source overlap: how many units appear in both OSM and Wikidata?
MATCH (u:AccommodationUnit)-[:OBSERVED_IN]->(s1:Source {name: 'OpenStreetMap'}),
      (u)-[:OBSERVED_IN]->(s2:Source {name: 'Wikidata'})
RETURN count(u) AS osm_and_wikidata_units;

// Source overlap: OSM and data.gv.at
MATCH (u:AccommodationUnit)-[:OBSERVED_IN]->(s1:Source {name: 'OpenStreetMap'}),
      (u)-[:OBSERVED_IN]->(s2:Source {name: 'data.gv.at'})
RETURN count(u) AS osm_and_datagv_units;

// Full source overlap summary
MATCH (u:AccommodationUnit)-[:OBSERVED_IN]->(s:Source)
WITH u, collect(s.name) AS sources
RETURN apoc.text.join(apoc.coll.sort(sources), '+') AS source_combination,
       count(u) AS units
ORDER BY units DESC;


// --- GRANULARITY ---

// Establishments (OSM/Wikidata/data.gv.at) by district
MATCH (u:AccommodationUnit {granularity: 'establishment'})-[:LOCATED_IN]->(d:District)
RETURN d.name AS district, count(u) AS establishments
ORDER BY establishments DESC;

// Listings (Airbnb) by district
MATCH (u:AccommodationUnit {granularity: 'listing'})-[:LOCATED_IN]->(d:District)
RETURN d.name AS district, count(u) AS listings
ORDER BY listings DESC;


// --- GRAPH VISUALIZATION ---

// Operator → units → districts subgraph for a selected operator
MATCH (o:Operator {name: 'AccorHotels'})
OPTIONAL MATCH (o)-[:AFFILIATED_WITH]->(c:HotelChain)
MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o)
OPTIONAL MATCH (u)-[:LOCATED_IN]->(d:District)
RETURN o, c, u, d LIMIT 50;

// Full district context subgraph
MATCH path = (d:District)<-[:LOCATED_IN]-(u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator)
             -[:AFFILIATED_WITH]->(c:HotelChain)
WHERE d.name = 'Innere Stadt'
RETURN path LIMIT 80;
