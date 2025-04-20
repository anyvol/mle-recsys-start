import pandas as pd
df = pd.read_parquet("final_recommendations_feat.parquet")
top_recs = df.sort_values("rank").drop_duplicates("item_id").head(1000)
top_recs[["item_id", "rank"]].to_parquet("top_recs.parquet")