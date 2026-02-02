#!/usr/bin/env python3
"""
Job Scraper for Visa Sponsorship Positions
Searches multiple job boards for DevOps/SRE roles with visa sponsorship
"""

import argparse
import csv
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Set

import pandas as pd
import yaml
from jobspy import scrape_jobs

# Browser automation for CAPTCHA handling (optional)
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

try:
    import undetected_chromedriver as uc
    UNDETECTED_CHROME_AVAILABLE = True
except ImportError:
    UNDETECTED_CHROME_AVAILABLE = False


class JobScraper:
    """Main job scraper class"""
    
    DEFAULT_CONFIG = {
        'job_roles': ['DevOps Engineer', 'Site Reliability Engineer'],
        'countries': ['germany', 'netherlands', 'sweden', 'spain', 'belgium', 'austria'],
        'job_sites': {
            'priority': ['indeed', 'glassdoor'],
            'secondary': ['linkedin', 'google', 'zip_recruiter'],
            'disabled': []
        },
        'visa_keywords': [
            'visa sponsorship',
            'visa',
            'visa support',
            'relocation package',
            'relocation assistance',
            'work permit',
            'sponsorship available',
            'relocation'
        ],
        'search_params': {
            'results_per_site': 50,
            'job_type': 'fulltime',
            'is_remote': False,
            'hours_old': 168,  # 7 days
            'distance': 50
        },
        'output': {
            'format': 'csv',
            'directory': 'results',
            'filename_pattern': 'jobs_{timestamp}.csv'
        },
        'exclusion_keywords': [
            'national of an EU member state',
            'EU member state national',
            'EU citizen',
            'European Union citizen',
            'EU citizenship required',
            'must be an EU national',
            'EU passport required',
            'citizenship of an EU country',
            'only EU nationals',
            'restricted to EU citizens',
            'EU/EEA nationals only',
            'EEA nationals only',
            'Swiss nationals only'
        ],
        'filters': {
            'visa_sponsorship_filter': True,
            'exclusion_filter': True,
            'case_sensitive': False
        },
        'captcha': {
            'enabled': False,  # Enable browser automation for manual CAPTCHA solving
            'method': 'manual',  # 'manual' or 'auto' (auto requires service integration)
            'browser': 'chrome',  # 'chrome' or 'undetected-chrome'
            'headless': False,  # Must be False for manual solving
            'wait_timeout': 300,  # Max seconds to wait for manual CAPTCHA solving
            'glassdoor_only': True  # Only use browser automation for Glassdoor
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize scraper with config"""
        self.config = self.DEFAULT_CONFIG.copy()
        
        if config_path and os.path.exists(config_path):
            self.load_config(config_path)
        
        self.results = []
        self.stats = {
            'total_scraped': 0,
            'after_filter': 0,
            'by_site': {},
            'by_country': {}
        }
        self.driver = None  # Browser driver for CAPTCHA handling
    
    def load_config(self, config_path: str):
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
            
            # Deep merge configs
            self._deep_update(self.config, user_config)
            print(f"✓ Loaded configuration from {config_path}")
        except Exception as e:
            print(f"⚠ Warning: Could not load config file: {e}")
            print("Using default configuration")
    
    def _deep_update(self, base_dict: dict, update_dict: dict):
        """Recursively update nested dictionaries"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def init_browser(self):
        """Initialize browser for CAPTCHA handling"""
        if not self.config['captcha']['enabled']:
            return None
        
        if not SELENIUM_AVAILABLE:
            print("⚠️  Warning: Selenium not installed. Install with: pip install selenium")
            print("   CAPTCHA handling disabled.")
            return None
        
        browser_type = self.config['captcha']['browser']
        headless = self.config['captcha']['headless']
        
        if headless and self.config['captcha']['method'] == 'manual':
            print("⚠️  Warning: Headless mode disabled for manual CAPTCHA solving")
            headless = False
        
        try:
            print("\n🌐 Initializing browser for CAPTCHA handling...")
            
            if browser_type == 'undetected-chrome' and UNDETECTED_CHROME_AVAILABLE:
                options = uc.ChromeOptions()
                if headless:
                    options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                self.driver = uc.Chrome(options=options)
                print("   ✓ Using undetected-chromedriver (better for Cloudflare)")
            else:
                if browser_type == 'undetected-chrome' and not UNDETECTED_CHROME_AVAILABLE:
                    print("   ⚠️  undetected-chromedriver not installed, using standard Chrome")
                    print("      Install with: pip install undetected-chromedriver")
                
                options = webdriver.ChromeOptions()
                if headless:
                    options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_experimental_option('excludeSwitches', ['enable-automation'])
                options.add_experimental_option('useAutomationExtension', False)
                
                self.driver = webdriver.Chrome(options=options)
                print("   ✓ Using standard Chrome WebDriver")
            
            return self.driver
        
        except Exception as e:
            print(f"❌ Error initializing browser: {e}")
            print("   Make sure ChromeDriver is installed and in PATH")
            print("   Install with: brew install chromedriver (macOS)")
            return None
    
    def close_browser(self):
        """Close browser if open"""
        if self.driver:
            try:
                self.driver.quit()
                print("\n🌐 Browser closed")
            except Exception as e:
                print(f"⚠️  Error closing browser: {e}")
            self.driver = None
    
    def handle_captcha_manual(self, url: str) -> bool:
        """Handle CAPTCHA manually by opening browser and waiting for user"""
        if not self.driver:
            self.driver = self.init_browser()
            if not self.driver:
                return False
        
        try:
            print(f"\n🔓 Opening browser for CAPTCHA handling...")
            print(f"   URL: {url}")
            
            self.driver.get(url)
            
            # Check if CAPTCHA/Cloudflare challenge is present
            time.sleep(3)  # Wait for page to load
            
            page_title = self.driver.title.lower()
            if 'cloudflare' in page_title or 'just a moment' in page_title:
                print("\n⚠️  Cloudflare challenge detected!")
                print("   📋 Please solve the CAPTCHA in the browser window")
                print(f"   ⏰ Waiting up to {self.config['captcha']['wait_timeout']} seconds...")
                print("   💡 The script will continue automatically once solved")
                
                # Wait for Cloudflare to be solved
                timeout = self.config['captcha']['wait_timeout']
                start_time = time.time()
                
                while time.time() - start_time < timeout:
                    time.sleep(2)
                    current_title = self.driver.title.lower()
                    
                    # Check if we've passed the challenge
                    if 'cloudflare' not in current_title and 'just a moment' not in current_title:
                        print("\n   ✅ CAPTCHA solved! Continuing...")
                        time.sleep(2)  # Give page time to fully load
                        return True
                    
                    # Show progress
                    elapsed = int(time.time() - start_time)
                    if elapsed % 10 == 0 and elapsed > 0:
                        print(f"   ⏳ Still waiting... ({elapsed}s elapsed)")
                
                print("\n   ⏰ Timeout waiting for CAPTCHA solution")
                return False
            else:
                print("   ✓ No CAPTCHA detected")
                return True
        
        except Exception as e:
            print(f"\n❌ Error handling CAPTCHA: {e}")
            return False
    
    def should_use_browser_for_site(self, site: str) -> bool:
        """Determine if browser automation should be used for this site"""
        if not self.config['captcha']['enabled']:
            return False
        
        if self.config['captcha']['glassdoor_only']:
            return site.lower() == 'glassdoor'
        
        return True
    
    def get_enabled_sites(self) -> List[str]:
        """Get list of enabled job sites"""
        priority = self.config['job_sites']['priority']
        secondary = self.config['job_sites']['secondary']
        disabled = set(self.config['job_sites']['disabled'])
        
        all_sites = priority + secondary
        enabled = [site for site in all_sites if site not in disabled]
        
        return enabled
    
    def compile_visa_keywords_pattern(self) -> re.Pattern:
        """Compile regex pattern for visa sponsorship keywords"""
        keywords = self.config['visa_keywords']
        # Escape special regex characters and join with OR
        escaped = [re.escape(kw) for kw in keywords]
        pattern = '|'.join(escaped)
        
        flags = re.IGNORECASE if not self.config['filters']['case_sensitive'] else 0
        return re.compile(pattern, flags)
    
    def compile_exclusion_keywords_pattern(self) -> re.Pattern:
        """Compile regex pattern for exclusion keywords"""
        keywords = self.config.get('exclusion_keywords', [])
        if not keywords:
            return None
        
        # Escape special regex characters and join with OR
        escaped = [re.escape(kw) for kw in keywords]
        pattern = '|'.join(escaped)
        
        flags = re.IGNORECASE if not self.config['filters']['case_sensitive'] else 0
        return re.compile(pattern, flags)
    
    def filter_by_exclusion(self, jobs_df: pd.DataFrame) -> pd.DataFrame:
        """Filter out jobs containing exclusion keywords (e.g., EU citizenship requirements)"""
        if not self.config['filters'].get('exclusion_filter', False):
            print("ℹ Exclusion filter is disabled")
            return jobs_df
        
        if jobs_df.empty:
            return jobs_df
        
        pattern = self.compile_exclusion_keywords_pattern()
        if pattern is None:
            return jobs_df
        
        print(f"\n🚫 Filtering out jobs with exclusion keywords...")
        print(f"   Excluding: EU citizenship requirements, etc.")
        
        original_count = len(jobs_df)
        
        # Check if description column exists
        if 'description' not in jobs_df.columns:
            print("⚠ Warning: No description column found, skipping exclusion filter")
            return jobs_df
        
        # Fill NaN descriptions with empty string
        jobs_df['description'] = jobs_df['description'].fillna('')
        
        # Apply exclusion filter (keep jobs that DON'T match exclusion patterns)
        mask = ~jobs_df['description'].str.contains(pattern, na=False, regex=True)
        filtered_df = jobs_df[mask].copy()
        
        filtered_count = len(filtered_df)
        excluded_count = original_count - filtered_count
        print(f"   ✓ Excluded {excluded_count} jobs with citizenship requirements ({filtered_count} remaining)")
        
        return filtered_df
    
    def filter_by_visa_sponsorship(self, jobs_df: pd.DataFrame) -> pd.DataFrame:
        """Filter jobs by visa sponsorship keywords in description"""
        if not self.config['filters']['visa_sponsorship_filter']:
            print("ℹ Visa sponsorship filter is disabled")
            return jobs_df
        
        if jobs_df.empty:
            return jobs_df
        
        print(f"\n🔍 Filtering for visa sponsorship keywords...")
        print(f"   Keywords: {', '.join(self.config['visa_keywords'][:3])}...")
        
        pattern = self.compile_visa_keywords_pattern()
        
        # Filter by description
        original_count = len(jobs_df)
        
        # Check if description column exists and is not null
        if 'description' not in jobs_df.columns:
            print("⚠ Warning: No description column found, skipping visa filter")
            return jobs_df
        
        # Fill NaN descriptions with empty string
        jobs_df['description'] = jobs_df['description'].fillna('')
        
        # Apply filter
        mask = jobs_df['description'].str.contains(pattern, na=False, regex=True)
        filtered_df = jobs_df[mask].copy()
        
        filtered_count = len(filtered_df)
        print(f"   ✓ Found {filtered_count} jobs with visa sponsorship ({original_count - filtered_count} filtered out)")
        
        # Add a flag column
        filtered_df['visa_sponsorship_mentioned'] = True
        
        return filtered_df
    
    def scrape_jobs_for_country(self, country: str, role: str) -> pd.DataFrame:
        """Scrape jobs for a specific country and role"""
        enabled_sites = self.get_enabled_sites()
        
        if not enabled_sites:
            print("⚠ No job sites enabled!")
            return pd.DataFrame()
        
        print(f"\n{'='*60}")
        print(f"🌍 Country: {country.upper()}")
        print(f"💼 Role: {role}")
        print(f"🔗 Sites: {', '.join(enabled_sites)}")
        print(f"{'='*60}")
        
        # Check if we need to pre-handle CAPTCHA for any sites
        if self.config['captcha']['enabled']:
            for site in enabled_sites:
                if self.should_use_browser_for_site(site):
                    print(f"\n🔓 Pre-checking {site} for CAPTCHA...")
                    # Pre-open Glassdoor to handle CAPTCHA
                    if site.lower() == 'glassdoor':
                        test_url = f"https://www.glassdoor.com/Job/germany-jobs-SRCH_IL.0,7_IN96.htm"
                        if not self.handle_captcha_manual(test_url):
                            print(f"   ⚠️  Could not pass CAPTCHA for {site}, results may be limited")
                        else:
                            print(f"   ✓ {site} CAPTCHA cleared")
        
        try:
            jobs_df = scrape_jobs(
                site_name=enabled_sites,
                search_term=role,
                location=country,
                distance=self.config['search_params']['distance'],
                is_remote=self.config['search_params']['is_remote'],
                job_type=self.config['search_params']['job_type'],
                results_wanted=self.config['search_params']['results_per_site'],
                hours_old=self.config['search_params']['hours_old'],
                country_indeed=country,
                description_format='markdown',  # Use markdown for descriptions (plain not supported)
                verbose=1
            )
            
            if not jobs_df.empty:
                # Add metadata
                jobs_df['search_country'] = country
                jobs_df['search_role'] = role
                jobs_df['scraped_at'] = datetime.now().isoformat()
                
                print(f"✓ Scraped {len(jobs_df)} jobs")
                
                # Update stats
                self.stats['total_scraped'] += len(jobs_df)
                self.stats['by_country'][country] = self.stats['by_country'].get(country, 0) + len(jobs_df)
                
                for site in jobs_df['site'].unique():
                    self.stats['by_site'][site] = self.stats['by_site'].get(site, 0) + len(jobs_df[jobs_df['site'] == site])
            
            return jobs_df
        
        except Exception as e:
            print(f"❌ Error scraping {country} for {role}: {str(e)}")
            return pd.DataFrame()
    
    def scrape_all(self) -> pd.DataFrame:
        """Scrape all configured countries and roles"""
        all_jobs = []
        
        total_combinations = len(self.config['countries']) * len(self.config['job_roles'])
        current = 0
        
        print(f"\n🚀 Starting job search...")
        print(f"   Roles: {len(self.config['job_roles'])}")
        print(f"   Countries: {len(self.config['countries'])}")
        print(f"   Total searches: {total_combinations}")
        
        for country in self.config['countries']:
            for role in self.config['job_roles']:
                current += 1
                print(f"\n[{current}/{total_combinations}] ", end="")
                
                jobs_df = self.scrape_jobs_for_country(country, role)
                
                if not jobs_df.empty:
                    all_jobs.append(jobs_df)
        
        if not all_jobs:
            print("\n⚠ No jobs found!")
            return pd.DataFrame()
        
        # Combine all results
        combined_df = pd.concat(all_jobs, ignore_index=True)
        
        # Remove duplicates based on job_url
        original_count = len(combined_df)
        combined_df = combined_df.drop_duplicates(subset=['job_url'], keep='first')
        duplicates_removed = original_count - len(combined_df)
        
        if duplicates_removed > 0:
            print(f"\n🔄 Removed {duplicates_removed} duplicate job listings")
        
        print(f"\n📊 Total unique jobs scraped: {len(combined_df)}")
        
        return combined_df
    
    def save_results(self, jobs_df: pd.DataFrame, output_path: Optional[str] = None, suffix: str = ''):
        """Save results to file"""
        if jobs_df.empty:
            print("\n⚠ No jobs to save!")
            return
        
        # Create output directory
        output_dir = Path(self.config['output']['directory'])
        output_dir.mkdir(exist_ok=True)
        
        # Generate filename
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.config['output']['filename_pattern'].format(timestamp=timestamp)
            # Add suffix if provided
            if suffix:
                filename = filename.replace('.csv', f'{suffix}.csv')
            output_path = output_dir / filename
        elif suffix:
            # Add suffix to provided path
            output_path = Path(str(output_path).replace('.csv', f'{suffix}.csv'))
        
        # Drop description column to prevent CSV formatting issues
        if 'description' in jobs_df.columns:
            jobs_df = jobs_df.drop(columns=['description'])
        
        # Reorder columns for better readability
        priority_columns = [
            'site', 'title', 'company', 'location', 'date_posted',
            'job_type', 'job_url', 'search_country', 
            'search_role', 'visa_sponsorship_mentioned', 'note'
        ]
        
        # Keep only existing columns
        existing_priority = [col for col in priority_columns if col in jobs_df.columns]
        other_columns = [col for col in jobs_df.columns if col not in existing_priority]
        ordered_columns = existing_priority + other_columns
        
        jobs_df = jobs_df[ordered_columns]
        
        # Save based on format
        output_format = self.config['output']['format'].lower()
        
        if output_format == 'csv':
            jobs_df.to_csv(output_path, index=False, quoting=csv.QUOTE_ALL)
            print(f"\n✅ Results saved to: {output_path}")
        elif output_format == 'json':
            output_path = Path(str(output_path).replace('.csv', '.json'))
            jobs_df.to_json(output_path, orient='records', indent=2)
            print(f"\n✅ Results saved to: {output_path}")
        elif output_format == 'excel':
            output_path = Path(str(output_path).replace('.csv', '.xlsx'))
            jobs_df.to_excel(output_path, index=False)
            print(f"\n✅ Results saved to: {output_path}")
        else:
            print(f"⚠ Unknown format: {output_format}, saving as CSV")
            jobs_df.to_csv(output_path, index=False, quoting=csv.QUOTE_ALL)
        
        # Save separate files per site if requested
        if len(jobs_df['site'].unique()) > 1:
            print(f"\n📑 Saving separate files by site...")
            for site in jobs_df['site'].unique():
                site_df = jobs_df[jobs_df['site'] == site]
                site_filename = str(output_path).replace('.csv', f'_{site}.csv')
                site_df.to_csv(site_filename, index=False, quoting=csv.QUOTE_ALL)
                print(f"   ✓ {site}: {len(site_df)} jobs → {Path(site_filename).name}")
    
    def print_statistics(self):
        """Print scraping statistics"""
        print(f"\n{'='*60}")
        print(f"📈 STATISTICS")
        print(f"{'='*60}")
        print(f"Total jobs scraped: {self.stats['total_scraped']}")
        print(f"After filtering: {self.stats['after_filter']}")
        
        if self.stats['by_site']:
            print(f"\n📊 By Site:")
            for site, count in sorted(self.stats['by_site'].items(), key=lambda x: x[1], reverse=True):
                print(f"   {site}: {count}")
        
        if self.stats['by_country']:
            print(f"\n🌍 By Country:")
            for country, count in sorted(self.stats['by_country'].items(), key=lambda x: x[1], reverse=True):
                print(f"   {country}: {count}")
        
        print(f"{'='*60}")
    
    def run(self, output_path: Optional[str] = None):
        """Main execution method"""
        print("\n" + "="*60)
        print("🔍 JOB SCRAPER FOR VISA SPONSORSHIP POSITIONS")
        print("="*60)
        
        try:
            # Scrape jobs
            jobs_df = self.scrape_all()
            
            if jobs_df.empty:
                return
            
            # Filter by visa sponsorship
            filtered_df = self.filter_by_visa_sponsorship(jobs_df)
            
            # Apply exclusion filter (remove jobs requiring EU citizenship)
            filtered_df = self.filter_by_exclusion(filtered_df)
            
            self.stats['after_filter'] = len(filtered_df)
            
            # Save results
            if filtered_df.empty and not jobs_df.empty:
                # No results after filtering, but we have unfiltered results
                print("\n⚠️  No jobs found with visa sponsorship keywords")
                print("💾 Saving unfiltered results for manual review...")
                
                # Add a note column
                jobs_df['note'] = 'No visa keywords found - manual review needed'
                self.save_results(jobs_df, output_path, suffix='_unfiltered')
            elif not filtered_df.empty:
                # Save filtered results
                self.save_results(filtered_df, output_path)
                
                # Also save unfiltered if different
                if len(filtered_df) < len(jobs_df):
                    print(f"\n💾 Also saving unfiltered results ({len(jobs_df)} total jobs)...")
                    jobs_df['note'] = 'Unfiltered - may not have visa keywords'
                    self.save_results(jobs_df, output_path, suffix='_all_jobs')
            
            # Print stats
            self.print_statistics()
        
        finally:
            # Always close browser if open
            self.close_browser()


def interactive_mode():
    """Run scraper in interactive mode"""
    print("\n🤖 INTERACTIVE JOB SCRAPER")
    print("="*60)
    
    # Ask for job roles
    print("\n1️⃣  Job Roles")
    roles_input = input("Enter job roles (comma-separated) [DevOps Engineer,Site Reliability Engineer]: ").strip()
    roles = [r.strip() for r in roles_input.split(',')] if roles_input else ['DevOps Engineer', 'Site Reliability Engineer']
    
    # Ask for countries
    print("\n2️⃣  Countries")
    print("Available: germany, netherlands, sweden, spain, belgium, austria")
    countries_input = input("Enter countries (comma-separated) [all]: ").strip()
    if countries_input.lower() in ['all', '']:
        countries = ['germany', 'netherlands', 'sweden', 'spain', 'belgium', 'austria']
    else:
        countries = [c.strip().lower() for c in countries_input.split(',')]
    
    # Ask for job sites
    print("\n3️⃣  Job Sites")
    print("Available: indeed, glassdoor, linkedin, google, zip_recruiter")
    sites_input = input("Enter sites to EXCLUDE (comma-separated) [none]: ").strip()
    disabled_sites = [s.strip().lower() for s in sites_input.split(',')] if sites_input else []
    
    # Ask for results per site
    print("\n4️⃣  Results")
    results_input = input("Results per site [50]: ").strip()
    results_per_site = int(results_input) if results_input.isdigit() else 50
    
    # Ask for visa filter
    print("\n5️⃣  Visa Sponsorship Filter")
    visa_filter = input("Enable visa sponsorship filter? [Y/n]: ").strip().lower()
    visa_filter_enabled = visa_filter != 'n'
    
    # Ask for days old
    print("\n6️⃣  Job Age")
    days_input = input("Max days old [7]: ").strip()
    days_old = int(days_input) if days_input.isdigit() else 7
    
    # Create config
    config = JobScraper.DEFAULT_CONFIG.copy()
    config['job_roles'] = roles
    config['countries'] = countries
    config['job_sites']['disabled'] = disabled_sites
    config['search_params']['results_per_site'] = results_per_site
    config['filters']['visa_sponsorship_filter'] = visa_filter_enabled
    config['search_params']['hours_old'] = days_old * 24
    
    print("\n" + "="*60)
    print("Configuration:")
    print(f"  Roles: {', '.join(roles)}")
    print(f"  Countries: {', '.join(countries)}")
    print(f"  Excluded sites: {', '.join(disabled_sites) if disabled_sites else 'none'}")
    print(f"  Results per site: {results_per_site}")
    print(f"  Visa filter: {'enabled' if visa_filter_enabled else 'disabled'}")
    print(f"  Max age: {days_old} days")
    print("="*60)
    
    confirm = input("\nProceed? [Y/n]: ").strip().lower()
    if confirm == 'n':
        print("Cancelled.")
        return
    
    # Run scraper
    scraper = JobScraper()
    scraper.config = config
    scraper.run()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Job Scraper for Visa Sponsorship Positions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use config file
  python job_scraper.py --config config.yaml
  
  # CLI arguments
  python job_scraper.py --roles "DevOps Engineer" "SRE" --countries germany sweden
  
  # Interactive mode
  python job_scraper.py --interactive
  
  # Exclude specific sites
  python job_scraper.py --exclude-sites linkedin google --no-visa-filter
  
  # Change results per site
  python job_scraper.py --results 100 --days 14
        """
    )
    
    parser.add_argument('-c', '--config', help='Path to config YAML file')
    parser.add_argument('-i', '--interactive', action='store_true', help='Run in interactive mode')
    parser.add_argument('-r', '--roles', nargs='+', help='Job roles to search for')
    parser.add_argument('--countries', nargs='+', help='Countries to search in')
    parser.add_argument('--exclude-sites', nargs='+', help='Job sites to exclude')
    parser.add_argument('--results', type=int, help='Results per site (default: 50)')
    parser.add_argument('--days', type=int, help='Max job age in days (default: 7)')
    parser.add_argument('--no-visa-filter', action='store_true', help='Disable visa sponsorship filter')
    parser.add_argument('-o', '--output', help='Output file path')
    parser.add_argument('--format', choices=['csv', 'json', 'excel'], help='Output format')
    
    args = parser.parse_args()
    
    # Interactive mode
    if args.interactive:
        interactive_mode()
        return
    
    # Load config or use defaults
    scraper = JobScraper(args.config)
    
    # Override with CLI arguments
    if args.roles:
        scraper.config['job_roles'] = args.roles
    
    if args.countries:
        scraper.config['countries'] = [c.lower() for c in args.countries]
    
    if args.exclude_sites:
        scraper.config['job_sites']['disabled'] = [s.lower() for s in args.exclude_sites]
    
    if args.results:
        scraper.config['search_params']['results_per_site'] = args.results
    
    if args.days:
        scraper.config['search_params']['hours_old'] = args.days * 24
    
    if args.no_visa_filter:
        scraper.config['filters']['visa_sponsorship_filter'] = False
    
    if args.format:
        scraper.config['output']['format'] = args.format
    
    # Run scraper
    scraper.run(args.output)


if __name__ == '__main__':
    main()
