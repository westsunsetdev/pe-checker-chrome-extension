#!/usr/bin/env python3
"""
Wikipedia Private Equity Companies Scraper - CORRECTED VERSION
Scrapes PE firms from subcategories, then matches portfolio companies from the main category
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time
from urllib.parse import urljoin, urlparse
import csv

class WikipediaPEScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.companies = {}
        self.pe_firms = []
        self.errors = []

    def scrape_main_category_page(self, category_url):
        """Scrape the main category page to get PE firms and portfolio companies"""
        print(f"Scraping main category page: {category_url}")
        
        try:
            response = self.session.get(category_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Get PE firms from Subcategories section
            pe_firms = self._extract_subcategories(soup)
            
            # Get portfolio companies from Pages in category section  
            portfolio_companies = self._extract_pages_in_category(soup)
            
            return pe_firms, portfolio_companies
            
        except Exception as e:
            error_msg = f"Error scraping category page {category_url}: {str(e)}"
            print(error_msg)
            self.errors.append(error_msg)
            return [], []

    def _extract_subcategories(self, soup):
        """Extract PE firms from the Subcategories section"""
        pe_firms = []
        
        # Look for the subcategories section
        subcategories_section = soup.find('div', {'id': 'mw-subcategories'})
        
        if not subcategories_section:
            print("Could not find subcategories section")
            return pe_firms
        
        # Find all links in subcategories
        links = subcategories_section.find_all('a', href=True)
        
        for link in links:
            href = link.get('href')
            if href and '/wiki/Category:' in href:
                firm_name = link.get_text().strip()
                # Remove "portfolio companies" from the end if present
                firm_name = re.sub(r'\s+portfolio companies$', '', firm_name, flags=re.IGNORECASE)
                
                full_url = urljoin('https://en.wikipedia.org', href)
                
                pe_firms.append({
                    'name': firm_name,
                    'category_url': full_url,
                    'category_name': link.get_text().strip()
                })
                print(f"Found PE firm: {firm_name}")
        
        print(f"Found {len(pe_firms)} PE firms in subcategories")
        return pe_firms

    def _extract_pages_in_category(self, soup):
        """Extract portfolio companies from Pages in category section"""
        companies = []
        
        # Look for the pages section
        pages_section = soup.find('div', {'id': 'mw-pages'})
        
        if not pages_section:
            print("Could not find pages in category section")
            return companies
        
        # Find all links in pages section
        links = pages_section.find_all('a', href=True)
        
        for link in links:
            href = link.get('href')
            if href and href.startswith('/wiki/') and ':' not in href:  # Avoid special pages
                company_name = link.get_text().strip()
                full_url = urljoin('https://en.wikipedia.org', href)
                
                companies.append({
                    'name': company_name,
                    'url': full_url
                })
                print(f"Found portfolio company: {company_name}")
        
        print(f"Found {len(companies)} portfolio companies in pages section")
        return companies

    def scrape_all_pe_firm_categories(self, pe_firms):
        """Get ALL portfolio companies directly from each PE firm's category page"""
        print("\nGetting companies from each PE firm's category...")
        print("=" * 60)
        
        for i, firm in enumerate(pe_firms, 1):
            print(f"\n[{i}/{len(pe_firms)}] Scraping {firm['name']} category...")
            
            # Get ALL companies in this PE firm's specific category
            self._scrape_pe_firm_category(firm['category_url'], firm['name'])
            
            time.sleep(1)  # Be respectful to Wikipedia

    def _scrape_pe_firm_category(self, category_url, pe_firm_name):
        """Scrape all companies from a specific PE firm's category page"""
        try:
            response = self.session.get(category_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for pages in this category
            pages_section = soup.find('div', {'id': 'mw-pages'})
            
            if not pages_section:
                print(f"  No pages section found for {pe_firm_name}")
                return
            
            links = pages_section.find_all('a', href=True)
            companies_added = 0
            
            for link in links:
                href = link.get('href')
                if href and href.startswith('/wiki/') and ':' not in href:
                    company_name = link.get_text().strip()
                    self._add_company(company_name, pe_firm_name)
                    companies_added += 1
            
            print(f"  Added {companies_added} companies for {pe_firm_name}")
            
        except Exception as e:
            error_msg = f"Error scraping category {category_url}: {str(e)}"
            print(f"  Error: {str(e)}")
            self.errors.append(error_msg)

    def _add_company(self, company_name, pe_firm, year=None):
        """Add company to our database"""
    if not company_name or len(company_name) < 2:
        return

    # Clean the company name
    clean_name = self._clean_company_name(company_name)
    if not clean_name:
        return

    # Try to guess website domain
    domain = self._guess_domain(clean_name)

    # Clean owner name
    cleaned_owner = re.sub(r'\s+companies$', '', pe_firm, flags=re.IGNORECASE).strip()

    key = domain if domain else clean_name.lower().replace(' ', '').replace('.', '')

    self.companies[key] = {
        'company': clean_name,
        'original_name': company_name,
        'owner': cleaned_owner,
        'domain': domain,
        'source': 'Wikipedia'
    }

    print(f"  Matched: {clean_name} → {cleaned_owner}")


    def _clean_company_name(self, name):
        """Clean and normalize company name"""
        if not name:
            return None
            
        # Remove common suffixes and prefixes
        name = re.sub(r'\s*(Inc\.?|LLC|Corp\.?|Ltd\.?|Co\.?|Company|Group|Holdings?|plc|PLC)\.?\s*$', '', name, flags=re.IGNORECASE)
        name = re.sub(r'^\s*(The|A)\s+', '', name, flags=re.IGNORECASE)
        
        # Remove extra whitespace
        name = ' '.join(name.split())
        
        # Skip if too short
        if len(name) < 2:
            return None
            
        return name.strip()

    def _guess_domain(self, company_name):
        """Attempt to guess likely domain name"""
        clean_name = company_name.lower()
        
        # Handle special cases and common company name patterns
        clean_name = re.sub(r'\s+', '', clean_name)  # Remove spaces
        clean_name = re.sub(r'[^a-z0-9]', '', clean_name)  # Remove special chars
        
        # Skip if name is too generic or short
        if len(clean_name) < 3 or clean_name in ['inc', 'llc', 'corp', 'ltd', 'plc']:
            return None
            
        return f"{clean_name}.com"

    def scrape_pe_ecosystem(self, category_url):
        """Main method to scrape PE ecosystem with correct logic"""
        print("Starting CORRECTED PE ecosystem scrape...")
        print("=" * 60)
        
        # Step 1: Get PE firms from main category page
        pe_firms, _ = self.scrape_main_category_page(category_url)
        
        if not pe_firms:
            print("Could not find PE firms, stopping...")
            return
        
        self.pe_firms = pe_firms
        
        # Step 2: Get ALL portfolio companies directly from each PE firm's category
        self.scrape_all_pe_firm_categories(pe_firms)
        
        print(f"\n" + "=" * 60)
        print("Scraping completed!")

    def save_to_json(self, filename='pe_database.json'):
        """Save scraped data to JSON file for Chrome extension"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.companies, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(self.companies)} companies to {filename}")

    def save_to_csv(self, filename='pe_companies.csv'):
        """Save scraped data to CSV file"""
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Domain', 'Company', 'Original_Name', 'PE Firm', 'Source'])

        for key, data in self.companies.items():
            writer.writerow([
                data.get('domain', ''),
                data['company'],
                data['original_name'],
                data['owner'],
                data['source']
            ])
    print(f"Saved {len(self.companies)} companies to {filename}")


    def print_summary(self):
        """Print summary of scraped data"""
        print(f"\n--- SCRAPING SUMMARY ---")
        print(f"PE firms found: {len(self.pe_firms)}")
        print(f"Total companies matched: {len(self.companies)}")
        print(f"Errors encountered: {len(self.errors)}")
        
        # Show PE firms found
        print(f"\nPE firms found:")
        for firm in self.pe_firms:
            print(f"  - {firm['name']}")
        
        # Show top PE firms by number of companies
        pe_counts = {}
        for company_data in self.companies.values():
            pe_firm = company_data['owner']
            pe_counts[pe_firm] = pe_counts.get(pe_firm, 0) + 1
        
        if pe_counts:
            print(f"\nPE firms by portfolio size:")
            for pe_firm, count in sorted(pe_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  {pe_firm}: {count} companies")
        
        if self.errors:
            print(f"\nErrors:")
            for error in self.errors[:5]:  # Show first 5 errors
                print(f"  - {error}")
            if len(self.errors) > 5:
                print(f"  ... and {len(self.errors) - 5} more errors")

# Example usage
if __name__ == "__main__":
    scraper = WikipediaPEScraper()
    
    # Wikipedia category page for PE portfolio companies
    category_url = "https://en.wikipedia.org/w/index.php?title=Category:Private_equity_portfolio_companies"
    
    print("Starting CORRECTED Wikipedia PE ecosystem scraper...")
    print("This will:")
    print("1. Get PE firms from 'Subcategories' section (should be ~26 firms)")
    print("2. Get portfolio companies from 'Pages in category' section")
    print("3. Match each company to its PE firm by checking individual categories")
    print("4. Save results to JSON and CSV files")
    print("=" * 60)
    
    # Scrape the entire ecosystem
    scraper.scrape_pe_ecosystem(category_url)
    
    # Save results
    scraper.save_to_json('pe_database.json')
    scraper.save_to_csv('pe_companies.csv')
    
    # Print summary
    scraper.print_summary()
    
    print("\nDone! Files created:")
    print("- pe_database.json (ready for Chrome extension)")
    print("- pe_companies.csv (for review/editing)")
    print("\nTo use in your Chrome extension:")
    print("1. Copy pe_database.json to your extension folder")
    print("2. Refresh your extension in chrome://extensions/")
    print("3. Test on some websites!")