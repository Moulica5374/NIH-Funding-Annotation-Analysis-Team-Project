# NIH Funding Annotation Analysis



## Project Overview
This project analyzes NIH funding data by integrating Gene Ontology annotations from NCBI's Gene Annotation File (GAF) with NIH Reporter funding information. Our team was responsible for the data acquisition, processing, and cleaning pipeline, delivering structured datasets ready for downstream analysis.

### Data Engineering & Processing
- Download and process large-scale GAF file (377M+ records)
- Integrate NIH Reporter data
- Clean and structure data for analysis
- Deliver processed datasets for analysis.

### Data Sources
1. NIH Reporter Data

- Source: https://reporter.nih.gov/exporter

**Sources Used:**

- **Projects** - NIH-funded project details (2013-2022)
- **Publications** - Publications resulting from NIH projects
- **Link_Tables** - Maps PMID to PROJECT_NUMBER





* Key Fields:
-  ACTIVITY, CORE_PROJECT_NUM, TOTAL_COST, PMID
* Format: 
- CSV files


2. NCBI Gene Annotation File (GAF)

- Source: https://ftp.ebi.ac.uk/pub/databases/GO/goa/UNIPROT/goa_uniprot_gcrp.gaf.gz
- Format: GAF 2.2 (tab-delimited)
- Compressed Size: ~4.5 GB
- Uncompressed Size: ~74 GB
- Total Records: 377,449,350 annotations

**Key Fields**:

* DB_Object_ID (protein identifier)
* GO_ID (Gene Ontology term)
* Taxon_ID (organism/species)
* PMID (PubMed publication ID)
* Evidence_Code (annotation evidence type)



## Technology Stack

### Data Storage & Processing

* **Google Cloud Storage (GCS)**: Raw data file storage
* **Google BigQuery**: Data warehouse for large-scale processing and analysis
* **BigQuery Load Jobs**: Direct data ingestion from GCS to BigQuery tables
* **Python 3.8+**: Data collection, transformation, and cleaning

## Key Libraries
- google-cloud-bigquery
- google-cloud-storage

### Architecture Overview

![DataSet Collection and PreProcessing](Architecture-1.png)

```
Raw Data Sources
    ├── NIH Reporter (CSV) ──────┐
    │                             ├──> Download & Upload to GCS
    └── NCBI GAF (70GB) ─────────┘
              │
              v
    Google Cloud Storage (Raw Data Buckets)
              │
              v
    BigQuery Load Jobs (Parallel Import)
              │
              ├──> Parse GAF format
              ├──> Schema auto-detection
              ├──> Load in parallel
              └──> Create partitioned tables
              │
              v
    Google BigQuery (Structured Tables)
              │
              ├──> Table: gaf_annotations
              ├──> Table: nih_projects  
              ├──> Table: nih_publications
              └──> Table: nih_project_publications
              │
              v
    Cleaned & Joined Datasets
              │
              v
    Analysis Team (Statistical Analysis & Visualization)
```



### Prerequisites

* Python 3.8+
* Google Cloud Platform account with:
  - BigQuery API enabled
  - Cloud Storage API enabled
* gcloud CLI installed and configured
### Setup Instructions

- Python 3.8+
Google Cloud Platform account with:

- BigQuery API enabled
- Cloud Storage API enabled


- gcloud CLI installed and configured

### Configure Google Cloud 

### Authenticate
```
gcloud auth login
```

### Set your project
```
gcloud config set project gaf-analysis
```

### Create GCS bucket for data storage
```
gsutil mb gs://nih-gaf-data-bucket
```

### Create BigQuery dataset
```
bq mk --dataset analysis:nih_funding_analysis
```

### Data Processing Steps

#### Step 1: Upload NIH Reporter Data to GCS
What we did: Uploaded pre-downloaded NIH Reporter CSV files to Cloud Storage bucket

NIH Reporter data files (FY 2017-2022) were uploaded to ***gs://gaf-data/Reports1/:***

#### Upload NIH Reporter CSV files to bucket
```

gsutil -m cp RePORTER_PRJ_C_FY*.csv gs://gaf-data/Reports1/
gsutil -m cp REPORTER_PUBLNK_C_*.csv gs://gaf-data/Reports1/
```

Files uploaded to gs://gaf-data/Reports1/:

- RePORTER_PRJ_C_FY2017.csv through FY2022.csv (~2.5M projects)
- REPORTER_PUBLNK_C_2017.csv through 2022.csv (~3.2M publication links)
Total size: ~2.8 GB

#### Step 2: Upload and Prepare GAF File

What we did: Uploaded pre-downloaded GAF file and prepared it for processing.

The GAF file was already downloaded and uncompressed locally, then uploaded to GCS:

#### Upload the uncompressed GAF file
```

gsutil cp goa_uniprot_gcrp.gaf gs://gaf-data/

```
Result: Uncompressed GAF file ready at gs://gaf-data/goa_uniprot_gcrp.gaf (~70 GB)

#### Step 3: Load GAF File to BigQuery using Dataproc/Spark (Job)
What we did: Used a Dataproc Spark job to read the uncompressed GAF file and load it to BigQuery

Why Spark? The 70GB uncompressed file is too large for direct BigQuery load jobs, so we used Spark for distributed processing.

Script: load_gaf.py (PySpark job submitted to Dataproc cluster)

```
from pyspark.sql import SparkSession

# Initialize Spark session
spark = SparkSession.builder \
    .appName("GAF to BigQuery") \
    .getOrCreate()

# Read UNCOMPRESSED GAF file (tab-delimited, no header)
df = spark.read \
    .option("delimiter", "\t") \
    .option("header", "false") \
    .csv("gs://gaf-data/goa_uniprot_gcrp.gaf")  # UNCOMPRESSED file

# Define GAF 2.2 column names
columns = ["DB", "DB_Object_ID", "DB_Object_Symbol", "Qualifier", "GO_ID", 
           "DB_Reference", "Evidence_Code", "With_From", "Aspect", 
           "DB_Object_Name", "DB_Object_Synonym", "DB_Object_Type", 
           "Taxon", "Date", "Assigned_By", "Annotation_Extension", 
           "Gene_Product_Form_ID"]

# Rename columns from _c0, _c1, etc.
for i, col in enumerate(columns):
    df = df.withColumnRenamed(f"_c{i}", col)

# Write directly to BigQuery
df.write \
    .format("bigquery") \
    .option("table", "gaf-analysis.genomics_data.goa_uniprot") \
    .option("temporaryGcsBucket", "dataproc-temp-us-central1-785677848009-os35jmlm") \
    .mode("overwrite") \
    .save()
```
#### How to run (on Dataproc):

#### Submit PySpark job to Dataproc cluster
```
gcloud dataproc jobs submit pyspark \
    gs://gaf-data/scripts/load_gaf.py \
    --cluster=gaf-analysis\
    --region=us-central1
```

**Result - Table Created:**

- Table: gaf-analysis.genomics_data.goa_uniprot
- Location: US (multi-region)
- Total Records: 377,110,983 gene annotations
- Size: 70.89 GB logical / 4.81 GB physical (compressed in BigQuery)

**Processing Details:**

- Spark reads file in parallel across multiple workers
- Processes 70GB of tab-delimited data
- Automatically handles schema and data types
- Uses temporary GCS bucket for staging before BigQuery load
- BigQuery compresses data upon storage (70GB → 4.8GB)

#### Step 4: Load NIH Reporter Data to BigQuery

What we did: Used Python script to load NIH Reporter CSV files from GCS to BigQuery.

NIH data files were uploaded to gs://gaf-data/Reports1/ and loaded using load_nih_reports.py script.

Script: gs://gaf-data/scripts/load_nih_reports.py

#### Script loaded CSV files from GCS to BigQuery

```

from google.cloud import bigquery

client = bigquery.Client()


job_config = bigquery.LoadJobConfig(
    source_format=bigquery.SourceFormat.CSV,
    skip_leading_rows=1,
    autodetect=True
)




load_job = client.load_table_from_uri(
    'gs://gaf-data/Reports1/RePORTER_PRJ_C_FY*.csv',
    'gaf-analysis.nih_reports_us.projects',
    job_config=job_config
)

load_job.result()
```

Tables Created in nih_reports_us dataset (US multi-region):

**Table 1:** projects - NIH Funded Projects (FY 2017-2022)

Key fields:

- CORE_PROJECT_NUM, PROJECT_TITLE, PI_NAMEs
- TOTAL_COST, DIRECT_COST_AMT, INDIRECT_COST_AMT
- FY (fiscal year), ACTIVITY (grant type)
- ORG_NAME, ORG_CITY, ORG_STATE
- PROJECT_START, PROJECT_END

**Table 2:** publication_links - Project-Publication Mapping

### Load publication links
```
load_job = client.load_table_from_uri(
    'gs://gaf-data/Reports1/REPORTER_PUBLNK_C_*.csv',
    'gaf-analysis.nih_reports_us.publication_links',
    job_config=job_config
)
```
Fields:

- PMID (PubMed ID)
- PROJECT_NUMBER (links to projects table)

### Step 5: Link GAF with NIH Data

What we did: Used SQL to extract PMIDs from GAF and join with NIH Reporter data

SQL Query: link_gaf_nih.sql

```
CREATE OR REPLACE TABLE `gaf-analysis.dataset.pmid_mapping` AS
SELECT 
  -- GAF gene annotation fields
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
```
This query:

- Filters GAF to only records with PMID references
- Extracts numeric PMID from "PMID:12345678" format using REGEXP_EXTRACT
- Joins with NIH reports table on the PMID
- Creates comprehensive mapping table linking genes to NIH funding

**Result:** pmid_mapping table with gene annotations + NIH project details

### Step 6: Create Final Integrated Dataset

**Final Query:** Join GAF annotations with NIH funding data using PMIDs as the link

```
CREATE OR REPLACE TABLE `gaf-analysis.nih_reports_us.nih_funded_gene_annotations` AS
SELECT 
  g.*,  -- All GAF annotation fields
  REGEXP_EXTRACT(g.DB_Reference, r'PMID:(\d+)') as pmid_extracted,
  pp.*  -- All NIH project fields
FROM `genomics_data.goa_uniprot` g
INNER JOIN `nih_reports_us.pmid_projects` pp
  ON REGEXP_EXTRACT(g.DB_Reference, r'PMID:(\d+)') = CAST(pp.PMID AS STRING)
WHERE g.DB_Reference LIKE 'PMID:%';
```
What this does:

- Filters GAF to only records with PMID references (1.14M out of 377M records)
- Extracts PMID from "PMID:12345678" format
- Joins with NIH projects via the PMID
- Creates comprehensive table with both gene annotations AND funding information


### Step 7: Data Cleaning - Remove Nulls and Duplicates

What we did: Cleaned the integrated dataset by removing null values and duplicate records

Query:

```
-- Create cleaned version of the dataset
CREATE OR REPLACE TABLE `gaf-analysis.dataset.pmid_mapping_clean` AS
SELECT DISTINCT
  gene_symbol,
  gene_name,
  GO_ID,
  Aspect,
  DB_Reference,
  APPLICATION_ID,
  PROJECT_TITLE,
  PI_NAMEs,
  TOTAL_COST,
  FY,
  ORG_NAME,
  PMID,
  matched_pmid
FROM `gaf-analysis.dataset.pmid_mapping`


WHERE 
  gene_symbol IS NOT NULL
  AND GO_ID IS NOT NULL
  AND PMID IS NOT NULL
  AND PROJECT_TITLE IS NOT NULL
  AND TOTAL_COST IS NOT NULL
  AND matched_pmid IS NOT NULL;
```
Result: Clean dataset ready for analysis team

### Step 8: Export for Analysis Team

Export to CSV for sharing with analysis :

```

EXPORT DATA OPTIONS(
  uri='gs://gaf-data/exports/final/gaf_nih_linked_*.csv',
  format='CSV',
  overwrite=true,
  header=true,
  field_delimiter=','
) AS
SELECT * FROM `nih_reports_us.nih_funded_gene_annotations`;
```
Output files in gs://gaf-data/exports/final/:

- gaf_nih_linked_000000000000.csv 
- gaf_nih_linked_000000000001.csv 










## Research Questions

### Required Questions
1. **RQ1**: How much NIH money is spent on different model organisms? Is there a bias?
2. **RQ2**: How much NIH money is spent on different proteins? Is there a bias?

### Team-Proposed Questions
3. **RQ3**: [Your additional research question]
4. **RQ4**: [Your additional research question]

## Data Sources

### 1. NIH Reporter Data
- **Source**: https://reporter.nih.gov/exporter
- **Tables Used**:
  - `Projects` - NIH-funded project details (2013-2022)
  - `Publications` - Publications resulting from NIH projects
  - `Link_Tables` - Maps PMID to PROJECT_NUMBER
- **Key Fields**: ACTIVITY (R01 focus), CORE_PROJECT_NUM, TOTAL_COST

### 2. UniProt-GOA Annotations
- **Source**: https://ftp.ebi.ac.uk/pub/databases/GO/goa/UNIPROT/goa_uniprot_gcrp.gaf.gz
- **Size**: ~70GB
- **Fields**: DB_Object_ID (protein), GO_ID (function), Taxon_ID (species), PMID

## Technology Stack

### Data Storage
- **Google Cloud Storage**: Raw GAF file storage (70GB)
- **Google BigQuery**: Data warehouse for analysis
- **MongoDB**: [Optional - if using for some data]

### Processing
- **Apache Spark on Dataproc**: Large-scale GAF file processing
- **Python 3.x**: Data collection, preprocessing, analysis
- **Libraries**: pandas, matplotlib, seaborn, scipy, pymongo, google-cloud-bigquery

## Project Structure

```
nih-funding-analysis/
├── README.md
├── requirements.txt
├── data/
│   ├── raw/                    # Small sample files only (GAF in GCS)
│   └── processed/              # Intermediate processed data
├── scripts/
│   ├── 01_download_nih_data.py      # Download NIH Reporter data
│   ├── 02_gaf_to_parquet.py         # Convert GAF to Parquet (Spark)
│   ├── 03_load_to_bigquery.py       # Load data to BigQuery
│   └── 04_mongodb_import.py         # Import to MongoDB (if used)
├── analysis/
│   ├── rq1_organism_funding.py      # RQ1 analysis
│   ├── rq2_protein_funding.py       # RQ2 analysis
│   ├── rq3_custom_analysis.py       # Your RQ3
│   └── rq4_custom_analysis.py       # Your RQ4
├── visualization/
│   ├── plot_organisms.py
│   └── plot_proteins.py
├── statistical_tests/
│   └── bias_detection.py            # Statistical significance testing
├── results/
│   ├── figures/
│   └── statistics/
├── docs/
│   ├── data_cards.md               # Data documentation
│   ├── supplemental.pdf            # Processing details
│   └── midterm_presentation.pptx
└── notebooks/
    └── exploratory_analysis.ipynb
```

## Setup Instructions

### Prerequisites
- Python 3.8+
- Google Cloud Platform account with BigQuery enabled
- MongoDB installed (if using)
- gcloud CLI installed

### 1. Clone Repository
```bash
git clone https://github.com/your-username/nih-funding-analysis.git
cd nih-funding-analysis
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up Google Cloud
```bash
# Authenticate
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Create GCS bucket for GAF data
gsutil mb gs://gaf-data

# Create BigQuery dataset
bq mk --dataset YOUR_PROJECT_ID:nih_analysis
```

### 4. Download and Process Data

#### Step 4.1: Download NIH Reporter Data (2013-2022)
```bash
python scripts/01_download_nih_data.py --years 2013-2022 --output data/raw/
```
**Expected Output**: 
- `projects_2013_2022.csv`
- `publications_2013_2022.csv`
- `link_tables_2013_2022.csv`

**Runtime**: ~15-30 minutes

#### Step 4.2: Download GAF File
```bash
# Download GAF file to GCS (70GB)
wget https://ftp.ebi.ac.uk/pub/databases/GO/goa/UNIPROT/goa_uniprot_gcrp.gaf.gz
gunzip goa_uniprot_gcrp.gaf.gz
gsutil cp goa_uniprot_gcrp.gaf gs://gaf-data/raw/
```
**Runtime**: ~20-40 minutes

#### Step 4.3: Convert GAF to Parquet using Dataproc
```bash
# Upload processing script
gsutil cp scripts/02_gaf_to_parquet.py gs://gaf-data/scripts/

# Submit Spark job
gcloud dataproc batches submit pyspark \
  gs://gaf-data/scripts/02_gaf_to_parquet.py \
  --region=us-central1 \
  --batch=gaf-parquet-$(date +%s) \
  --properties=spark.executor.instances=4,spark.executor.cores=4,spark.executor.memory=8g
```
**Expected Output**: Parquet files in `gs://gaf-data/parquet/gaf.parquet/`  
**Runtime**: ~25-50 minutes  
**Rows Processed**: ~377 million

#### Step 4.4: Load Data to BigQuery
```bash
# Load NIH Projects
bq load --autodetect --replace \
  nih_analysis.nih_projects \
  gs://gaf-data/parquet/gaf.parquet/*

# Load Publications
bq load --autodetect --source_format=CSV \
  nih_analysis.nih_publications \
  data/raw/publications_2013_2022.csv

# Load Link Tables
bq load --autodetect --source_format=CSV \
  nih_analysis.nih_project_publications \
  data/raw/link_tables_2013_2022.csv
```
**Runtime**: ~5-15 minutes per table

## Running Analyses

### Research Question 1: Organism Funding Analysis
```bash
python analysis/rq1_organism_funding.py
```
**Expected Output**:
- `results/figures/organism_funding_distribution.png`
- `results/statistics/organism_bias_test.json`
- Console output with bias statistics

**Sample Output**:
```
Top 5 Organisms by Funding:
1. Homo sapiens: $15.2B (bias: +2.3σ, p<0.001)
2. Mus musculus: $8.7B (bias: +1.1σ, p=0.023)
...
```

### Research Question 2: Protein Funding Analysis
```bash
python analysis/rq2_protein_funding.py
```
**Expected Output**:
- `results/figures/protein_funding_distribution.png`
- `results/statistics/protein_bias_test.json`

### Research Question 3: [Your Question]
```bash
python analysis/rq3_custom_analysis.py
```
**Expected Output**: [Describe outputs]

### Research Question 4: [Your Question]
```bash
python analysis/rq4_custom_analysis.py
```
**Expected Output**: [Describe outputs]

## Results Summary

| Research Question | Key Finding | Statistical Test | p-value |
|-------------------|-------------|------------------|---------|
| RQ1: Organism Bias | [Finding] | Chi-square | p<0.001 |
| RQ2: Protein Bias | [Finding] | T-test | p=0.023 |
| RQ3: [Custom] | [Finding] | [Test] | [Value] |
| RQ4: [Custom] | [Finding] | [Test] | [Value] |

## Bias Detection Method

We detect funding bias using the formula:
```
bias(T, θ) = E(T) - θ
```

Where:
- **T**: Observed funding allocation statistic
- **θ**: Expected funding allocation under null hypothesis (uniform distribution)
- **E(T)**: Expected value of T

**Interpretation**: 
- Positive bias indicates over-funding
- Negative bias indicates under-funding
- Statistical significance tested using appropriate tests (Chi-square, t-test, ANOVA)

## Data Statistics

### NIH Projects Dataset
- **Time Period**: 2013-2022
- **Total Projects**: [X]
- **R01 Grants**: [Y]
- **Total Funding**: $[Z]B
- **Fields**: 45 columns

### GAF Annotations Dataset
- **Total Rows**: 377,449,350
- **Unique Proteins**: [X]
- **Unique Organisms**: [Y]
- **Unique PMIDs**: [Z]

### Merged Dataset
- **Projects with Publications**: [X]
- **Projects with Annotations**: [Y]
- **Coverage Rate**: [Z]%

## Visualization Examples

All visualizations are located in `results/figures/`:
- Organism funding distribution bar charts
- Protein funding heatmaps
- Temporal funding trends
- Bias detection plots with confidence intervals

## Database Schema

### BigQuery Tables

#### `nih_analysis.nih_projects`
```sql
- APPLICATION_ID (STRING)
- CORE_PROJECT_NUM (STRING)
- TOTAL_COST (INTEGER)
- PROJECT_START (DATE)
- PROJECT_END (DATE)
- [... 40 more fields]
```

#### `nih_analysis.nih_project_publications`
```sql
- PMID (STRING)
- PROJECT_NUMBER (STRING)
```

#### `nih_analysis.gaf_annotations`
```sql
- DB_Object_ID (STRING) -- Protein ID
- GO_ID (STRING) -- Function ID
- Taxon_ID (STRING) -- Species
- PMID (STRING)
- [... 12 more fields]
```

## Performance Considerations

- **GAF Processing**: Due to 70GB size, processed on GCP Dataproc (not local)
- **BigQuery Queries**: Optimized with partitioning on fiscal year
- **Memory Usage**: Most analyses run with <8GB RAM
- **Query Costs**: Estimated $0.50-$2.00 per full dataset scan

## Known Issues & Limitations

1. **GAF File Size**: Cannot process locally, requires cloud infrastructure
2. **PMID Matching**: ~[X]% of projects have no linked publications
3. **Data Coverage**: Some organisms/proteins may have limited annotations
4. **Time Period**: Analysis limited to 2013-2022 fiscal years

## Citation

```
NIH Reporter Data: National Institutes of Health. NIH RePORTER. 
https://reporter.nih.gov/

UniProt-GOA: The Gene Ontology Consortium. Gene Ontology Annotations (GOA).
https://www.ebi.ac.uk/GOA
```

## License
[Specify your license]

## Contact
- [Your Name]: [email]
- Project Repository: [GitHub URL]

---
**Last Updated**: October 28, 2025  
**Project Due Date**: [Insert due date]