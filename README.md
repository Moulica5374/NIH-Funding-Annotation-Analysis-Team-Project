# NIH Funding Annotation Analysis



## Project Overview
This project analyzes NIH funding data by integrating Gene Ontology annotations from NCBI's Gene Annotation File (GAF) with NIH Reporter funding information. Our team was responsible for the data acquisition, processing, and cleaning pipeline, delivering structured datasets ready for downstream analysis.

### Data Engineering & Processing
- Download and process large-scale GAF file (377M+ records)
- Integrate NIH Reporter data
- Clean and structure data for analysis
- Deliver processed datasets to analysis team

### Data Sources
1. NIH Reporter Data

- Source: https://reporter.nih.gov/exporter
Tables Used:

-- Projects - NIH-funded project details (2013-2022)
-- Publications - Publications resulting from NIH projects
-- Link_Tables - Maps PMID to PROJECT_NUMBER


Key Fields: ACTIVITY, CORE_PROJECT_NUM, TOTAL_COST, PMID
Format: CSV files
Size: ~2-5 GB total

Key Fields: ACTIVITY, CORE_PROJECT_NUM, TOTAL_COST, PMID
Format: CSV files
Size: ~2-5 GB total

2. NCBI Gene Annotation File (GAF)

- Source: https://ftp.ebi.ac.uk/pub/databases/GO/goa/UNIPROT/goa_uniprot_gcrp.gaf.gz
- Format: GAF 2.2 (tab-delimited)
- Compressed Size: ~4.5 GB
- Uncompressed Size: ~70 GB
- Total Records: 377,449,350 annotations
Key Fields:

- DB_Object_ID (protein identifier)
- GO_ID (Gene Ontology term)
- Taxon_ID (organism/species)
- PMID (PubMed publication ID)
- Evidence_Code (annotation evidence type)



Technology Stack
Data Storage & Processing

Google Cloud Storage (GCS): Raw data file storage
Google BigQuery: Data warehouse for large-scale processing and analysis
BigQuery Load Jobs: Direct data ingestion from GCS to BigQuery tables
Python 3.8+: Data collection, transformation, and cleaning






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