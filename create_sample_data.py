import pandas as pd

# Create sample data with the original structure
data = {
    'Unnamed: 0': range(5),  # Adding back the index column
    'book_name': [
        'The Great Gatsby',
        '1984',
        'Pride and Prejudice',
        'The Hobbit',
        'To Kill a Mockingbird'
    ],
    'summaries': [
        'A story of decadence and excess, following Jay Gatsby and his pursuit of his lost love.',
        'A dystopian novel about totalitarian control and surveillance.',
        'A romantic novel about prejudice and hasty judgments in 19th century England.',
        'A fantasy adventure about a hobbit who joins a quest to reclaim a dwarf kingdom.',
        'A story about racial injustice and the loss of innocence in the American South.'
    ],
    'categories': [
        'Classic Fiction',
        'Science Fiction',
        'Romance',
        'Fantasy',
        'Literary Fiction'
    ]
}

# Create DataFrame
df = pd.DataFrame(data)

# Save to CSV with index=True to keep the 'Unnamed: 0' column
df.to_csv('books_summary.csv', index=True)

# Verify the file was created correctly
try:
    test_df = pd.read_csv('books_summary.csv')
    print("CSV file created successfully with columns:", test_df.columns.tolist())
    print(f"Number of books: {len(test_df)}")
except Exception as e:
    print("Error creating CSV file:", e) 