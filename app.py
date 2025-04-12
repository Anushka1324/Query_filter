from flask import Flask, request, jsonify, render_template
import spacy
import spacy.cli
spacy.cli.download("en_core_web_sm") 
from spacy.matcher import Matcher
import re
import os

app = Flask(__name__)
nlp = spacy.load("en_core_web_sm")

# Load locations from file
def load_locations(filepath='first_column.txt'):
    if not os.path.exists(filepath):
        return set()
    with open(filepath, 'r', encoding='utf-8') as file:
        return set(line.strip().lower() for line in file if line.strip())

KNOWN_LOCATIONS = load_locations()

# Gender keywords mapping
GENDER_KEYWORDS = {
    'male': ['boy', 'boys', 'male', 'guy', 'guys','men'],
    'female': ['girl', 'girls', 'female', 'lady', 'ladies','women'],
    'co-ed': ['co-ed', 'unisex', 'mixed', 'any']
}

# Additional filters like "wifi", "ac", etc.
FILTER_KEYWORDS = ['food', 'wifi', 'ac', 'attached bathroom', 'private room', 'furnished', 'laundry','refridgerator','geyzer']

# Reason keywords mapping (Hotel, PG, Room, House Rent)
REASON_KEYWORDS = {
    'hotel': ['hotel', 'guest house', 'hotel room', 'hotel stay'],
    'pg': ['pg', 'paying guest', 'girls pg', 'boys pg', 'co-ed pg'],
    'room': ['room', 'private room', 'rented room'],
    'house rent': ['house rent', 'flat', 'apartment', 'rented house']
}

matcher = Matcher(nlp.vocab)
price_patterns = [
    [{"LOWER": {"IN": ["under", "below", "less", "max"]}}, {"IS_DIGIT": True}],
    [{"IS_DIGIT": True}, {"LOWER": {"IN": ["k", "K"]}}],
    [{"TEXT": {"REGEX": r"\d+[kK]?"}}],
]
matcher.add("PRICE", price_patterns)

def extract_info(text):
    doc = nlp(text.lower())
    matches = matcher(doc)

    # Extract price
    price = None
    for _, start, end in matches:
        span = doc[start:end]
        price_text = span.text.replace('₹', '').replace(',', '').lower()
        match = re.match(r'(\d+)(k)?', price_text)
        if match:
            price = int(match.group(1)) * 1000 if match.group(2) else int(match.group(1))
            break

    # Extract location
    location = None
    for token in doc:
        if token.text.lower() in KNOWN_LOCATIONS:
            location = token.text.title()
            break
    
    # Extract gender
    gender = None
    for key, values in GENDER_KEYWORDS.items():
        if any(val in text.lower() for val in values):
            gender = key
            break
    
    # Extract filters
    filters = [keyword for keyword in FILTER_KEYWORDS if keyword in text.lower()]

    # Extract reason
    reason = None
    for key, values in REASON_KEYWORDS.items():
        if any(val in text.lower() for val in values):
            reason = key
            break

    return {
        "location": location,
        "price": price,
        "gender": gender,
        "filters": filters,
        "reason": reason if reason else "Not specified"
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    data = request.json
    user_input = data.get('query', '')
    result = extract_info(user_input)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
