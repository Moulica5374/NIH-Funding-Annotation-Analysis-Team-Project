CREATE OR REPLACE TABLE `gaf-analysis.dataset.pmid_mapping` AS
SELECT 
  g.DB_Object_Symbol AS gene_symbol,
  g.DB_Object_Name AS gene_name,
  g.GO_ID,
  g.Aspect,
  g.DB_Reference,
  r.APPLICATION_ID,
  r.PROJECT_TITLE,
  r.PI_NAMEs,
  r.TOTAL_COST,
  r.FY,
  r.ORG_NAME,
  r.PMID,
  REGEXP_EXTRACT(g.DB_Reference, r'PMID:(\d+)') AS matched_pmid
FROM `genomics_data.goa_uniprot` g
INNER JOIN `gaf-analysis.dataset.nih_reports` r
  ON REGEXP_EXTRACT(g.DB_Reference, r'PMID:(\d+)') = r.PMID
WHERE g.DB_Reference LIKE 'PMID:%';
