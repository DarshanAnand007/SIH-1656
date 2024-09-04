import folium
import pandas as pd
from datetime import datetime

def get_sample_data():
    """
    Returns a DataFrame containing sample beach data.
    """
    data = {
        'Beach Name': ['Marina Beach', 'Juhu Beach', 'Kovalam Beach', 'Baga Beach', 'Radhanagar Beach'],
        'Latitude': [13.0475, 19.0968, 8.4006, 15.5569, 11.9796],
        'Longitude': [80.2820, 72.8265, 76.9781, 73.7437, 92.9876],
        'Wave Height (m)': [1.5, 2.3, 0.8, 2.0, 1.2]
    }
    df = pd.DataFrame(data)
    return df

def assess_suitability(df, threshold=2.0):
    """
    Adds a 'Suitability' column to the DataFrame based on wave height threshold.
    """
    df['Suitability'] = df['Wave Height (m)'].apply(lambda x: 'Suitable' if x <= threshold else 'Not Suitable')
    return df

def print_results(df):
    """
    Prints the beach data along with current date and time.
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\nBeach Suitability Report - {current_time}\n")
    print(df.to_string(index=False))
    print("\n")

def generate_map(df, output_file='beach_suitability_map.html'):
    """
    Generates an interactive map with beach markers indicating suitability.
    """
    # Create a map centered around India
    india_coords = [20.5937, 78.9629]
    beach_map = folium.Map(location=india_coords, zoom_start=5)

    # Define color mapping for suitability
    color_map = {'Suitable': 'green', 'Not Suitable': 'red'}

    # Add markers to the map
    for _, row in df.iterrows():
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=folium.Popup(f"<b>{row['Beach Name']}</b><br>Wave Height: {row['Wave Height (m)']} m<br>Suitability: {row['Suitability']}", max_width=200),
            icon=folium.Icon(color=color_map[row['Suitability']])
        ).add_to(beach_map)

    # Save the map to an HTML file
    beach_map.save(output_file)
    print(f"Interactive map has been saved to '{output_file}'\n")

def main():
    # Get sample data
    df = get_sample_data()

    # Assess suitability
    df = assess_suitability(df)

    # Print results
    print_results(df)

    # Generate and save map
    generate_map(df)

if __name__ == "__main__":
    main()
