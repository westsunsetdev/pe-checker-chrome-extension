// background.js - Service Worker for PE Checker extension
let peOwnedCompanies = {};

// Load PE database when extension starts
chrome.runtime.onStartup.addListener(loadPEDatabase);
chrome.runtime.onInstalled.addListener(loadPEDatabase);

// Load PE database from JSON file
async function loadPEDatabase() {
  try {
    const response = await fetch(chrome.runtime.getURL('pe_database.json'));
    const text = await response.text();
    peOwnedCompanies = JSON.parse(text);
    console.log(`Loaded ${Object.keys(peOwnedCompanies).length} PE companies from database`);
  } catch (error) {
    console.error('Error loading PE database:', error);
    
    // Fallback to minimal hardcoded data if file loading fails
    peOwnedCompanies = {
      'petco.com': {
        company: 'Petco',
        owner: 'CVC Capital Partners & CPP Investments',
        year: '2020',
        source: 'Fallback'
      }
    };
  }
}

// Listen for messages from popup and content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'checkDomain') {
    const result = checkPEOwnership(request.domain);
    sendResponse(result);
    return true;
  }
  
  if (request.action === 'getPEDatabase') {
    sendResponse(peOwnedCompanies);
    return true;
  }
});

// Check if company is PE-owned
function checkPEOwnership(domain) {
  if (!domain) return null;
  
  // Clean domain
  const cleanDomain = domain.replace(/^www\./, '').toLowerCase();
  
  // Direct match
  if (peOwnedCompanies[cleanDomain]) {
    return peOwnedCompanies[cleanDomain];
  }
  
  // Check for matches in the database
  for (const [key, value] of Object.entries(peOwnedCompanies)) {
    // Check if the database domain matches
    if (value.domain && value.domain.replace(/^www\./, '').toLowerCase() === cleanDomain) {
      return value;
    }
    
    // Check if key matches domain
    if (key.includes(cleanDomain) || cleanDomain.includes(key.replace('.com', ''))) {
      return value;
    }
  }
  
  return null;
}