// This script runs on every webpage and can analyze page content
// For now, it's minimal but can be extended to extract company info from pages

// Function to extract company information from the page
function extractCompanyInfo() {
  const domain = window.location.hostname.replace('www.', '');
  
  // Try to find company name in various places
  const title = document.title;
  const h1 = document.querySelector('h1')?.textContent?.trim() || '';
  
  // Look for OpenGraph site name (most reliable)
  const metaTitle = document.querySelector('meta[property="og:site_name"]')?.content?.trim() || 
                   document.querySelector('meta[name="application-name"]')?.content?.trim() || '';
  
  // Look for other meta tags that might contain company name
  const metaDescription = document.querySelector('meta[name="description"]')?.content?.trim() || '';
  
  // Try to find company name in footer or header
  const footerText = document.querySelector('footer')?.textContent?.trim() || '';
  const headerText = document.querySelector('header')?.textContent?.trim() || '';
  
  return {
    domain: domain,
    title: title,
    h1: h1,
    metaTitle: metaTitle,
    metaDescription: metaDescription.substring(0, 200), // Limit length
    footerText: footerText.substring(0, 200),
    headerText: headerText.substring(0, 200),
    url: window.location.href
  };
}

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getPageInfo') {
    const pageInfo = extractCompanyInfo();
    sendResponse(pageInfo);
  }
});

// Optional: You could also inject a visual indicator on PE-owned sites
// This is commented out but shows how you could add visual elements to pages
/*
function addPEIndicator() {
  const indicator = document.createElement('div');
  indicator.style.cssText = `
    position: fixed;
    top: 10px;
    right: 10px;
    background: #ff5722;
    color: white;
    padding: 8px 12px;
    border-radius: 4px;
    font-family: Arial, sans-serif;
    font-size: 12px;
    z-index: 10000;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
  `;
  indicator.textContent = '⚠️ PE Owned';
  document.body.appendChild(indicator);
}
*/