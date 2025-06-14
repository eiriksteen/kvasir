import pandas as pd

# Load the dataset
file_path = 'data/DailyDelhiClimateTrain.csv'
df = pd.read_csv(file_path)
# df["city"] = "Delhi"

# df.to_csv("data/DailyDelhiClimateTrain.csv", index=False)
print(df.head())


# df['date'] = pd.to_datetime(df['date'])  # Convert date to datetime

# # Set the index to date for time series
# miya_data = df.set_index('date')

# # Create metadata (static features)
# miya_metadata = pd.DataFrame({
#     'city': ['Delhi'],
#     'country': ['India'], 
#     'source': ['Daily Weather Data']
# }, index=['Delhi'])

# # Set miya_mapping to None as there are no categorical features to map
# miya_mapping = None

# # Display the transformed data and metadata
# print(miya_data.head())
# print(miya_metadata)
# print()