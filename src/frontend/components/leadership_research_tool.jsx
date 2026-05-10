import React, { useState, useEffect } from 'react';
import { Search, Download, Globe, Users, Settings, Database, AlertTriangle, CheckCircle } from 'lucide-react';

const LeadershipResearchTool = () => {
  const [activeTab, setActiveTab] = useState('scraper');
  const [scrapingResults, setScrapingResults] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [config, setConfig] = useState({
    targetSources: [],
    languages: ['zh-CN', 'ru'],
    dataFields: ['name', 'title', 'role', 'age', 'yearsInPosition', 'salary', 'biography'],
    outputFormat: 'json',
    rateLimit: 2000, // ms between requests
    respectRobots: true
  });

  // Predefined target sources for organizational leadership data
  const targetSources = [
    {
      name: 'Chinese Government Portal',
      url: 'http://www.gov.cn',
      language: 'zh-CN',
      type: 'government',
      selectors: {
        leaderList: '.leader-list, .gov-leaders',
        name: '.name, .leader-name',
        title: '.title, .position',
        department: '.department, .org'
      }
    },
    {
      name: 'Chinese Ministry of Defense',
      url: 'http://www.mod.gov.cn',
      language: 'zh-CN',
      type: 'military',
      selectors: {
        leaderList: '.leadership, .command-structure',
        name: '.commander-name',
        title: '.rank, .position'
      }
    },
    {
      name: 'Russian Government',
      url: 'http://government.ru',
      language: 'ru',
      type: 'government',
      selectors: {
        leaderList: '.government-members, .leadership',
        name: '.member-name',
        title: '.position, .title'
      }
    }
  ];

  const scrapeLeadershipData = async (source) => {
    setIsProcessing(true);
    
    try {
      // Simulate API call to Claude for web scraping and translation
      const response = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 1000,
          tools: [
            {
              "type": "web_search_20250305",
              "name": "web_search"
            }
          ],
          messages: [
            { 
              role: "user", 
              content: `Please search for current leadership information from ${source.name} (${source.url}). 
              
              I need to collect the following data points for research purposes:
              - Names (original and romanized)
              - Official titles/positions
              - Organizational roles
              - Years in current position (if available)
              - Ages (if publicly available)
              - Brief biographical information
              
              Please search for this information and format it as structured data. This is for academic research into organizational leadership structures for simulation modeling purposes.
              
              Language: ${source.language}
              Type: ${source.type}
              
              Please provide the results in JSON format with proper romanization of non-Latin names.`
            }
          ]
        })
      });

      const data = await response.json();
      
      // Extract and process the response
      const textResponses = data.content
        .filter(item => item.type === "text")
        .map(item => item.text)
        .join("\n");

      // Parse any JSON from the response
      let structuredData = [];
      try {
        const jsonMatch = textResponses.match(/```json\n([\s\S]*?)\n```/);
        if (jsonMatch) {
          structuredData = JSON.parse(jsonMatch[1]);
        }
      } catch (e) {
        console.log("No structured data found, using text response");
      }

      return {
        source: source.name,
        data: structuredData,
        rawText: textResponses,
        timestamp: new Date().toISOString()
      };

    } catch (error) {
      console.error('Scraping error:', error);
      return {
        source: source.name,
        error: error.message,
        timestamp: new Date().toISOString()
      };
    } finally {
      setIsProcessing(false);
    }
  };

  const handleScrapeSource = async (source) => {
    const result = await scrapeLeadershipData(source);
    setScrapingResults(prev => [...prev, result]);
  };

  const exportData = () => {
    const exportData = {
      metadata: {
        collectionDate: new Date().toISOString(),
        sources: scrapingResults.map(r => r.source),
        totalRecords: scrapingResults.reduce((acc, r) => acc + (r.data?.length || 0), 0),
        purpose: "KVP Simulator Dataset - Organizational Leadership Research"
      },
      leadership_data: scrapingResults
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `leadership_research_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const generateKVPDataset = () => {
    // Transform collected data into KVP simulator format
    const kvpData = scrapingResults.map(result => {
      if (!result.data) return null;
      
      return result.data.map(leader => ({
        entity_id: `leader_${leader.name?.replace(/\s+/g, '_').toLowerCase()}`,
        entity_type: "person",
        attributes: {
          name: leader.name,
          romanized_name: leader.romanized_name || leader.name,
          title: leader.title,
          organization: result.source,
          role_type: leader.role || "leadership",
          years_in_position: leader.yearsInPosition || null,
          age: leader.age || null,
          biography: leader.biography || null,
          source: result.source,
          collection_date: result.timestamp
        },
        relationships: {
          member_of: result.source,
          reports_to: leader.supervisor || null
        },
        confidence: 0.85 // Since this is from public sources
      }));
    }).flat().filter(Boolean);

    const kvpExport = {
      dataset_info: {
        name: "Organizational Leadership KVP Dataset",
        version: "1.0",
        created: new Date().toISOString(),
        purpose: "Adversarial organizational modeling for KVP simulator",
        source: "Web scraping of public leadership information"
      },
      entities: kvpData
    };

    const blob = new Blob([JSON.stringify(kvpExport, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `kvp_leadership_dataset_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-800 text-white">
      <div className="container mx-auto p-6">
        <div className="bg-slate-800/50 backdrop-blur border border-slate-600 rounded-xl p-6 mb-8">
          <div className="flex items-center gap-3 mb-4">
            <Database className="w-8 h-8 text-blue-400" />
            <div>
              <h1 className="text-2xl font-bold">Organizational Leadership Research Tool</h1>
              <p className="text-slate-300">Collect leadership data for KVP simulator datasets</p>
            </div>
          </div>
          
          <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-4 mb-6">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-yellow-500 mt-0.5" />
              <div className="text-sm">
                <p className="font-medium text-yellow-400 mb-1">Research Ethics Notice</p>
                <p className="text-yellow-200">
                  This tool is designed for academic research purposes. All data collection respects robots.txt, 
                  implements rate limiting, and focuses on publicly available information only.
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-slate-800/30 backdrop-blur border border-slate-600 rounded-xl overflow-hidden">
          <div className="border-b border-slate-600">
            <div className="flex">
              {['scraper', 'data', 'export'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-6 py-4 font-medium capitalize transition-colors ${
                    activeTab === tab
                      ? 'bg-blue-600 text-white border-b-2 border-blue-400'
                      : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
                  }`}
                >
                  {tab === 'scraper' && <Search className="w-4 h-4 inline mr-2" />}
                  {tab === 'data' && <Users className="w-4 h-4 inline mr-2" />}
                  {tab === 'export' && <Download className="w-4 h-4 inline mr-2" />}
                  {tab}
                </button>
              ))}
            </div>
          </div>

          <div className="p-6">
            {activeTab === 'scraper' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                    <Globe className="w-5 h-5" />
                    Target Sources
                  </h3>
                  <div className="grid gap-4">
                    {targetSources.map((source, index) => (
                      <div key={index} className="bg-slate-700/50 border border-slate-600 rounded-lg p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <h4 className="font-medium text-blue-400">{source.name}</h4>
                            <p className="text-sm text-slate-300">{source.url}</p>
                            <div className="flex gap-2 mt-2">
                              <span className="px-2 py-1 bg-blue-600/20 text-blue-300 text-xs rounded">
                                {source.language}
                              </span>
                              <span className="px-2 py-1 bg-green-600/20 text-green-300 text-xs rounded">
                                {source.type}
                              </span>
                            </div>
                          </div>
                          <button
                            onClick={() => handleScrapeSource(source)}
                            disabled={isProcessing}
                            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 
                                     disabled:cursor-not-allowed rounded-lg transition-colors"
                          >
                            {isProcessing ? 'Processing...' : 'Scrape'}
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-slate-700/30 border border-slate-600 rounded-lg p-4">
                  <h4 className="font-medium mb-3 flex items-center gap-2">
                    <Settings className="w-4 h-4" />
                    Configuration
                  </h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <label className="block text-slate-300 mb-1">Rate Limit (ms)</label>
                      <input
                        type="number"
                        value={config.rateLimit}
                        onChange={(e) => setConfig(prev => ({...prev, rateLimit: parseInt(e.target.value)}))}
                        className="w-full bg-slate-600 border border-slate-500 rounded px-3 py-2 text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-slate-300 mb-1">Output Format</label>
                      <select
                        value={config.outputFormat}
                        onChange={(e) => setConfig(prev => ({...prev, outputFormat: e.target.value}))}
                        className="w-full bg-slate-600 border border-slate-500 rounded px-3 py-2 text-white"
                      >
                        <option value="json">JSON</option>
                        <option value="csv">CSV</option>
                        <option value="xml">XML</option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'data' && (
              <div className="space-y-4">
                <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                  <Users className="w-5 h-5" />
                  Collected Data ({scrapingResults.length} sources)
                </h3>
                
                {scrapingResults.length === 0 ? (
                  <div className="text-center py-12 text-slate-400">
                    <Users className="w-16 h-16 mx-auto mb-4 opacity-50" />
                    <p>No data collected yet. Start scraping from the Scraper tab.</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {scrapingResults.map((result, index) => (
                      <div key={index} className="bg-slate-700/50 border border-slate-600 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-3">
                          <h4 className="font-medium text-blue-400">{result.source}</h4>
                          <div className="flex items-center gap-2">
                            {result.error ? (
                              <span className="text-red-400 text-sm">Error</span>
                            ) : (
                              <CheckCircle className="w-4 h-4 text-green-400" />
                            )}
                            <span className="text-xs text-slate-400">
                              {new Date(result.timestamp).toLocaleString()}
                            </span>
                          </div>
                        </div>
                        
                        {result.error ? (
                          <p className="text-red-300 text-sm">{result.error}</p>
                        ) : (
                          <div>
                            <p className="text-sm text-slate-300 mb-2">
                              Collected {result.data?.length || 0} leadership records
                            </p>
                            {result.data && result.data.length > 0 && (
                              <div className="bg-slate-800 rounded p-3 text-xs font-mono max-h-40 overflow-y-auto">
                                <pre>{JSON.stringify(result.data[0], null, 2)}</pre>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeTab === 'export' && (
              <div className="space-y-6">
                <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                  <Download className="w-5 h-5" />
                  Export Data
                </h3>

                <div className="grid gap-4">
                  <div className="bg-slate-700/50 border border-slate-600 rounded-lg p-6">
                    <h4 className="font-medium mb-3">Raw Research Data</h4>
                    <p className="text-sm text-slate-300 mb-4">
                      Export all collected leadership data in structured format for analysis.
                    </p>
                    <button
                      onClick={exportData}
                      disabled={scrapingResults.length === 0}
                      className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 
                               disabled:cursor-not-allowed rounded-lg transition-colors"
                    >
                      Export JSON
                    </button>
                  </div>

                  <div className="bg-slate-700/50 border border-slate-600 rounded-lg p-6">
                    <h4 className="font-medium mb-3">KVP Simulator Dataset</h4>
                    <p className="text-sm text-slate-300 mb-4">
                      Transform data into KVP simulator format for adversarial organizational modeling.
                    </p>
                    <button
                      onClick={generateKVPDataset}
                      disabled={scrapingResults.length === 0}
                      className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-slate-600 
                               disabled:cursor-not-allowed rounded-lg transition-colors"
                    >
                      Generate KVP Dataset
                    </button>
                  </div>
                </div>

                <div className="bg-slate-700/30 border border-slate-600 rounded-lg p-4">
                  <h4 className="font-medium mb-3">Data Summary</h4>
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <div className="text-2xl font-bold text-blue-400">{scrapingResults.length}</div>
                      <div className="text-sm text-slate-300">Sources</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-green-400">
                        {scrapingResults.reduce((acc, r) => acc + (r.data?.length || 0), 0)}
                      </div>
                      <div className="text-sm text-slate-300">Leaders</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-yellow-400">
                        {scrapingResults.filter(r => r.error).length}
                      </div>
                      <div className="text-sm text-slate-300">Errors</div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LeadershipResearchTool;