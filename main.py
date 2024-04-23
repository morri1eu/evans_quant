# main.py
from src.entries.moving_average_crossover_entry import run_moving_average_strategy
from src.data_fetchers.eodhd.get_baseline import fetch_baseline_data
from src.data_fetchers.eodhd.update_eod_data import fetch_and_update_data
from dotenv import load_dotenv
import os

load_dotenv()
# Example usage
api_token = os.getenv("EOD_HD_API_KEY")
tickers_json_path = "../../../eodhd_us_tickers_list.json"
output_folder = "../../../data/baseline_data"

def main():
    print("Select a strategy to run:")
    print("1: Moving Average Crossover")
    # Add more strategies here

    choice = input("Enter the number of the strategy you want to run: ")

    if choice == '1':
        run_moving_average_strategy()
    # Add more elif conditions for other strategies

# if __name__ == "__main__":
#     main()

def start_baseline_fetch():
    try:
        fetch_baseline_data(api_token, tickers_json_path, output_folder)
        return True
    except Exception as e:
        print(f"An error occurred while fetching baseline data {e}")
        return None
    
def update_baseline_data():
    try:
        fetch_and_update_data(api_token, tickers_json_path, output_folder)
        return True
    except Exception as e:
        print(f"An error occurred while updating baseline data {e}")
        return None
    
