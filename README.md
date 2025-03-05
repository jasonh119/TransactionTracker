# Transaction Tracker

## Overview
This project is a Python application for refreshing my engineering and coding skills and while doing a machine learning course.  I was looking for something chunkier to play with so built my own dataset from transaction history that is quite dirty and poorly formatted and from many different financial institutions and countries. 

I then got carried away and connected it to gemini with a view to exploring using it with this dataset and others in future programmatically. 

First example is classifying expenses from transactions.  Supports SC Accounts and SC Card .csvs currently

To run this, you need 
a) a gemini API - free will do and 
b) update environment variable file with your `GEMINI_API_KEY` and 
c) update parameters in config.yaml file - model: gemini-2.0-flash will do for now - Pro model in testing, local model under development
d) SC account or credit card Dataset in the input directory - other banks csv's under development

Necessity is the mother of invention.

## Features
- Process transaction data from various financial institutions
- Combine transactions into a single dataset
- **NEW: AI-powered transaction categorization** using Google's Gemini API
  - Automatically categorizes transactions into main categories and sub-categories
  - Special handling for PayNow transactions and transfers to individuals
  - Customizable category definitions in config.yaml

## Installation
To install the required dependencies, run the following command:
You will need Gemini free tier access to use the gemini API - save your key to environment variable `GEMINI_API_KEY`
```
pip install -r requirements.txt
```

## Usage
To run the application, execute the following command:

```
python src/main.py
```

The application will:
1. Process all transaction files in the input directory
2. Combine them into a single dataset
3. Offer to categorize the transactions using Gemini AI
4. Offer to start an interactive chat with Gemini AI

### Transaction Categorization
The transaction categorization feature uses Google's Gemini AI to automatically categorize your transactions based on the categories defined in `config.yaml`. You can customize these categories to match your specific needs.

To use this feature:
1. Ensure your Gemini API key is set in the environment variable `GEMINI_API_KEY`
2. Run the application and select 'y' when prompted to categorize transactions
3. The categorized transactions will be saved to the output directory as both CSV and Excel files

## Configuration
You can customize the expense categories, PayNow vendors, and external individuals in the `config.yaml` file:

```yaml
# Expense categories with sub-categories
expense_categories:
  Food:
    - Groceries
    - Restaurants
    - Delivery
    - Cafes
  # Add more categories as needed

# PayNow vendor mappings
paynow_vendors:
  - vendor: "PAYNOW-VENDORNAME"
    category: "Category"
    subcategory: "Sub-Category"
  # Add more vendors as needed

# External individuals for transfers
external_individuals:
  - name: "PERSON NAME"
    category: "Transfers"
    subcategory: "Friends"
  # Add more individuals as needed
```

## Running Tests
To run the unit tests, use the following command:


## TODOs and NOT IMPLEMENTED YET
(in no particular order)
- Unit testing
- Other Banks formats csv extracts
- Handling large csv's for categorisation - gemini truncates the response - so crashes 
- local model option for security - e.g. lama2, llama3 to
- other commercial models for more tokens output in particularly 
- Move external transfers and paynow mappings to secondary secrets file (.env or second yaml file) 

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License
