import os
import pandas as pd
import numpy as np

def process_csv_files(directory="output"):
    """
    Processes CSV files in the specified directory, splits them into training, validation,
    and test sets, and saves these sets to separate files.
    
    Parameters:
    directory (str): The directory containing the CSV files to process.
    """
    # Initialize lists to store data frames for each set
    training_frames = []
    validation_frames = []
    test_frames = []

    # Process each CSV file in the directory
    for filename in os.listdir(directory):
        if filename.endswith(".csv"):
            file_path = os.path.join(directory, filename)
            data = pd.read_csv(file_path, header=None, names=['Column1', 'Column2'])
            data_shuffled = data.sample(frac=1).reset_index(drop=True)
            total_rows = len(data_shuffled)
            training_end = int(0.90 * total_rows)
            validation_end = int(0.98 * total_rows)
            training = data_shuffled.iloc[:training_end]
            validation = data_shuffled.iloc[training_end:validation_end]
            test = data_shuffled.iloc[validation_end:]
            training_frames.append(training)
            validation_frames.append(validation)
            test_frames.append(test)

    # Concatenate all data frames for each set and save to CSV
    training_data = pd.concat(training_frames, ignore_index=True)
    validation_data = pd.concat(validation_frames, ignore_index=True)
    test_data = pd.concat(test_frames, ignore_index=True)

    training_data.to_csv("training.csv", index=False, header=False)
    validation_data.to_csv("validation.csv", index=False, header=False)
    test_data.to_csv("test.csv", index=False, header=False)

def find_soft_duplicates():
    """
    Finds and prints search terms that appear more than once across the training, validation,
    and test sets (soft duplicates).
    """
    training_data = pd.read_csv('training.csv', header=None, names=['tag', 'search_term'])
    validation_data = pd.read_csv('validation.csv', header=None, names=['tag', 'search_term'])
    test_data = pd.read_csv('test.csv', header=None, names=['tag', 'search_term'])

    data_frames = {
        'training.csv': training_data,
        'validation.csv': validation_data,
        'test.csv': test_data
    }

    # Combine all search terms and find duplicates
    all_queries = pd.concat([training_data['search_term'], validation_data['search_term'], test_data['search_term']])
    duplicated_queries = all_queries[all_queries.duplicated(keep=False)].unique()

    # Print the duplicate search terms and their locations
    for search_term in duplicated_queries:
        print(f"Duplicate search term found: {search_term}")
        for file_name, data_frame in data_frames.items():
            if search_term in data_frame['search_term'].values:
                lines = (data_frame.index[data_frame['search_term'] == search_term] + 1).tolist()
                print(f"\t\t|_Found in {file_name} on lines: {lines}")

def find_hard_duplicates():
    """
    Finds and prints rows that are exactly the same across the training, validation,
    and test sets (hard duplicates).
    """
    training = pd.read_csv("training.csv", header=None, names=['tag', 'search_term'])
    validation = pd.read_csv("validation.csv", header=None, names=['tag', 'search_term'])
    test = pd.read_csv("test.csv", header=None, names=['tag', 'search_term'])

    # Combine all data with an identifier
    training['File'] = 'training.csv'
    validation['File'] = 'validation.csv'
    test['File'] = 'test.csv'

    combined = pd.concat([training, validation, test], ignore_index=True)

    # Find duplicates
    duplicates = combined.duplicated(subset=['tag', 'search_term'], keep=False)
    dup_data = combined[duplicates]

    if not dup_data.empty:
        grouped = dup_data.groupby(['tag', 'search_term'])
        for name, group in grouped:
            print(f'Duplicate found for tag: {name[0]}, Search Term: "{name[1]}"')
            for index, row in group.iterrows():
                print(f'  Found in {row["File"]}, Line: {index + 1}')
    else:
        print("No hard duplicates found across files.")
