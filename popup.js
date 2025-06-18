// popup.js - Popup script for PE Checker extension

// Extract domain from URL
function getDomain(url) {
  try {
    const hostname = new URL(url).hostname;
    return hostname.replace('www.', '');
  } catch (e) {
    return null;
  }
}

// Extract company name from domain
function getCompanyFromDomain(domain) {
  if (!domain) return 'Unknown';
  
  // Remove common TLDs and clean up
  const name = domain
    .replace(/\.(com|org|net|edu|gov|co\.uk|co|io|ai|ly)$/i, '')
    .split('.')[0]  // Take first part if there are subdomains
    .replace(/[-_]/g, ' ')  // Replace hyphens/underscores with spaces
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
  
  return name;
}

// Enhanced company name extraction from page content
async function getCompanyFromPage() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    // Send message to content script to get page info
    const pageInfo = await chrome.tabs.sendMessage(tab.id, { action: 'getPageInfo' });
    
    if (pageInfo) {
      // Priority order for company name extraction:
      
      // 1. OpenGraph site name (most reliable)
      if (pageInfo.metaTitle && pageInfo.metaTitle !== pageInfo.title) {
        return pageInfo.metaTitle;
      }
      
      // 2. Clean up page title
      if (pageInfo.title) {
        let title = pageInfo.title;
        
        // Remove common suffixes
        title = title.replace(/\s*[-|•]\s*(Home|Welcome|Official Site|Website).*$/i, '');
        title = title.replace(/\s*[-|•]\s*.*$/i, ''); // Remove everything after first separator
        
        // If title looks like a company name (not too long, not generic)
        if (title.length > 0 && title.length < 50 && !title.toLowerCase().includes('untitled')) {
          return title.trim();
        }
      }
      
      // 3. Use domain-based name
      return getCompanyFromDomain(pageInfo.domain);
    }
    
    // Fallback to domain-based extraction
    const domain = getDomain(tab.url);
    return getCompanyFromDomain(domain);
    
  } catch (error) {
    console.log('Could not extract from page, using domain:', error);
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const domain = getDomain(tab.url);
    return getCompanyFromDomain(domain);
  }
}

// Update UI with results
async function updateUI(domain, companyData, actualCompanyName) {
  const companyNameEl = document.getElementById('company-name');
  const websiteUrlEl = document.getElementById('website-url');
  const peStatusEl = document.getElementById('pe-status');
  const detailsEl = document.getElementById('details');
  
  // Show the actual company name we extracted
  companyNameEl.textContent = actualCompanyName || 'Unknown';
  websiteUrlEl.textContent = domain;
  
  if (companyData) {
    peStatusEl.textContent = 'Private Equity Owned';
    peStatusEl.className = 'pe-status pe-owned';
    detailsEl.innerHTML = `
      <strong>Owner:</strong> ${companyData.owner}<br>
      <strong>Acquired:</strong> ${companyData.year}<br>
      <em>This company is owned by private equity.</em>
    `;
  } else {
    peStatusEl.textContent = 'Not in PE Database';
    peStatusEl.className = 'pe-status not-pe-owned';
    detailsEl.innerHTML = `
      <em>No private equity ownership found in our database. This doesn't guarantee the company isn't PE-owned, just that it's not in our current records.</em>
    `;
  }
}

// Main function
async function checkCurrentSite() {
  try {
    // Get current tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const domain = getDomain(tab.url);
    
    if (!domain) {
      document.getElementById('loading').style.display = 'none';
      document.getElementById('results').style.display = 'block';
      document.getElementById('details').textContent = 'Unable to analyze this page.';
      return;
    }
    
    // Extract company name from the page
    const companyName = await getCompanyFromPage();
    
    // Check PE ownership via background script
    const companyData = await chrome.runtime.sendMessage({
      action: 'checkDomain',
      domain: domain
    });
    
    // Update UI with both PE data and extracted company name
    document.getElementById('loading').style.display = 'none';
    document.getElementById('results').style.display = 'block';
    await updateUI(domain, companyData, companyName);
    
  } catch (error) {
    console.error('Error checking site:', error);
    document.getElementById('loading').textContent = 'Error analyzing site';
  }
}

// Event listeners
document.addEventListener('DOMContentLoaded', checkCurrentSite);
document.getElementById('check-button')?.addEventListener('click', checkCurrentSite);