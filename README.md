# Job Scraper for Visa Sponsorship Positions

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A flexible Python script to search for DevOps/SRE jobs with visa sponsorship across multiple European countries and job boards.

> **🎯 Perfect for:** Non-EU developers looking for jobs in Europe that offer visa sponsorship and relocation assistance.

## Features

- 🌍 **Multi-country search**: Germany, Netherlands, Sweden, Spain, Belgium, Austria
- 💼 **Multiple job boards**: Indeed, Glassdoor (priority) + LinkedIn, Google, ZipRecruiter
- 🔍 **Smart filtering**: Filters jobs by visa sponsorship keywords in descriptions
- 🚫 **Exclusion filtering**: Automatically removes jobs requiring EU citizenship/nationality
- ⚙️ **Flexible configuration**: CLI arguments, config file, or interactive mode
- 📊 **Detailed statistics**: Results by site and country
- 📁 **Multiple formats**: CSV (default), JSON, or Excel output
- 🎯 **Customizable**: Enable/disable specific sites, adjust search parameters

## Installation

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Quick activation:** After initial setup, just run:
```bash
source venv/bin/activate
```

## Quick Start

### 1. Using Config File (Recommended)
```bash
python job_scraper.py --config config.yaml
```

### 2. Interactive Mode
```bash
python job_scraper.py --interactive
```

### 3. CLI Arguments
```bash
python job_scraper.py --roles "DevOps Engineer" "SRE" --countries germany sweden
```

## Usage Examples

### Basic Search
```bash
# Default settings (config.yaml)
python job_scraper.py

# With custom config
python job_scraper.py --config my_config.yaml
```

### Custom Roles and Countries
```bash
python job_scraper.py --roles "DevOps Engineer" "Platform Engineer" --countries germany netherlands
```

### Exclude Specific Job Sites
```bash
# Exclude LinkedIn and Google
python job_scraper.py --exclude-sites linkedin google
```

### Adjust Results and Filters
```bash
# Get 100 results per site, jobs from last 14 days
python job_scraper.py --results 100 --days 14

# Disable visa sponsorship filter (get all jobs)
python job_scraper.py --no-visa-filter
```

### Custom Output
```bash
# Save to specific file
python job_scraper.py --output my_jobs.csv

# Save as JSON
python job_scraper.py --format json

# Save as Excel
python job_scraper.py --format excel
```

### Combined Example
```bash
python job_scraper.py \
  --roles "DevOps Engineer" "Site Reliability Engineer" \
  --countries germany netherlands sweden \
  --exclude-sites zip_recruiter \
  --results 75 \
  --days 10 \
  --output jobs_eu.csv
```

## Configuration File

Edit `config.yaml` to customize default settings:

```yaml
job_roles:
  - DevOps Engineer
  - Site Reliability Engineer

countries:
  - germany
  - netherlands
  - sweden

job_sites:
  disabled:
    - zip_recruiter  # Add sites to exclude

search_params:
  results_per_site: 50
  hours_old: 168  # 7 days

filters:
  visa_sponsorship_filter: true
```

## Output

Results are saved to the `results/` directory with:
- ✅ Main CSV file with all jobs
- ✅ Separate CSV files per job site
- ✅ Columns: site, title, company, location, job_url, description, etc.
- ✅ Metadata: search_country, search_role, scraped_at

### Output Columns
- `site` - Job board (indeed, glassdoor, etc.)
- `title` - Job title
- `company` - Company name
- `location` - Job location
- `date_posted` - When job was posted
- `job_type` - Full-time, part-time, etc.
- `job_url` - Direct link to job posting
- `search_country` - Country searched
- `search_role` - Role searched for
- `visa_sponsorship_mentioned` - True if visa keywords found
- `scraped_at` - Timestamp of scrape

**Note:** The description column is excluded from CSV output to prevent formatting issues. You can view job descriptions by visiting the `job_url`.

## Visa Sponsorship Keywords

The script searches for these keywords in job descriptions (configurable in `config.yaml`):
- visa sponsorship
- visa support
- relocation package
- relocation assistance
- work permit
- sponsorship available
- relocation

## Exclusion Filter

The scraper automatically **excludes** jobs that require EU/EEA citizenship or nationality. Jobs containing phrases like:
- "national of an EU member state"
- "EU citizenship required"
- "only EU nationals"
- "EU/EEA nationals only"
- And similar citizenship requirements

This ensures you only see jobs that are genuinely open to non-EU candidates requiring visa sponsorship.

**Disable this filter** in `config.yaml`:
```yaml
filters:
  exclusion_filter: false
```

Or customize the exclusion keywords in `config.yaml` under `exclusion_keywords`.

## Tips

1. **Indeed & Glassdoor**: Most reliable for European job searches
2. **Rate Limiting**: If you get blocked, wait a few minutes or use proxies
3. **LinkedIn**: Can be aggressive with rate limiting, consider excluding if issues occur
4. **Results**: Start with 50 per site to avoid long wait times
5. **Filtering**: Keep visa filter enabled to focus on relevant jobs

## Troubleshooting

### No results found
- Try disabling visa filter: `--no-visa-filter`
- Reduce results per site: `--results 25`
- Check if sites are responding

### Rate limiting (429 errors)
- Wait a few minutes between searches
- Reduce number of sites or countries
- Consider using proxies (see `.env.example`)

### LinkedIn blocking
- Exclude LinkedIn: `--exclude-sites linkedin`
- Use proxies

## Command Reference

```
Arguments:
  -c, --config PATH          Config file path
  -i, --interactive          Interactive mode
  -r, --roles ROLE [ROLE]    Job roles
  --countries COUNTRY [..]   Countries to search
  --exclude-sites SITE [..]  Sites to exclude
  --results N                Results per site
  --days N                   Max job age in days
  --no-visa-filter           Disable visa filter
  -o, --output PATH          Output file
  --format {csv,json,excel}  Output format
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Disclaimer

This tool is for personal use to assist with job searching. Please respect the terms of service of the job boards you search. Use responsibly and avoid excessive requests that could impact the services.

