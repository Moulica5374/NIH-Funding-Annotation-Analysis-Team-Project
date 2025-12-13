from google.cloud import bigquery
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_nih_projects():
    client = bigquery.Client(project='gaf-analysis')
    
    source_uri = "gs://gaf-data/Reports1/RePORTER_PRJ_C_FY*.csv"
    table_id = "gaf-analysis.nih_reports_us.projects"
    
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        allow_quoted_newlines=True
    )
    
    logger.info(f"Loading NIH projects from {source_uri}")
    
    load_job = client.load_table_from_uri(
        source_uri,
        table_id,
        job_config=job_config
    )
    
    logger.info(f"Job ID: {load_job.job_id}")
    load_job.result()
    
    table = client.get_table(table_id)
    logger.info(f" Loaded {table.num_rows:,} NIH projects")
    
    return load_job

def load_publication_links():
    client = bigquery.Client(project='gaf-analysis')
    
    source_uri = "gs://gaf-data/Reports1/REPORTER_PUBLNK_C_*.csv"
    table_id = "gaf-analysis.nih_reports_us.publication_links"
    
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
    )
    
    logger.info(f"Loading publication links from {source_uri}")
    
    load_job = client.load_table_from_uri(
        source_uri,
        table_id,
        job_config=job_config
    )
    
    logger.info(f"Job ID: {load_job.job_id}")
    load_job.result()
    
    table = client.get_table(table_id)
    logger.info(f" Loaded {table.num_rows:,} publication-project links")
    
    return load_job

def main():
    logger.info("=" * 60)
    logger.info("Starting NIH Reporter Data Load")
    logger.info("=" * 60)
    
    try:
        logger.info("\n[1/2] Loading NIH Projects...")
        load_nih_projects()
        
        logger.info("\n[2/2] Loading Publication Links...")
        load_publication_links()
        
        logger.info("\n" + "=" * 60)
        logger.info(" All NIH data loaded successfully!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"\n Error loading NIH data: {str(e)}")
        raise

if __name__ == "__main__":
    main()
