// ============================================================================
// GROK 4.1 – RETAIL HYPE SCORER v9.0 (REAL DATA + TRANSCRIPTS + WEB SEARCH)
// ============================================================================
//
// WHAT'S NEW IN v9.0:
// - Reads pre-fetched TECHNICAL DATA from "Tech_Data" tab
// - Reads pre-fetched TRANSCRIPT SUMMARIES from "Transcripts" tab
// - Enriched prompts include REAL indicator values (not just web search)
// - Grok focuses web search on SOCIAL/SENTIMENT data only
// - Data freshness indicator shows when data was last fetched
//
// WORKFLOW:
// 1. Run Python script: python sheet_data_loader.py
// 2. Run this scorer from Sheets menu: 🚀 Hype Scorer v9.0 → Score All
//
// COLUMNS:
//   A = Ticker    B = Category    C = Subcategory    D = Focus    E = Notes
//   F = Score     G = Type        H = Drivers        I = Risk
//   J = Beta      K = EarningsDate   L = EarningsScore   M = EarningsSummary
//   N = Timestamp    O = Validation   P = DataSource
// ============================================================================

const CONFIG = {
  MODEL: 'grok-4-1-fast-reasoning',
  API_KEY: 'YOUR_GROK_API_KEY_HERE',  // Get your key from https://console.x.ai/
  BASE_URL: 'https://api.x.ai/v1/chat/completions',
  SLEEP_MS: 5000,
  MAX_RUNTIME_MS: 5.5 * 60 * 1000,
  MAX_RETRIES: 2,

  // Column configuration (main sheet)
  COL_TICKER: 1,            // A
  COL_SCORE: 6,             // F
  COL_TYPE: 7,              // G
  COL_DRIVERS: 8,           // H
  COL_RISK: 9,              // I
  COL_BETA: 10,             // J
  COL_EARNINGS_DATE: 11,    // K
  COL_EARNINGS_SCORE: 12,   // L
  COL_EARNINGS_SUMMARY: 13, // M
  COL_TIMESTAMP: 14,        // N
  COL_VALIDATION: 15,       // O
  COL_DATA_SOURCE: 16,      // P (NEW: shows data freshness)

  // Helper tab names
  TECH_DATA_TAB: 'Tech_Data',
  TRANSCRIPTS_TAB: 'Transcripts',
  
  // Data freshness threshold (hours)
  DATA_FRESHNESS_HOURS: 24
};

// ============================================================================
// DATA LOOKUP FUNCTIONS (NEW in v9.0)
// ============================================================================

/**
 * Load all tech data from Tech_Data tab into a lookup map
 * @returns {Object} Map of ticker -> technical data object
 */
function loadTechDataMap() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(CONFIG.TECH_DATA_TAB);
  
  if (!sheet) {
    Logger.log('⚠️ Tech_Data tab not found. Run Python loader first.');
    return {};
  }
  
  const data = sheet.getDataRange().getValues();
  if (data.length < 2) {
    Logger.log('⚠️ Tech_Data tab is empty.');
    return {};
  }
  
  const headers = data[0];
  const map = {};
  
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    const ticker = String(row[0] || '').toUpperCase().trim();
    if (!ticker) continue;
    
    const obj = {};
    headers.forEach((h, idx) => {
      obj[h] = row[idx];
    });
    map[ticker] = obj;
  }
  
  Logger.log(`✓ Loaded tech data for ${Object.keys(map).length} tickers`);
  return map;
}

/**
 * Load all transcript data from Transcripts tab into a lookup map
 * @returns {Object} Map of ticker -> transcript data object
 */
function loadTranscriptsMap() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(CONFIG.TRANSCRIPTS_TAB);
  
  if (!sheet) {
    Logger.log('⚠️ Transcripts tab not found. Run Python loader first.');
    return {};
  }
  
  const data = sheet.getDataRange().getValues();
  if (data.length < 2) {
    Logger.log('⚠️ Transcripts tab is empty.');
    return {};
  }
  
  const headers = data[0];
  const map = {};
  
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    const ticker = String(row[0] || '').toUpperCase().trim();
    if (!ticker) continue;
    
    const obj = {};
    headers.forEach((h, idx) => {
      obj[h] = row[idx];
    });
    map[ticker] = obj;
  }
  
  Logger.log(`✓ Loaded transcripts for ${Object.keys(map).length} tickers`);
  return map;
}

/**
 * Check if data is fresh (within threshold hours)
 * @param {string} updatedStr - Date string from Updated column
 * @returns {boolean} True if data is fresh
 */
function isDataFresh(updatedStr) {
  if (!updatedStr) return false;
  
  try {
    const updated = new Date(updatedStr);
    const now = new Date();
    const hoursDiff = (now - updated) / (1000 * 60 * 60);
    return hoursDiff <= CONFIG.DATA_FRESHNESS_HOURS;
  } catch (e) {
    return false;
  }
}

/**
 * Format data freshness for display
 * @param {Object} techData - Tech data object
 * @param {Object} transcriptData - Transcript data object
 * @returns {string} Freshness indicator
 */
function formatDataSource(techData, transcriptData) {
  const parts = [];
  
  if (techData && techData.Status === 'OK') {
    const fresh = isDataFresh(techData.Updated);
    parts.push(`Tech:${fresh ? '✓' : '⚠️'}${techData.Updated || 'N/A'}`);
  } else {
    parts.push('Tech:❌');
  }
  
  if (transcriptData && transcriptData.Status === 'OK') {
    parts.push(`Earn:${transcriptData.Period || 'N/A'}`);
  } else if (transcriptData && transcriptData.Status === 'NO_DATA') {
    parts.push('Earn:N/A');
  } else {
    parts.push('Earn:❌');
  }
  
  return parts.join(' | ');
}

// ============================================================================
// ENHANCED PROMPT BUILDER (NEW in v9.0)
// ============================================================================

/**
 * Build enriched prompt with pre-fetched data
 */
function buildEnrichedPrompt(ticker, today, techData, transcriptData) {
  // Build technical data section
  let techSection = '';
  if (techData && techData.Status === 'OK') {
    techSection = `
=== PRE-CALCULATED TECHNICAL DATA (as of ${techData.Updated || 'unknown'}) ===
Price: $${techData.Price} (${techData['Change%']})
RSI(14): ${techData.RSI}
MACD: ${techData.MACD} / Signal: ${techData.MACD_Signal} / Histogram: ${techData.MACD_Hist}
ADX (trend strength): ${techData.ADX}
Trend Classification: ${techData.Trend}
Moving Averages: SMA20=$${techData.SMA_20}, SMA50=$${techData.SMA_50}, SMA200=$${techData.SMA_200}
Bollinger Bands: Upper=$${techData.BB_Upper}, Lower=$${techData.BB_Lower}
Stochastic: %K=${techData.Stoch_K}, %D=${techData.Stoch_D}
VWAP: $${techData.VWAP}
ATR: ${techData.ATR}
OBV Trend: ${techData.OBV_Trend}
Volatility Regime: ${techData.Volatility}
Divergence: ${techData.Divergence}
Relative Volume: ${techData.Volume_Rel}
52-Week Range: $${techData['52W_Low']} - $${techData['52W_High']}

NOTE: This technical data is PRE-CALCULATED from verified market data. Use these values directly.
`;
  } else {
    techSection = `
=== TECHNICAL DATA ===
No pre-fetched technical data available. Use web search to find current price, RSI, and key levels.
`;
  }

  // Build transcript section
  let transcriptSection = '';
  if (transcriptData && transcriptData.Status === 'OK') {
    transcriptSection = `
=== LATEST EARNINGS TRANSCRIPT (${transcriptData.Period}, reported ${transcriptData.Earnings_Date}) ===
Key Metrics: ${transcriptData.Key_Metrics || 'N/A'}
Guidance: ${transcriptData.Guidance || 'N/A'}
Management Tone: ${transcriptData.Tone || 'N/A'}
Summary: ${transcriptData.Summary || 'N/A'}

NOTE: This earnings data is from the actual transcript. Use it for EarningsScore and EarningsSummary.
`;
  } else if (transcriptData && transcriptData.Status === 'NO_DATA') {
    transcriptSection = `
=== EARNINGS DATA ===
No transcript available for this company. Search for recent earnings results if available.
`;
  } else {
    transcriptSection = `
=== EARNINGS DATA ===
No pre-fetched earnings data. Use web search for recent earnings results.
`;
  }

  return `
You are a quantitative analyst focused on retail investor hype.
Your task is to rate the current retail hype for $${ticker} as of ${today}.

${techSection}
${transcriptSection}

=== YOUR WEB SEARCH TASK ===
Use real-time web search to gather CURRENT SOCIAL/SENTIMENT data:
- Reddit/WSB activity (last 48 hours)
- X/Twitter volume and sentiment
- Options flow (unusual activity)
- Short interest and Reg SHO status
- Retail broker popularity (Robinhood, etc.)
- TikTok/YouTube mentions
- Discord/Telegram coordination

IMPORTANT:
- The technical data above (if provided) is PRE-CALCULATED and verified. Use it directly.
- Focus your web search on SOCIAL and SENTIMENT indicators only.
- For Beta, use the web search to find the current 3-5 year beta from Yahoo Finance or similar.

SCORING SCALE (2025 calibration, integer 10 to 100 only):
10-29: Dead money, mostly institutional, boring sectors like utilities and insurance
30-49: Low retail, classic dividend blue chips, examples: PG, KO, JNJ
50-64: Moderate retail, large liquid tech with broad ownership, examples: AAPL, MSFT, GOOGL
65-75: Active retail, popular growth favorites, examples: PLTR, SOFI, HOOD
76-84: High retail, momentum or cult names, examples: NVDA, TSLA, AMD
85-91: Active meme, frequent WSB buzz, squeeze narratives, elevated options activity
92-96: Hot meme, coordinated raids, high short interest, small or tight float
97-100: Nuclear meme, extreme mania similar to GME January 2021, extremely rare

STEP 1: RATE THE 10 HYPE DIMENSIONS

For each dimension, pick exactly one level:
1) Reddit/WSB last 48h [none | rare | occasional | frequent | dominant]
2) X/Twitter volume [silent | minimal | moderate | active | viral]
3) Options flow today [none | light | moderate | heavy | extreme]
4) Short interest [<5% | 5-15% | 15-25% | 25-40% | >40%]
5) Reg SHO status [no | yes]
6) Retail broker rank [unlisted | low | mid | top100 | top20]
7) Catalyst sensitivity [low | medium | high | extreme]
8) Float size [large | medium | small | micro]
9) TikTok/YouTube [irrelevant | noise | trending | viral]
10) Discord/Telegram [none | quiet | active | coordinated]

STEP 2: COMPUTE HYPE SCORE, TYPE, AND RISK

Type options: [dividend | institutional | thematic | momentum | meme]
Risk options: [Low | Medium | High]

RISK RULES (mandatory):
- If beta >= 1.8: Risk MUST be "High"
- If beta <= 0.9 AND short interest < 5% AND options flow is "none/light" AND Reddit is "none/rare": Risk MUST be "Low"
- If Float is "small" or "micro": Risk CANNOT be "Low"

STEP 3: EARNINGS ANALYSIS

${transcriptData && transcriptData.Status === 'OK' ? 
`Use the pre-fetched earnings data above for your EarningsScore and EarningsSummary.
- EarningsDate: ${transcriptData.Earnings_Date}
- Base your EarningsScore (1-10) on the Key_Metrics, Guidance, and Tone provided.
- Use the pre-fetched Summary as a starting point for EarningsSummary.` :
`Search for the most recent quarterly earnings and provide:
- EarningsDate (YYYY-MM-DD or N/A)
- EarningsScore (1-10 based on results vs expectations, guidance, tone)
- EarningsSummary (3 sentences: metrics vs estimates, key theme, guidance/reaction)`}

EARNINGS SCORE SCALE:
1-2: Disaster, large miss, guidance cut
3-4: Bad, clear miss or lowered guidance
5: Mixed, small beat/miss, neutral
6-7: Good, clean beat, stable guidance
8-9: Great, strong beat, raised guidance
10: Blowout, exceptional results

STEP 4: BETA

Search for the current 3-5 year beta versus S&P 500 from Yahoo Finance or similar.
Return a single number (e.g., 1.23) or N/A.

STEP 5: OUTPUT FORMAT

Return your answer in exactly this format, no extra text:

Score: XX/100
Type: [type]
Drivers: Reddit: <level>; Twitter: <level>; Options: <level>; SI: <level>; RegSHO: <yes/no>; Brokers: <level>; Catalyst: <level>; Float: <size>; TikTok: <level>; Discord: <level>
Risk: [Low | Medium | High]
Beta: X.XX
EarningsDate: YYYY-MM-DD or N/A
EarningsScore: X/10 or N/A
EarningsSummary: [Sentence 1. Sentence 2. Sentence 3.]
`;
}

// ============================================================================
// CORE SCORING FUNCTION (ENHANCED in v9.0)
// ============================================================================

function scoreTickerWithRetry(ticker, apiKey, techDataMap, transcriptsMap) {
  const today = new Date().toISOString().split('T')[0];
  
  // Get pre-fetched data
  const techData = techDataMap[ticker.toUpperCase()] || null;
  const transcriptData = transcriptsMap[ticker.toUpperCase()] || null;
  
  // Log data availability
  if (techData && techData.Status === 'OK') {
    Logger.log(`  📊 Using pre-fetched tech data (${techData.Updated})`);
  } else {
    Logger.log(`  ⚠️ No pre-fetched tech data for ${ticker}`);
  }
  
  if (transcriptData && transcriptData.Status === 'OK') {
    Logger.log(`  📝 Using pre-fetched transcript (${transcriptData.Period})`);
  } else {
    Logger.log(`  ⚠️ No pre-fetched transcript for ${ticker}`);
  }
  
  // Build enriched prompt
  const prompt = buildEnrichedPrompt(ticker, today, techData, transcriptData);
  
  const raw = callGrokWithRetry(prompt, apiKey);

  // Parse all fields
  const scoreMatch = raw.match(/Score:\s*(\d+)\/100/i);
  const typeMatch = raw.match(/Type:\s*(dividend|institutional|thematic|momentum|meme)/i);
  const driversMatch = raw.match(/Drivers:\s*(.+)/i);
  const riskMatch = raw.match(/Risk:\s*(Low|Medium|High)/i);
  const betaMatch = raw.match(/Beta:\s*([Nn]\/[Aa]|[\d.]+)/i);
  const earningsDateMatch = raw.match(/EarningsDate:\s*(\d{4}-\d{2}-\d{2}|N\/A)/i);
  const earningsScoreMatch = raw.match(/EarningsScore:\s*(\d+|N\/A)(?:\/10)?/i);
  const earningsSummaryMatch = raw.match(/EarningsSummary:\s*(.+)/is);

  if (!scoreMatch) {
    throw new Error('Could not parse score from: ' + truncate(raw, 100));
  }

  // Clean earnings summary
  let earningsSummary = 'No summary available';
  if (earningsSummaryMatch) {
    earningsSummary = earningsSummaryMatch[1]
      .trim()
      .replace(/\s+/g, ' ')
      .replace(/\n/g, ' ');
    const sentences = earningsSummary.match(/[^.!?]+[.!?]+/g);
    if (sentences && sentences.length > 3) {
      earningsSummary = sentences.slice(0, 3).join(' ').trim();
    }
  }

  // Beta
  let betaValue = 'N/A';
  if (betaMatch) {
    const betaRaw = betaMatch[1].toUpperCase();
    if (betaRaw === 'N/A') {
      betaValue = 'N/A';
    } else {
      const num = parseFloat(betaRaw);
      betaValue = isNaN(num) ? 'N/A' : num.toFixed(2);
    }
  }

  // EarningsScore
  let earningsScore = 'N/A';
  if (earningsScoreMatch) {
    const esRaw = earningsScoreMatch[1].toUpperCase();
    earningsScore = esRaw === 'N/A' ? 'N/A' : parseInt(esRaw, 10);
  }
  
  // If we have pre-fetched earnings date, prefer it
  let earningsDate = earningsDateMatch ? earningsDateMatch[1] : 'N/A';
  if (transcriptData && transcriptData.Status === 'OK' && transcriptData.Earnings_Date) {
    earningsDate = transcriptData.Earnings_Date;
  }

  return {
    score: parseInt(scoreMatch[1], 10),
    type: typeMatch ? typeMatch[1].toLowerCase() : 'unknown',
    drivers: driversMatch
      ? truncate(driversMatch[1].trim().replace(/\s+/g, ' '), 400)
      : 'No drivers parsed',
    risk: riskMatch ? riskMatch[1] : 'Unknown',
    beta: betaValue,
    earningsDate: earningsDate,
    earningsScore,
    earningsSummary: truncate(earningsSummary, 500),
    dataSource: formatDataSource(techData, transcriptData)
  };
}

// ============================================================================
// API CALL FUNCTIONS
// ============================================================================

function callGrokWithRetry(prompt, apiKey) {
  let lastError;

  for (let attempt = 0; attempt <= CONFIG.MAX_RETRIES; attempt++) {
    try {
      return callGrok(prompt, apiKey);
    } catch (e) {
      lastError = e;
      if (attempt < CONFIG.MAX_RETRIES) {
        Logger.log(`Retry ${attempt + 1} after error: ${e}`);
        Utilities.sleep(3000 * (attempt + 1));
      }
    }
  }
  throw lastError;
}

function callGrok(prompt, apiKey) {
  const url = CONFIG.BASE_URL;

  const payload = {
    model: CONFIG.MODEL,
    messages: [{ role: 'user', content: prompt }],
    temperature: 0.2,
    max_tokens: 2000,
    search: true
  };

  const options = {
    method: 'post',
    contentType: 'application/json',
    headers: {
      Authorization: 'Bearer ' + apiKey
    },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };

  const response = UrlFetchApp.fetch(url, options);
  const status = response.getResponseCode();
  const text = response.getContentText();

  if (status === 429) {
    throw new Error('Rate limited, wait and retry');
  }
  if (status !== 200) {
    throw new Error(`API ${status}: ${truncate(text, 100)}`);
  }

  const json = JSON.parse(text);

  if (json.error) {
    throw new Error(json.error.message);
  }

  if (!json.choices?.[0]?.message?.content) {
    throw new Error('Empty response from API');
  }

  incrementDailyCount();

  if (json.usage) {
    Logger.log(
      `Tokens, prompt: ${json.usage.prompt_tokens}, completion: ${json.usage.completion_tokens}`
    );
  }

  return json.choices[0].message.content.trim();
}

// ============================================================================
// MAIN SCORER (ENHANCED in v9.0)
// ============================================================================

function GROK_HYPE_SCORER() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const apiKey = CONFIG.API_KEY;
  const startTime = Date.now();

  // Daily limit check
  const dailyCount = getDailyRequestCount();
  if (dailyCount >= 950) {
    const ui = SpreadsheetApp.getUi();
    const resp = ui.alert(
      '⚠️ Rate Limit Warning',
      `You have made ${dailyCount} API calls today.\n\nContinue anyway?`,
      ui.ButtonSet.YES_NO
    );
    if (resp !== ui.Button.YES) return;
  }

  const lastRow = sheet.getLastRow();
  if (lastRow < 2) {
    showStatus('No tickers found. Add tickers in column A starting row 2.');
    return;
  }

  // Load pre-fetched data (NEW in v9.0)
  Logger.log('Loading pre-fetched data from helper tabs...');
  const techDataMap = loadTechDataMap();
  const transcriptsMap = loadTranscriptsMap();
  
  const hasTechData = Object.keys(techDataMap).length > 0;
  const hasTranscripts = Object.keys(transcriptsMap).length > 0;
  
  if (!hasTechData && !hasTranscripts) {
    const ui = SpreadsheetApp.getUi();
    const resp = ui.alert(
      '⚠️ No Pre-fetched Data',
      'Tech_Data and Transcripts tabs are empty or missing.\n\n' +
      'For best results, run the Python loader first:\n' +
      '  python sheet_data_loader.py\n\n' +
      'Continue with web search only?',
      ui.ButtonSet.YES_NO
    );
    if (resp !== ui.Button.YES) return;
  }

  let processed = 0;
  let skipped = 0;
  let errors = 0;

  for (let row = 2; row <= lastRow; row++) {
    if (Date.now() - startTime > CONFIG.MAX_RUNTIME_MS) {
      showStatus(
        `⏱️ Timeout at row ${row}. Processed: ${processed}, Errors: ${errors}. Run again to continue.`
      );
      return;
    }

    const ticker = sheet
      .getRange(row, CONFIG.COL_TICKER)
      .getValue()
      ?.toString()
      .trim()
      .toUpperCase();
    const existingScore = sheet.getRange(row, CONFIG.COL_SCORE).getValue();

    if (!ticker) {
      skipped++;
      continue;
    }
    if (
      existingScore !== '' &&
      existingScore !== 'ERROR' &&
      existingScore !== 'RETRY' &&
      existingScore !== '⏳'
    ) {
      skipped++;
      continue;
    }

    sheet.getRange(row, CONFIG.COL_SCORE).setValue('⏳');
    SpreadsheetApp.flush();

    try {
      const result = scoreTickerWithRetry(ticker, apiKey, techDataMap, transcriptsMap);

      sheet.getRange(row, CONFIG.COL_SCORE).setValue(result.score);
      sheet.getRange(row, CONFIG.COL_TYPE).setValue(result.type);
      sheet.getRange(row, CONFIG.COL_DRIVERS).setValue(result.drivers);
      sheet.getRange(row, CONFIG.COL_RISK).setValue(result.risk);
      sheet.getRange(row, CONFIG.COL_BETA).setValue(result.beta);
      sheet.getRange(row, CONFIG.COL_EARNINGS_DATE).setValue(result.earningsDate);
      sheet.getRange(row, CONFIG.COL_EARNINGS_SCORE).setValue(result.earningsScore);
      sheet.getRange(row, CONFIG.COL_EARNINGS_SUMMARY).setValue(result.earningsSummary);
      sheet.getRange(row, CONFIG.COL_TIMESTAMP).setValue(new Date());
      sheet.getRange(row, CONFIG.COL_DATA_SOURCE).setValue(result.dataSource);
      sheet.getRange(row, CONFIG.COL_TICKER).setFontColor('#0b8043');

      processed++;
      Logger.log(
        `✓ ${ticker}: ${result.score}/100 [${result.type}] Beta:${result.beta} Earn:${result.earningsScore}/10`
      );

      Utilities.sleep(CONFIG.SLEEP_MS);
    } catch (e) {
      sheet.getRange(row, CONFIG.COL_SCORE).setValue('ERROR');
      sheet.getRange(row, CONFIG.COL_DRIVERS).setValue(truncate(e.toString(), 100));
      sheet.getRange(row, CONFIG.COL_TICKER).setFontColor('#cc0000');
      errors++;
      Logger.log(`✗ ${ticker}: ${e}`);
    }
  }

  sortByScore(sheet);
  showStatus(`✅ Done. Processed: ${processed}, Skipped: ${skipped}, Errors: ${errors}`);
}

// ============================================================================
// TEST MODE (ENHANCED in v9.0)
// ============================================================================

function TEST_HYPE_SCORER() {
  const testTickers = ['GME', 'AAPL', 'PLTR', 'PG', 'NVDA'];
  const apiKey = CONFIG.API_KEY;

  Logger.log('='.repeat(60));
  Logger.log('TEST MODE - v9.0 with PRE-FETCHED DATA + WEB SEARCH');
  Logger.log('Model: ' + CONFIG.MODEL);
  Logger.log('='.repeat(60));

  // Load pre-fetched data
  const techDataMap = loadTechDataMap();
  const transcriptsMap = loadTranscriptsMap();
  
  Logger.log(`Tech data available for: ${Object.keys(techDataMap).join(', ') || 'none'}`);
  Logger.log(`Transcripts available for: ${Object.keys(transcriptsMap).join(', ') || 'none'}`);

  const results = [];

  const expectedRanges = {
    GME: [85, 96],
    AAPL: [50, 65],
    PLTR: [65, 80],
    PG: [20, 40],
    NVDA: [75, 88]
  };

  for (const ticker of testTickers) {
    Logger.log('\n' + '-'.repeat(40));
    Logger.log(`SCORING: $${ticker}`);
    Logger.log('-'.repeat(40));

    try {
      const startTime = Date.now();
      const result = scoreTickerWithRetry(ticker, apiKey, techDataMap, transcriptsMap);
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);

      const expected = expectedRanges[ticker];
      let calibrationNote = '';
      if (result.score < expected[0]) {
        calibrationNote = ` ⚠️ LOW (expected ${expected[0]}-${expected[1]})`;
      } else if (result.score > expected[1]) {
        calibrationNote = ` ⚠️ HIGH (expected ${expected[0]}-${expected[1]})`;
      } else {
        calibrationNote = ` ✓ In range`;
      }

      Logger.log(`✓ Score: ${result.score}/100${calibrationNote}`);
      Logger.log(`✓ Type: ${result.type}`);
      Logger.log(`✓ Drivers: ${result.drivers}`);
      Logger.log(`✓ Risk: ${result.risk}`);
      Logger.log(`✓ Beta: ${result.beta}`);
      Logger.log(`✓ Earnings Date: ${result.earningsDate}`);
      Logger.log(`✓ Earnings Score: ${result.earningsScore}/10`);
      Logger.log(`✓ Earnings Summary: ${result.earningsSummary}`);
      Logger.log(`✓ Data Source: ${result.dataSource}`);
      Logger.log(`✓ Time: ${elapsed}s`);

      results.push({
        ticker,
        score: result.score,
        type: result.type,
        risk: result.risk,
        beta: result.beta,
        earningsScore: result.earningsScore,
        dataSource: result.dataSource,
        status: 'OK',
        calibration: calibrationNote
      });

      Utilities.sleep(CONFIG.SLEEP_MS);
    } catch (e) {
      Logger.log(`✗ ERROR: ${e.toString()}`);
      results.push({
        ticker,
        score: 'ERR',
        type: '',
        risk: '',
        beta: '',
        earningsScore: '',
        dataSource: '',
        status: 'FAIL',
        calibration: ''
      });
    }
  }

  Logger.log('\n' + '='.repeat(60));
  Logger.log('TEST RESULTS SUMMARY');
  Logger.log('='.repeat(60));

  for (const r of results) {
    Logger.log(
      `${r.ticker}: ${r.score}/100 [${r.type}] Risk:${r.risk} Beta:${r.beta} Earn:${r.earningsScore}${r.calibration}`
    );
  }

  const successCount = results.filter(r => r.status === 'OK').length;
  const inRangeCount = results.filter(r => r.calibration.includes('In range')).length;

  Logger.log('\n' + '-'.repeat(40));
  Logger.log(`Success: ${successCount}/${results.length}`);
  Logger.log(`Calibration: ${inRangeCount}/${successCount} in expected range`);
  Logger.log('-'.repeat(40));

  const ui = SpreadsheetApp.getUi();
  const summary = results
    .map(r => `${r.ticker}: ${r.score} [${r.type}] ${r.dataSource}${r.calibration}`)
    .join('\n');
  ui.alert(
    'Test Complete (v9.0)',
    `Results:\n${summary}\n\nView > Logs for full output.`,
    ui.ButtonSet.OK
  );
}

// ============================================================================
// VALIDATION PASS
// ============================================================================

function VALIDATE_HYPE_SCORES() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const apiKey = CONFIG.API_KEY;
  const startTime = Date.now();

  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return;

  // Load tech data for validation comparison
  const techDataMap = loadTechDataMap();

  let validated = 0;

  for (let row = 2; row <= lastRow; row++) {
    if (Date.now() - startTime > CONFIG.MAX_RUNTIME_MS) {
      showStatus(`⏱️ Validation timeout at row ${row}. Run again to continue.`);
      return;
    }

    const ticker = sheet
      .getRange(row, CONFIG.COL_TICKER)
      .getValue()
      ?.toString()
      .trim();
    const score = sheet.getRange(row, CONFIG.COL_SCORE).getValue();
    const type = sheet.getRange(row, CONFIG.COL_TYPE).getValue();
    const beta = sheet.getRange(row, CONFIG.COL_BETA).getValue();
    const earningsScore = sheet.getRange(row, CONFIG.COL_EARNINGS_SCORE).getValue();
    const existingValidation = sheet.getRange(row, CONFIG.COL_VALIDATION).getValue();

    if (!ticker || typeof score !== 'number' || existingValidation !== '') {
      continue;
    }

    sheet.getRange(row, CONFIG.COL_VALIDATION).setValue('⏳');
    SpreadsheetApp.flush();

    try {
      // Include tech data in validation if available
      const techData = techDataMap[ticker.toUpperCase()] || null;
      const validation = validateScore(ticker, score, type, beta, earningsScore, techData, apiKey);
      sheet.getRange(row, CONFIG.COL_VALIDATION).setValue(validation);
      validated++;

      Utilities.sleep(CONFIG.SLEEP_MS);
    } catch (e) {
      sheet
        .getRange(row, CONFIG.COL_VALIDATION)
        .setValue('ERR: ' + truncate(e.toString(), 40));
    }
  }

  showStatus(`✅ Validation complete. Checked: ${validated} stocks`);
}

function validateScore(ticker, score, type, beta, earningsScore, techData, apiKey) {
  let techContext = '';
  if (techData && techData.Status === 'OK') {
    techContext = `
Pre-fetched technical data available:
- RSI: ${techData.RSI}
- Trend: ${techData.Trend}
- ADX: ${techData.ADX}
`;
  }
  
  const prompt = `
You are verifying a previously computed retail hype score for $${ticker}.

Claimed values:
- Hype score: ${score}/100
- Type: ${type}
- Beta: ${beta}
- Earnings score: ${earningsScore}/10
${techContext}

Use real-time web search to check:
1) Whether the beta is correct (compare to Yahoo Finance).
2) Whether the hype score seems reasonable given current social activity.
3) Whether the earnings score matches recent results.

If everything is reasonable, reply with: ✓ OK
If there is any issue, reply with: ⚠️ <specific issue>

Output exactly one line.
`;

  const raw = callGrokWithRetry(prompt, apiKey);

  const lines = raw.split('\n').filter(l => l.trim());
  for (const line of lines) {
    if (line.includes('✓') || line.includes('⚠️')) {
      return truncate(line.trim(), 100);
    }
  }
  return truncate(raw, 100);
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

function sortByScore(sheet) {
  const lastRow = sheet.getLastRow();
  if (lastRow < 3) return;

  const numCols = Math.max(sheet.getLastColumn(), CONFIG.COL_DATA_SOURCE);
  const range = sheet.getRange(2, 1, lastRow - 1, numCols);

  const scores = sheet
    .getRange(2, CONFIG.COL_SCORE, lastRow - 1, 1)
    .getValues()
    .flat();
  const hasNumericScores = scores.some(s => typeof s === 'number');

  if (hasNumericScores) {
    range.sort({ column: CONFIG.COL_SCORE, ascending: false });
    Logger.log('Sorted by score descending');
  }
}

function getDailyRequestCount() {
  const props = PropertiesService.getScriptProperties();
  const today = new Date().toDateString();
  const stored = props.getProperty('DAILY_COUNT_DATE');

  if (stored !== today) {
    props.setProperty('DAILY_COUNT_DATE', today);
    props.setProperty('DAILY_COUNT', '0');
    return 0;
  }
  return parseInt(props.getProperty('DAILY_COUNT') || '0', 10);
}

function incrementDailyCount() {
  const props = PropertiesService.getScriptProperties();
  const count = getDailyRequestCount() + 1;
  props.setProperty('DAILY_COUNT', count.toString());
  return count;
}

function truncate(str, len) {
  if (!str) return '';
  str = str.toString();
  return str.length > len ? str.slice(0, len - 3) + '...' : str;
}

function showStatus(message) {
  SpreadsheetApp.getActiveSpreadsheet().toast(message, 'Hype Scorer v9.0', 10);
  Logger.log(message);
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function CLEAR_SCORES() {
  const ui = SpreadsheetApp.getUi();
  const response = ui.alert(
    'Clear All Scores?',
    'This will clear columns F-P (all scoring data) but keep ticker info.',
    ui.ButtonSet.YES_NO
  );

  if (response !== ui.Button.YES) return;

  const sheet = SpreadsheetApp.getActiveSheet();
  const lastRow = sheet.getLastRow();

  if (lastRow > 1) {
    // Clear F through P (columns 6-16 = 11 columns)
    sheet.getRange(2, CONFIG.COL_SCORE, lastRow - 1, 11).clearContent();
    sheet.getRange(2, CONFIG.COL_TICKER, lastRow - 1, 1).setFontColor('#000000');
  }

  showStatus('Cleared all scores. Ready to re-run.');
}

function CHECK_DATA_FRESHNESS() {
  const techMap = loadTechDataMap();
  const transMap = loadTranscriptsMap();
  
  const techCount = Object.keys(techMap).length;
  const transCount = Object.keys(transMap).length;
  
  let staleCount = 0;
  for (const ticker in techMap) {
    if (!isDataFresh(techMap[ticker].Updated)) {
      staleCount++;
    }
  }
  
  const ui = SpreadsheetApp.getUi();
  ui.alert(
    'Data Freshness Check',
    `Tech_Data: ${techCount} tickers (${staleCount} stale)\n` +
    `Transcripts: ${transCount} tickers\n\n` +
    `Data is considered stale after ${CONFIG.DATA_FRESHNESS_HOURS} hours.\n` +
    `Run Python loader to refresh: python sheet_data_loader.py`,
    ui.ButtonSet.OK
  );
}

// ============================================================================
// MENU
// ============================================================================

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('🚀 Hype Scorer v9.0')
    .addItem('🧪 Test (5 tickers)', 'TEST_HYPE_SCORER')
    .addSeparator()
    .addItem('▶️ Score All Tickers', 'GROK_HYPE_SCORER')
    .addItem('✓ Validate Scores', 'VALIDATE_HYPE_SCORES')
    .addSeparator()
    .addItem('📊 Check Data Freshness', 'CHECK_DATA_FRESHNESS')
    .addItem('📈 Check API Usage', 'CHECK_DAILY_USAGE')
    .addItem('🗑️ Clear All Scores', 'CLEAR_SCORES')
    .addToUi();
}

function CHECK_DAILY_USAGE() {
  const count = getDailyRequestCount();
  SpreadsheetApp.getUi().alert(
    'API Usage Today',
    `Requests made: ${count}\nRemaining: ${1000 - count}`,
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}
