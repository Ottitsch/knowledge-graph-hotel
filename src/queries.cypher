// ============================================================
// Vienna Hotel Ownership Knowledge Graph — Cypher Query Examples
// Run in Neo4j Browser at http://localhost:7474
// ============================================================


// --- BASIC OVERVIEW ---

// Count nodes by label
MATCH (n) RETURN labels(n) AS label, count(n) AS count ORDER BY count DESC;

// Count relationships by type
MATCH ()-[r]->() RETURN type(r) AS rel_type, count(r) AS count ORDER BY count DESC;


// --- PROPERTY & OPERATOR QUERIES ---

// Show 50 properties with their operators
MATCH (p:Property)-[:OPERATED_BY]->(o:Operator)
RETURN p.name AS property, p.property_type AS type, o.name AS operator
LIMIT 50;

// Top 20 operators by number of properties managed
MATCH (p:Property)-[:OPERATED_BY]->(o:Operator)
RETURN o.name AS operator, count(p) AS property_count
ORDER BY property_count DESC
LIMIT 20;

// Operators managing more than 5 properties (likely professional/corporate hosts)
MATCH (p:Property)-[:OPERATED_BY]->(o:Operator)
WITH o, count(p) AS cnt
WHERE cnt > 5
RETURN o.name AS operator, cnt AS properties
ORDER BY cnt DESC;


// --- CHAIN / OWNERSHIP QUERIES ---

// Which hotel chains have the most properties in Vienna?
MATCH (p:Property)-[:OPERATED_BY]->(o:Operator)-[:SUBSIDIARY_OF]->(c:HotelChain)
RETURN c.name AS chain, count(p) AS properties
ORDER BY properties DESC;

// Full ownership chain: property → operator → chain → owner
MATCH (p:Property)-[:OPERATED_BY]->(o:Operator)-[:SUBSIDIARY_OF]->(c:HotelChain)
OPTIONAL MATCH (owner:OwnerCompany)-[:OWNS]->(c)
RETURN p.name AS property, o.name AS operator, c.name AS chain,
       coalesce(owner.name, 'unknown') AS owner_company
ORDER BY chain, property
LIMIT 100;

// Hotels owned by a specific chain (change 'Marriott International' as needed)
MATCH (p:Property)-[:OPERATED_BY]->(o:Operator)-[:SUBSIDIARY_OF]->(c:HotelChain {name: 'Marriott International'})
RETURN p.name AS hotel, p.address AS address;

// AccorHotels properties
MATCH (p:Property)-[:OPERATED_BY]->(o:Operator)-[:SUBSIDIARY_OF]->(c:HotelChain)
WHERE c.name CONTAINS 'Accor'
RETURN p.name, o.name, c.name;


// --- DISTRICT ANALYSIS ---

// How many properties per district?
MATCH (p:Property)-[:LOCATED_IN]->(d:District)
RETURN d.name AS district, count(p) AS properties
ORDER BY properties DESC;

// Corporate vs individual operators per district
// (corporate = operator with > 3 properties)
MATCH (p:Property)-[:OPERATED_BY]->(o:Operator)-[:LOCATED_IN]->(d:District)
WITH d, o, count(p) AS listings
RETURN d.name AS district,
       sum(CASE WHEN listings > 3 THEN listings ELSE 0 END) AS corporate_listings,
       sum(CASE WHEN listings <= 3 THEN listings ELSE 0 END) AS individual_listings
ORDER BY district;

// District breakdown of hotel chains
MATCH (p:Property)-[:LOCATED_IN]->(d:District),
      (p)-[:OPERATED_BY]->(o:Operator)-[:SUBSIDIARY_OF]->(c:HotelChain)
RETURN d.name AS district, c.name AS chain, count(p) AS count
ORDER BY district, count DESC;


// --- PLATFORM ANALYSIS ---

// Properties per platform
MATCH (p:Property)-[:LISTED_ON]->(pl:Platform)
RETURN pl.name AS platform, count(p) AS listings;

// Operators present on both booking.com and Airbnb (cross-listers)
MATCH (o:Operator)<-[:OPERATED_BY]-(p1:Property)-[:LISTED_ON]->(pl1:Platform {name: 'booking.com'}),
      (o)<-[:OPERATED_BY]-(p2:Property)-[:LISTED_ON]->(pl2:Platform {name: 'Airbnb'})
WHERE p1 <> p2
RETURN o.name AS operator, count(DISTINCT p1) AS booking_listings,
       count(DISTINCT p2) AS airbnb_listings;


// --- FIRMENBUCH / LEGAL ENTITY QUERIES ---

// Operators with verified Firmenbuch registration
MATCH (o:Operator)-[:REGISTERED_AS]->(fn:OwnerCompany)
RETURN o.name AS operator, fn.name AS legal_name,
       fn.firmenbuch_number AS fn_number, fn.legal_form AS form
ORDER BY operator;

// Corporate ownership chain with Firmenbuch verification
MATCH (oc:OwnerCompany)-[:OWNS]->(o:Operator)<-[:OPERATED_BY]-(p:Property)
RETURN oc.name AS owner, o.name AS operator, p.name AS property
ORDER BY owner, operator
LIMIT 50;


// --- GRAPH VISUALIZATION QUERIES (use in Neo4j Browser) ---

// Visualize top 5 operators and their properties (limit for readability)
MATCH (p:Property)-[:OPERATED_BY]->(o:Operator)
WITH o, count(p) AS cnt ORDER BY cnt DESC LIMIT 5
MATCH (p:Property)-[:OPERATED_BY]->(o)
RETURN p, o LIMIT 100;

// Visualize full ownership graph for one chain
MATCH path = (p:Property)-[:OPERATED_BY]->(o:Operator)-[:SUBSIDIARY_OF]->(c:HotelChain {name: 'AccorHotels'})
RETURN path LIMIT 50;

// Subgraph: district → properties → operators → chains
MATCH path = (d:District)<-[:LOCATED_IN]-(p:Property)-[:OPERATED_BY]->(o:Operator)-[:SUBSIDIARY_OF]->(c:HotelChain)
WHERE d.name = 'Innere Stadt'
RETURN path LIMIT 80;
