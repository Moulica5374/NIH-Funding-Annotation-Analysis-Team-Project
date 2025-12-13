from pyspark.sql import SparkSession

def load_gaf_to_bigquery():
    spark = SparkSession.builder \
        .appName("GAF to BigQuery") \
        .getOrCreate()
    
    df = spark.read \
        .option("delimiter", "\t") \
        .option("header", "false") \
        .csv("gs://gaf-data/goa_uniprot_gcrp.gaf")
    
    columns = [
        "DB",
        "DB_Object_ID",
        "DB_Object_Symbol",
        "Qualifier",
        "GO_ID",
        "DB_Reference",
        "Evidence_Code",
        "With_From",
        "Aspect",
        "DB_Object_Name",
        "DB_Object_Synonym",
        "DB_Object_Type",
        "Taxon",
        "Date",
        "Assigned_By",
        "Annotation_Extension",
        "Gene_Product_Form_ID"
    ]
    
    for i, col in enumerate(columns):
        df = df.withColumnRenamed(f"_c{i}", col)
    
    df.write \
        .format("bigquery") \
        .option("table", "gaf-analysis.genomics_data.goa_uniprot") \
        .option("temporaryGcsBucket", "dataproc-temp-us-central1-785677848009-os35jmlm") \
        .mode("overwrite") \
        .save()
    
    spark.stop()

if __name__ == "__main__":
    load_gaf_to_bigquery()
