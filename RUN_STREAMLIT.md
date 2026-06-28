# Running the Streamlit UI

## Quick Start

### Method 1: Using the launcher script
```bash
python run_app.py
```

### Method 2: Direct Streamlit command
```bash
streamlit run ui/app.py
```

### Method 3: With specific port
```bash
streamlit run ui/app.py --server.port 8501
```

## Features

The Streamlit UI provides:

1. **Data Upload**
   - Upload CSV files via file uploader
   - Automatic data validation
   - Preview uploaded data

2. **Interactive Analysis**
   - Configurable column mapping (brand, price, feature)
   - Adjustable analysis parameters (top N, thresholds)
   - Real-time analysis execution

3. **Visualizations** (Plotly)
   - Brand distribution charts (bar & pie)
   - Pricing statistics and optimal ranges
   - Feature analysis charts
   - Market gap visualizations

4. **AI Summary**
   - LLM-generated summary (if API key configured)
   - Model information display
   - Error handling for quota issues

5. **Export Results**
   - Download analysis results as JSON
   - Includes all agent outputs and LLM summary

6. **WhatsApp share**
   - Pre-filled report summary via wa.me (click-to-chat)
   - Enter country code + phone on the Export tab

## Configuration

### API Key Setup
The app automatically loads API key from:
- `!.env` file (priority)
- `.env` file (fallback)
- Environment variable `GROQ_API_KEY`

### Sidebar Settings
- **Column Mapping**: Specify column names for brand, price, feature
- **Analysis Options**: Adjust top N values and gap threshold
- **LLM Summary**: Enable/disable AI summarization

## Usage

1. **Start the app**: `python run_app.py`
2. **Upload CSV**: Use file uploader or test with included `test_data.csv`
3. **Configure**: Adjust settings in sidebar if needed
4. **Run Analysis**: Click "Run Analysis" button
5. **View Results**: Scroll through visualizations and insights
6. **Export**: Download results if needed

## Requirements

- Python 3.11+
- Dependencies installed: `pip install -r requirements.txt`
- API key configured (optional, for LLM summary)

## Troubleshooting

**App won't start:**
- Check if Streamlit is installed: `pip install streamlit`
- Verify Python version: `python --version`

**Import errors:**
- Make sure you're in the project root directory
- Install dependencies: `pip install -r requirements.txt`

**API key issues:**
- Check `!.env` or `.env` file exists
- Verify API key format: `GROQ_API_KEY=gsk_...` (from https://console.groq.com)
- See `ENV_SETUP.md` for detailed setup

**Visualizations not showing:**
- Check if Plotly is installed: `pip install plotly`
- Verify data has correct column names

