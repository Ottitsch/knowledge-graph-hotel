// ============================================================
// Vienna Accommodation Operator Knowledge Graph - Cypher Queries
// Main question: Which accommodation units in Vienna are operated
// by the same person or organization, and what other units do they operate?
// ============================================================

// --- OVERVIEW ---

MATCH (n)
RETURN labels(n) AS label, count(n) AS count
ORDER BY count DESC;

MATCH ()-[r]->()
RETURN type(r) AS rel_type, count(r) AS count
ORDER BY count DESC;

MATCH (u:AccommodationUnit)
RETURN u.granularity AS granularity, count(u) AS count
ORDER BY count DESC;

MATCH (u:AccommodationUnit)-[:OBSERVED_IN]->(s:Source)
RETURN s.name AS source, count(u) AS units
ORDER BY units DESC;

// --- CORE OPERATOR QUESTIONS ---

MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator)
RETURN o.name AS operator, count(u) AS unit_count
ORDER BY unit_count DESC
LIMIT 20;

MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator {name: 'Example Host'})
RETURN u.name AS unit, u.address AS address, u.granularity AS granularity,
       u.district AS district, u.unit_type AS type,
       u.operator_identity_confidence AS operator_identity_confidence
ORDER BY unit;

MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator)
WITH o, count(u) AS cnt
WHERE cnt > 3
RETURN o.name AS operator, cnt AS unit_count
ORDER BY unit_count DESC;

// --- DISTRICT ANALYSIS ---

MATCH (u:AccommodationUnit)-[:LOCATED_IN]->(d:District)
RETURN d.name AS district, count(u) AS units
ORDER BY units DESC;

MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator)
MATCH (u)-[:LOCATED_IN]->(d:District)
WITH d, o, count(u) AS unit_count
WITH d,
     sum(CASE WHEN unit_count > 3 THEN unit_count ELSE 0 END) AS professional_units,
     sum(CASE WHEN unit_count <= 3 THEN unit_count ELSE 0 END) AS smaller_units
RETURN d.name AS district, professional_units, smaller_units
ORDER BY (professional_units + smaller_units) DESC;

MATCH (u:AccommodationUnit)-[:LOCATED_IN]->(d:District),
      (u)-[:OPERATED_BY]->(o:Operator)-[:AFFILIATED_WITH]->(c:HotelChain)
RETURN d.name AS district, c.name AS chain, count(u) AS units
ORDER BY district, units DESC;

// --- PROVENANCE AND QUALITY ---

MATCH (u:AccommodationUnit)
RETURN u.operator_identity_confidence AS operator_identity_confidence, count(u) AS units
ORDER BY units DESC;

MATCH (u:AccommodationUnit {granularity: 'establishment'})
RETURN u.merge_confidence AS merge_confidence, count(u) AS units
ORDER BY units DESC;

MATCH (l:AccommodationUnit {granularity: 'listing'})
OPTIONAL MATCH (l)-[r:LISTING_OF]->(e:AccommodationUnit)
RETURN coalesce(r.confidence, 'unlinked') AS listing_match_confidence, count(l) AS listings
ORDER BY listings DESC;

MATCH (l:AccommodationUnit)-[r:LISTING_OF]->(e:AccommodationUnit)
RETURN l.name AS listing, e.name AS establishment,
       r.confidence AS confidence, r.evidence AS evidence
ORDER BY confidence DESC, listing
LIMIT 50;

MATCH (u:AccommodationUnit)-[:OBSERVED_IN]->(s:Source)
WITH u, count(s) AS source_count
WHERE source_count > 1
RETURN u.name AS unit, source_count, u.merge_confidence AS confidence
ORDER BY source_count DESC
LIMIT 50;

MATCH (u:AccommodationUnit)-[:OBSERVED_IN]->(s:Source)
WITH u, s
ORDER BY s.name
WITH u, collect(s.name) AS sources
RETURN reduce(label = '', source IN sources |
              label + CASE WHEN label = '' THEN '' ELSE '+' END + source) AS source_combination,
       count(u) AS units
ORDER BY units DESC;

// --- CHAIN ANALYSIS ---

MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator)-[:AFFILIATED_WITH]->(c:HotelChain)
RETURN c.name AS chain, count(u) AS units
ORDER BY units DESC;

MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o:Operator)-[:AFFILIATED_WITH]->(c:HotelChain {name: 'Marriott International'})
RETURN u.name AS unit, u.address AS address, o.name AS operator
ORDER BY unit;

// --- GRAPH VIEWS ---

MATCH path = (d:District {name: 'Innere Stadt'})<-[:LOCATED_IN]-(u:AccommodationUnit)
             -[:OPERATED_BY]->(o:Operator)
OPTIONAL MATCH (o)-[:AFFILIATED_WITH]->(c:HotelChain)
RETURN path
LIMIT 80;

MATCH (o:Operator {name: 'AccorHotels'})
OPTIONAL MATCH (o)-[:AFFILIATED_WITH]->(c:HotelChain)
MATCH (u:AccommodationUnit)-[:OPERATED_BY]->(o)
OPTIONAL MATCH (u)-[:LOCATED_IN]->(d:District)
RETURN o, c, u, d
LIMIT 50;
