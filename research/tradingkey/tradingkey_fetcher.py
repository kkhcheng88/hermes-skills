"""
TradingKey Data Fetcher for CIO Engine
Production-ready module for fetching stock analysis and news from TradingKey.
"""
import urllib.request
import json
import re
import sys
import os
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8', errors='replace')


class TradingKeyFetcher:
    """Fetch stock analysis and news from TradingKey.com"""
    
    BASE_URL = "https://api.tradingkey.com"
    WEB_URL = "https://www.tradingkey.com"
    
    def __init__(self, symbol: str):
        self.symbol = symbol.upper()
        self.route = f"nasdaq-{symbol.lower()}"
    
    def _make_request(self, url: str, headers: dict = None) -> str:
        """Make HTTP request with proper headers"""
        if headers is None:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Referer': f'{self.WEB_URL}/',
            }
        req = urllib.request.Request(url, headers=headers)
        return urllib.request.urlopen(req, timeout=15).read().decode('utf-8')
    
    def get_stock_analysis(self) -> dict:
        """
        Fetch comprehensive stock analysis from TradingKey API.
        Returns: dict with score, suggests, labels, support/resistance, sentiment, agency rating
        """
        url = f"{self.BASE_URL}/quotes-base/diagnosis/v1/stock-score?route={self.route}"
        data = json.loads(self._make_request(url))
        return data.get('value', {})
    
    def get_news(self, limit: int = 6) -> dict:
        """
        Fetch stock-specific news from TradingKey SSR HTML.
        Returns: dict with list of articles and total count
        """
        url = f"{self.WEB_URL}/zh-hant/markets/stocks/{self.route}"
        html = self._make_request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html',
        })
        
        # Extract newsRelatedArticleData from SSR HTML
        marker = '"newsRelatedArticleData":{'
        idx = html.find(marker)
        if idx == -1:
            return {"list": [], "total": "0"}
        
        start = idx + len(marker) - 1
        depth = 0
        for i in range(start, len(html)):
            if html[i] == '{': 
                depth += 1
            if html[i] == '}':
                depth -= 1
                if depth == 0: 
                    break
        
        json_str = html[start:i+1]
        news_data = json.loads(json_str)
        
        # Limit articles
        news_data['list'] = news_data.get('list', [])[:limit]
        return news_data
    
    def get_article_content(self, article_route: str) -> str:
        """Fetch full article content by route slug"""
        url = f"{self.WEB_URL}/zh-hant/analysis/stocks/us-stock/{article_route}"
        html = self._make_request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html',
        })
        
        marker = '"content":"'
        idx = html.find(marker)
        if idx == -1:
            return None
        
        start = idx + len(marker)
        end = html.find('",', start)
        content = html[start:end]
        content = content.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
        return content
    
    def fetch_all(self, save_dir: str = None) -> dict:
        """
        Fetch all available data for the stock.
        Returns combined analysis + news data
        """
        result = {
            'symbol': self.symbol,
            'fetched_at': datetime.now().isoformat(),
        }
        
        # Get analysis
        try:
            result['analysis'] = self.get_stock_analysis()
        except Exception as e:
            result['analysis_error'] = str(e)
        
        # Get news
        try:
            result['news'] = self.get_news()
        except Exception as e:
            result['news_error'] = str(e)
        
        # Save if directory provided
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
            with open(f'{save_dir}/tradingkey_analysis.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"Saved to {save_dir}/tradingkey_analysis.json")
        
        return result
    
    def print_summary(self, data: dict):
        """Print human-readable summary of fetched data"""
        print(f"\n{'='*50}")
        print(f"TradingKey Analysis: {self.symbol}")
        print(f"{'='*50}")
        
        # Analysis
        if 'analysis' in data:
            v = data['analysis']
            s = v.get('score', {})
            
            print(f"\n[Score] Total: {s.get('totalScore', 'N/A')}/10")
            print(f"[Score] Industry: {s.get('industryRank', 'N/A')}/{s.get('industryTotal', 'N/A')}")
            print(f"[Score] Market: {s.get('marketRank', 'N/A')}/{s.get('marketTotal', 'N/A')}")
            print(f"[Score] Date: {s.get('countDate', 'N/A')}")
            
            print(f"\n[Dimensions]")
            dims = [
                ('revenueForecasts', 'Revenue Forecasts'),
                ('financialDiagnostics', 'Financial Diagnostics'),
                ('priceMomentum', 'Price Momentum'),
                ('riskAssessment', 'Risk Assessment'),
                ('institutionalRecognition', 'Institutional Recognition'),
                ('companyValuation', 'Company Valuation'),
            ]
            for key, name in dims:
                score = s.get(key, 'N/A')
                print(f"  {name}: {score}/10")
            
            print(f"\n[Support/Resistance]")
            print(f"  Resistance: {v.get('pressure', 'N/A')}")
            print(f"  Support: {v.get('support', 'N/A')}")
            
            print(f"\n[Sentiment]")
            cs = v.get('companySentiment', {})
            print(f"  Sentiment: {cs.get('companySentiment', 'N/A')}")
            print(f"  Hot Score: {cs.get('companyHot', 'N/A')}")
            
            print(f"\n[Agency Rating]")
            ar = v.get('agencyRating', {})
            print(f"  Rating: {ar.get('rating', 'N/A')}")
            print(f"  Target Price: {ar.get('targetPrice', 'N/A')}")
            print(f"  Price Space: {ar.get('priceSpace', 'N/A')}%")
            print(f"  Analysts: {ar.get('total', 'N/A')}")
            
            print(f"\n[Labels]")
            for item in v.get('labelList', []):
                lt = '[POSITIVE]' if item['labelType'] == 1 else '[NEGATIVE]'
                print(f"  {lt} {item['title']}")
            
            print(f"\n[Stock Suggest]")
            print(f"  {v.get('suggests', {}).get('stockSuggest', 'N/A')[:300]}...")
        
        # News
        if 'news' in data:
            news = data['news']
            print(f"\n[News] Total: {news.get('total', 'N/A')} articles")
            for i, a in enumerate(news.get('list', []), 1):
                print(f"\n  {i}. {a.get('title', 'N/A')[:80]}")
                print(f"     {a.get('description', 'N/A')[:100]}...")
        
        print(f"\n{'='*50}")
        print(f"Fetched at: {data.get('fetched_at', 'N/A')}")
        print(f"{'='*50}\n")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Fetch TradingKey data for a stock')
    parser.add_argument('symbol', help='Stock symbol (e.g., TSLA)')
    parser.add_argument('--save', help='Directory to save data')
    args = parser.parse_args()
    
    fetcher = TradingKeyFetcher(args.symbol)
    data = fetcher.fetch_all(save_dir=args.save)
    fetcher.print_summary(data)


if __name__ == '__main__':
    main()
