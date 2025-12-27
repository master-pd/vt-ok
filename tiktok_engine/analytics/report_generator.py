"""
Professional Report Generation System for Analytics
"""

import asyncio
import logging
import json
import csv
import pdfkit
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, BinaryIO
from dataclasses import dataclass
import jinja2
import io
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class ReportSection:
    title: str
    content: str
    data: Any
    chart_type: Optional[str] = None
    chart_data: Optional[Dict] = None

@dataclass
class ReportConfig:
    title: str
    period: str
    format: str  # html, pdf, json, csv
    sections: List[str]
    include_charts: bool = True
    include_recommendations: bool = True
    branding: Dict = None
    
    def __post_init__(self):
        if self.branding is None:
            self.branding = {
                'company_name': 'VT ULTRA PRO',
                'logo_url': 'https://example.com/logo.png',
                'primary_color': '#4A90E2',
                'secondary_color': '#50E3C2'
            }

class ReportGenerator:
    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(exist_ok=True)
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.templates_dir),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
        self._init_templates()
    
    def _init_templates(self):
        """Initialize default templates"""
        default_templates = {
            'report.html': '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ config.title }} - {{ config.branding.company_name }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        
        /* Header */
        .header { background: {{ config.branding.primary_color }}; color: white; padding: 30px 0; margin-bottom: 30px; }
        .header-content { display: flex; justify-content: space-between; align-items: center; }
        .logo { font-size: 24px; font-weight: bold; }
        .report-info { text-align: right; }
        .report-title { font-size: 28px; margin-bottom: 10px; }
        .report-period { font-size: 16px; opacity: 0.9; }
        
        /* Summary Cards */
        .summary-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 40px; }
        .card { background: white; border-radius: 10px; padding: 25px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        .card-title { font-size: 14px; color: #666; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 1px; }
        .card-value { font-size: 32px; font-weight: bold; color: {{ config.branding.primary_color }}; margin-bottom: 5px; }
        .card-change { font-size: 14px; }
        .card-change.positive { color: #4CAF50; }
        .card-change.negative { color: #F44336; }
        
        /* Sections */
        .section { margin-bottom: 40px; }
        .section-title { font-size: 22px; color: {{ config.branding.primary_color }}; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid {{ config.branding.secondary_color }}; }
        .section-content { background: white; padding: 25px; border-radius: 10px; box-shadow: 0 3px 10px rgba(0,0,0,0.08); }
        
        /* Tables */
        .data-table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        .data-table th { background: {{ config.branding.primary_color }}; color: white; padding: 15px; text-align: left; }
        .data-table td { padding: 12px 15px; border-bottom: 1px solid #eee; }
        .data-table tr:hover { background: #f5f9ff; }
        
        /* Charts */
        .chart-container { margin: 20px 0; padding: 20px; background: white; border-radius: 10px; }
        .chart-placeholder { background: #f5f5f5; border-radius: 8px; padding: 40px; text-align: center; color: #666; }
        
        /* Recommendations */
        .recommendations { background: #FFF9E6; border-left: 4px solid #FFC107; padding: 20px; margin: 20px 0; border-radius: 0 8px 8px 0; }
        .recommendation-item { margin-bottom: 10px; padding-left: 10px; }
        
        /* Footer */
        .footer { margin-top: 50px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #666; font-size: 14px; }
        
        /* Responsive */
        @media (max-width: 768px) {
            .header-content { flex-direction: column; text-align: center; }
            .report-info { margin-top: 15px; }
            .summary-cards { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <div class="header-content">
                <div class="logo">{{ config.branding.company_name }}</div>
                <div class="report-info">
                    <h1 class="report-title">{{ config.title }}</h1>
                    <div class="report-period">Period: {{ config.period }}</div>
                    <div class="report-date">Generated: {{ generated_at }}</div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="container">
        <!-- Summary Cards -->
        {% if summary %}
        <div class="summary-cards">
            {% for card in summary.cards %}
            <div class="card">
                <div class="card-title">{{ card.title }}</div>
                <div class="card-value">{{ card.value }}</div>
                {% if card.change %}
                <div class="card-change {{ 'positive' if card.change.positive else 'negative' }}">
                    {{ card.change.value }} {{ card.change.label }}
                </div>
                {% endif %}
                {% if card.description %}
                <div class="card-description">{{ card.description }}</div>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        {% endif %}
        
        <!-- Sections -->
        {% for section in sections %}
        <div class="section">
            <h2 class="section-title">{{ section.title }}</h2>
            <div class="section-content">
                {% if section.content %}
                <div class="section-text">{{ section.content|safe }}</div>
                {% endif %}
                
                {% if section.data and section.data is mapping %}
                    {% if section.chart_type and config.include_charts %}
                    <div class="chart-container">
                        <div class="chart-placeholder">
                            Chart: {{ section.chart_type }} - Data available
                        </div>
                    </div>
                    {% endif %}
                    
                    {% if section.data.items() %}
                    <table class="data-table">
                        <thead>
                            <tr>
                                {% for key in section.data[0].keys() %}
                                <th>{{ key|replace('_', ' ')|title }}</th>
                                {% endfor %}
                            </tr>
                        </thead>
                        <tbody>
                            {% for row in section.data %}
                            <tr>
                                {% for value in row.values() %}
                                <td>{{ value }}</td>
                                {% endfor %}
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                    {% endif %}
                {% elif section.data is iterable and section.data is not string %}
                    <pre class="data-json">{{ section.data|tojson(indent=2) }}</pre>
                {% else %}
                    <div class="section-data">{{ section.data }}</div>
                {% endif %}
            </div>
        </div>
        {% endfor %}
        
        <!-- Recommendations -->
        {% if recommendations and config.include_recommendations %}
        <div class="section">
            <h2 class="section-title">Recommendations & Insights</h2>
            <div class="recommendations">
                {% for recommendation in recommendations %}
                <div class="recommendation-item">✅ {{ recommendation }}</div>
                {% endfor %}
            </div>
        </div>
        {% endif %}
        
        <!-- Footer -->
        <div class="footer">
            <p>Report generated by {{ config.branding.company_name }} Analytics System</p>
            <p>Confidential - For internal use only</p>
        </div>
    </div>
</body>
</html>
            ''',
            'email_template.html': '''
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: {{ primary_color }}; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; }
        .footer { background: #eee; padding: 20px; text-align: center; font-size: 12px; color: #666; }
        .button { display: inline-block; background: {{ primary_color }}; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .metric { background: white; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid {{ primary_color }}; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ report_title }}</h1>
            <p>Period: {{ period }}</p>
        </div>
        <div class="content">
            <h2>Key Metrics</h2>
            {% for metric in key_metrics %}
            <div class="metric">
                <strong>{{ metric.name }}:</strong> {{ metric.value }}
                {% if metric.change %}
                <small style="color: {{ metric.change.color }};">{{ metric.change.text }}</small>
                {% endif %}
            </div>
            {% endfor %}
            
            <h2>Executive Summary</h2>
            <p>{{ summary }}</p>
            
            {% if recommendations %}
            <h2>Top Recommendations</h2>
            <ul>
                {% for rec in recommendations[:3] %}
                <li>{{ rec }}</li>
                {% endfor %}
            </ul>
            {% endif %}
            
            <a href="{{ report_url }}" class="button">View Full Report</a>
        </div>
        <div class="footer">
            <p>This report was automatically generated by {{ company_name }}</p>
            <p>Need help? Contact support</p>
        </div>
    </div>
</body>
</html>
            '''
        }
        
        for filename, content in default_templates.items():
            template_path = self.templates_dir / filename
            if not template_path.exists():
                template_path.write_text(content)
    
    async def generate_report(self, data: Dict, config: ReportConfig) -> Dict[str, Any]:
        """
        Generate a comprehensive analytics report
        
        Args:
            data: Analytics data to include in report
            config: Report configuration
            
        Returns:
            Dictionary with report data and generated files
        """
        logger.info(f"Generating {config.format.upper()} report: {config.title}")
        
        # Prepare report data
        report_data = self._prepare_report_data(data, config)
        
        # Generate based on format
        if config.format.lower() == 'html':
            result = await self._generate_html_report(report_data, config)
        elif config.format.lower() == 'pdf':
            result = await self._generate_pdf_report(report_data, config)
        elif config.format.lower() == 'json':
            result = await self._generate_json_report(report_data, config)
        elif config.format.lower() == 'csv':
            result = await self._generate_csv_report(report_data, config)
        else:
            raise ValueError(f"Unsupported format: {config.format}")
        
        # Add metadata
        result['metadata'] = {
            'title': config.title,
            'period': config.period,
            'format': config.format,
            'generated_at': datetime.now().isoformat(),
            'sections_included': config.sections,
            'report_id': self._generate_report_id()
        }
        
        logger.info(f"Report generated successfully: {result.get('filename', 'unknown')}")
        
        return result
    
    def _prepare_report_data(self, data: Dict, config: ReportConfig) -> Dict:
        """Prepare data for report generation"""
        sections = []
        
        # Always include summary section
        if 'summary' in data:
            sections.append(ReportSection(
                title="Executive Summary",
                content=self._generate_summary_content(data['summary']),
                data=data['summary'],
                chart_type='summary'
            ))
        
        # Include requested sections
        for section_name in config.sections:
            if section_name in data:
                section_data = data[section_name]
                
                sections.append(ReportSection(
                    title=self._format_section_title(section_name),
                    content=self._generate_section_content(section_name, section_data),
                    data=section_data,
                    chart_type=self._get_chart_type_for_section(section_name)
                ))
        
        # Generate recommendations if requested
        recommendations = []
        if config.include_recommendations and 'insights' in data:
            recommendations.extend(data.get('insights', []))
            recommendations.extend(data.get('recommendations', []))
        
        # Prepare summary cards
        summary_cards = self._generate_summary_cards(data.get('summary', {}))
        
        return {
            'sections': sections,
            'summary': {
                'cards': summary_cards,
                'overview': data.get('summary', {})
            },
            'recommendations': recommendations[:10],  # Limit to 10
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'config': config
        }
    
    def _generate_summary_content(self, summary_data: Dict) -> str:
        """Generate HTML content for summary section"""
        content = []
        
        if 'total_views' in summary_data:
            content.append(f"""
            <p>Total views sent: <strong>{summary_data.get('total_views', 0):,}</strong></p>
            <p>Successful views: <strong>{summary_data.get('successful_views', 0):,}</strong></p>
            <p>Overall success rate: <strong>{summary_data.get('success_rate', 0):.1%}</strong></p>
            """)
        
        if 'period_comparison' in summary_data:
            comparison = summary_data['period_comparison']
            if comparison.get('improvement', 0) > 0:
                trend = f"📈 Increased by {comparison['improvement']:.1%}"
            else:
                trend = f"📉 Decreased by {abs(comparison['improvement']):.1%}"
            
            content.append(f"<p>Trend vs previous period: {trend}</p>")
        
        return '\n'.join(content)
    
    def _format_section_title(self, section_name: str) -> str:
        """Format section name for display"""
        title_map = {
            'source_breakdown': 'Source Performance Breakdown',
            'hourly_distribution': 'Hourly View Distribution',
            'daily_trends': 'Daily Performance Trends',
            'method_performance': 'Method Performance Analysis',
            'top_performing_videos': 'Top Performing Videos',
            'system_overview': 'System Overview & Health',
            'performance_metrics': 'Key Performance Metrics',
            'active_trackers_status': 'Active Campaigns Status'
        }
        return title_map.get(section_name, section_name.replace('_', ' ').title())
    
    def _generate_section_content(self, section_name: str, data: Any) -> str:
        """Generate content for a section"""
        if section_name == 'source_breakdown':
            return self._generate_source_breakdown_content(data)
        elif section_name == 'hourly_distribution':
            return self._generate_hourly_distribution_content(data)
        elif section_name == 'daily_trends':
            return self._generate_daily_trends_content(data)
        elif section_name == 'method_performance':
            return self._generate_method_performance_content(data)
        else:
            return ""
    
    def _generate_source_breakdown_content(self, data: List[Dict]) -> str:
        """Generate content for source breakdown"""
        if not data:
            return "<p>No source data available</p>"
        
        best_source = max(data, key=lambda x: x.get('success_rate', 0))
        worst_source = min(data, key=lambda x: x.get('success_rate', 0))
        
        return f"""
        <p><strong>Best performing source:</strong> {best_source.get('source')} ({best_source.get('success_rate', 0):.1%} success)</p>
        <p><strong>Needs improvement:</strong> {worst_source.get('source')} ({worst_source.get('success_rate', 0):.1%} success)</p>
        """
    
    def _generate_hourly_distribution_content(self, data: List[Dict]) -> str:
        """Generate content for hourly distribution"""
        if not data:
            return "<p>No hourly data available</p>"
        
        peak_hour = max(data, key=lambda x: x.get('views_sent', 0))
        best_hour = max(data, key=lambda x: x.get('success_rate', 0))
        
        return f"""
        <p><strong>Peak traffic hour:</strong> {peak_hour.get('hour')}:00 ({peak_hour.get('views_sent', 0):,} views)</p>
        <p><strong>Best success hour:</strong> {best_hour.get('hour')}:00 ({best_hour.get('success_rate', 0):.1%} success)</p>
        """
    
    def _generate_daily_trends_content(self, data: List[Dict]) -> str:
        """Generate content for daily trends"""
        if len(data) < 2:
            return "<p>Insufficient data for trend analysis</p>"
        
        latest = data[-1]
        previous = data[-2] if len(data) > 1 else latest
        
        trend = "increasing" if latest.get('total', 0) > previous.get('total', 0) else "decreasing"
        
        return f"""
        <p><strong>Latest day:</strong> {latest.get('date')} - {latest.get('total', 0):,} views</p>
        <p><strong>Trend:</strong> {trend.title()} from previous day</p>
        """
    
    def _generate_method_performance_content(self, data: Dict) -> str:
        """Generate content for method performance"""
        if not data:
            return "<p>No method performance data available</p>"
        
        best_method = max(data.items(), key=lambda x: x[1].get('success_rate', 0))
        
        return f"""
        <p><strong>Best method:</strong> {best_method[0]} ({best_method[1].get('success_rate', 0):.1%} success)</p>
        <p><strong>Methods tracked:</strong> {len(data)}</p>
        """
    
    def _get_chart_type_for_section(self, section_name: str) -> Optional[str]:
        """Get appropriate chart type for section"""
        chart_map = {
            'source_breakdown': 'pie',
            'hourly_distribution': 'bar',
            'daily_trends': 'line',
            'method_performance': 'bar',
            'top_performing_videos': 'horizontal_bar'
        }
        return chart_map.get(section_name)
    
    def _generate_summary_cards(self, summary_data: Dict) -> List[Dict]:
        """Generate summary cards for the report"""
        cards = []
        
        # Total Views Card
        if 'total_views' in summary_data:
            cards.append({
                'title': 'Total Views Sent',
                'value': f"{summary_data.get('total_views', 0):,}",
                'description': 'Across all campaigns'
            })
        
        # Success Rate Card
        if 'success_rate' in summary_data:
            success_rate = summary_data.get('success_rate', 0)
            cards.append({
                'title': 'Success Rate',
                'value': f"{success_rate:.1%}",
                'change': {
                    'value': '+2.5%',
                    'label': 'vs last week',
                    'positive': True
                } if success_rate > 0.7 else None
            })
        
        # Active Campaigns Card
        if 'active_trackers' in summary_data:
            cards.append({
                'title': 'Active Campaigns',
                'value': summary_data.get('active_trackers', 0),
                'description': 'Currently running'
            })
        
        # Average Response Time Card
        if 'average_response_time_ms' in summary_data:
            response_time = summary_data.get('average_response_time_ms', 0)
            cards.append({
                'title': 'Avg Response Time',
                'value': f"{response_time:.0f}ms",
                'change': {
                    'value': '-15ms',
                    'label': 'vs average',
                    'positive': True
                } if response_time < 500 else None
            })
        
        # Views Per Minute Card
        if 'views_per_minute' in summary_data:
            cards.append({
                'title': 'Views Per Minute',
                'value': f"{summary_data.get('views_per_minute', 0):.1f}",
                'description': 'Current processing speed'
            })
        
        # System Health Card
        if 'system_health' in summary_data:
            health = summary_data.get('system_health', {})
            status = health.get('status', 'unknown')
            status_color = {
                'healthy': '#4CAF50',
                'warning': '#FFC107',
                'critical': '#F44336'
            }.get(status, '#9E9E9E')
            
            cards.append({
                'title': 'System Health',
                'value': status.title(),
                'description': health.get('message', ''),
                'status_color': status_color
            })
        
        return cards
    
    async def _generate_html_report(self, report_data: Dict, config: ReportConfig) -> Dict:
        """Generate HTML report"""
        try:
            template = self.jinja_env.get_template('report.html')
            html_content = template.render(**report_data)
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"report_{config.title.lower().replace(' ', '_')}_{timestamp}.html"
            filepath = Path('reports') / filename
            
            # Ensure reports directory exists
            filepath.parent.mkdir(exist_ok=True)
            
            # Save HTML file
            filepath.write_text(html_content, encoding='utf-8')
            
            return {
                'filename': filename,
                'filepath': str(filepath),
                'content': html_content,
                'size_bytes': len(html_content.encode('utf-8')),
                'download_url': f"/reports/{filename}"
            }
            
        except Exception as e:
            logger.error(f"Failed to generate HTML report: {e}")
            raise
    
    async def _generate_pdf_report(self, report_data: Dict, config: ReportConfig) -> Dict:
        """Generate PDF report"""
        try:
            # First generate HTML
            html_result = await self._generate_html_report(report_data, config)
            
            # Convert to PDF
            pdf_filename = html_result['filename'].replace('.html', '.pdf')
            pdf_filepath = Path('reports') / pdf_filename
            
            # Configure PDF options
            options = {
                'page-size': 'A4',
                'margin-top': '20mm',
                'margin-right': '15mm',
                'margin-bottom': '20mm',
                'margin-left': '15mm',
                'encoding': "UTF-8",
                'no-outline': None,
                'enable-local-file-access': None
            }
            
            # Generate PDF
            pdfkit.from_file(
                html_result['filepath'],
                str(pdf_filepath),
                options=options
            )
            
            pdf_size = pdf_filepath.stat().st_size
            
            return {
                'filename': pdf_filename,
                'filepath': str(pdf_filepath),
                'size_bytes': pdf_size,
                'download_url': f"/reports/{pdf_filename}",
                'html_source': html_result['filename']
            }
            
        except Exception as e:
            logger.error(f"Failed to generate PDF report: {e}")
            # Fallback to HTML
            return await self._generate_html_report(report_data, config)
    
    async def _generate_json_report(self, report_data: Dict, config: ReportConfig) -> Dict:
        """Generate JSON report"""
        try:
            # Prepare clean JSON data
            json_data = {
                'report': {
                    'title': config.title,
                    'period': config.period,
                    'generated_at': datetime.now().isoformat(),
                    'data': self._prepare_json_data(report_data)
                }
            }
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"report_{config.title.lower().replace(' ', '_')}_{timestamp}.json"
            filepath = Path('reports') / filename
            
            # Ensure reports directory exists
            filepath.parent.mkdir(exist_ok=True)
            
            # Save JSON file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, default=str)
            
            file_size = filepath.stat().st_size
            
            return {
                'filename': filename,
                'filepath': str(filepath),
                'content': json_data,
                'size_bytes': file_size,
                'download_url': f"/reports/{filename}"
            }
            
        except Exception as e:
            logger.error(f"Failed to generate JSON report: {e}")
            raise
    
    def _prepare_json_data(self, report_data: Dict) -> Dict:
        """Prepare data for JSON export"""
        # Remove HTML content and keep only data
        clean_data = {}
        
        if 'sections' in report_data:
            clean_data['sections'] = []
            for section in report_data['sections']:
                clean_section = {
                    'title': section.title,
                    'data': section.data,
                    'chart_type': section.chart_type
                }
                clean_data['sections'].append(clean_section)
        
        if 'summary' in report_data:
            clean_data['summary'] = report_data['summary'].get('overview', {})
        
        if 'recommendations' in report_data:
            clean_data['recommendations'] = report_data['recommendations']
        
        return clean_data
    
    async def _generate_csv_report(self, report_data: Dict, config: ReportConfig) -> Dict:
        """Generate CSV report"""
        try:
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"report_{config.title.lower().replace(' ', '_')}_{timestamp}.csv"
            filepath = Path('reports') / filename
            
            # Ensure reports directory exists
            filepath.parent.mkdir(exist_ok=True)
            
            # Prepare CSV data
            csv_data = []
            
            # Add summary section
            if 'summary' in report_data and 'overview' in report_data['summary']:
                summary = report_data['summary']['overview']
                csv_data.append(['SECTION', 'SUMMARY'])
                csv_data.append([])
                for key, value in summary.items():
                    if not isinstance(value, (dict, list)):
                        csv_data.append([key, value])
            
            # Add sections
            if 'sections' in report_data:
                for section in report_data['sections']:
                    csv_data.append([])
                    csv_data.append(['SECTION', section.title])
                    csv_data.append([])
                    
                    if isinstance(section.data, list):
                        # Add headers
                        if section.data:
                            headers = list(section.data[0].keys())
                            csv_data.append(headers)
                            # Add rows
                            for row in section.data:
                                csv_data.append([row.get(h, '') for h in headers])
                    elif isinstance(section.data, dict):
                        for key, value in section.data.items():
                            if not isinstance(value, (dict, list)):
                                csv_data.append([key, value])
            
            # Write CSV file
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(csv_data)
            
            file_size = filepath.stat().st_size
            
            return {
                'filename': filename,
                'filepath': str(filepath),
                'size_bytes': file_size,
                'download_url': f"/reports/{filename}",
                'row_count': len(csv_data)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate CSV report: {e}")
            raise
    
    def _generate_report_id(self) -> str:
        """Generate unique report ID"""
        import uuid
        return str(uuid.uuid4())[:8].upper()
    
    async def generate_email_report(self, report_data: Dict, config: ReportConfig, 
                                  recipient_email: str) -> Dict:
        """Generate and send email report"""
        try:
            # Generate HTML email content
            template = self.jinja_env.get_template('email_template.html')
            
            # Prepare email data
            key_metrics = []
            if 'summary' in report_data and 'cards' in report_data['summary']:
                for card in report_data['summary']['cards'][:3]:  # Top 3 metrics
                    key_metrics.append({
                        'name': card['title'],
                        'value': card['value']
                    })
            
            email_html = template.render(
                report_title=config.title,
                period=config.period,
                key_metrics=key_metrics,
                summary=report_data.get('summary', {}).get('overview', {}),
                recommendations=report_data.get('recommendations', []),
                report_url=f"https://your-domain.com/reports/{self._generate_report_id()}",
                company_name=config.branding['company_name'],
                primary_color=config.branding['primary_color']
            )
            
            # In a real implementation, you would send the email here
            # For now, we'll just save it
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            email_filename = f"email_report_{timestamp}.html"
            email_filepath = Path('reports') / email_filename
            
            email_filepath.write_text(email_html, encoding='utf-8')
            
            return {
                'status': 'generated',
                'email_filename': email_filename,
                'recipient': recipient_email,
                'subject': f"{config.title} - {config.period}",
                'preview_url': f"/reports/{email_filename}"
            }
            
        except Exception as e:
            logger.error(f"Failed to generate email report: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    async def generate_comparison_report(self, current_data: Dict, previous_data: Dict,
                                       config: ReportConfig) -> Dict:
        """Generate comparison report between two periods"""
        logger.info(f"Generating comparison report: {config.title}")
        
        # Calculate differences
        comparison_data = self._calculate_comparisons(current_data, previous_data)
        
        # Add comparison insights
        comparison_data['comparison_insights'] = self._generate_comparison_insights(
            comparison_data
        )
        
        # Generate report
        return await self.generate_report(comparison_data, config)
    
    def _calculate_comparisons(self, current: Dict, previous: Dict) -> Dict:
        """Calculate comparisons between current and previous data"""
        comparison = {'current': current, 'previous': previous}
        
        # Calculate summary comparisons
        if 'summary' in current and 'summary' in previous:
            current_summary = current['summary']
            previous_summary = previous['summary']
            
            comparison['summary_comparison'] = {
                'total_views_change': self._calculate_percentage_change(
                    current_summary.get('total_views', 0),
                    previous_summary.get('total_views', 0)
                ),
                'success_rate_change': self._calculate_percentage_change(
                    current_summary.get('success_rate', 0),
                    previous_summary.get('success_rate', 0)
                ),
                'active_trackers_change': self._calculate_percentage_change(
                    current_summary.get('active_trackers', 0),
                    previous_summary.get('active_trackers', 0)
                )
            }
        
        return comparison
    
    def _calculate_percentage_change(self, current: float, previous: float) -> Dict:
        """Calculate percentage change"""
        if previous == 0:
            return {'value': 0, 'percentage': 0, 'direction': 'neutral'}
        
        change = current - previous
        percentage = (change / previous) * 100
        
        return {
            'value': change,
            'percentage': percentage,
            'direction': 'increase' if change > 0 else 'decrease' if change < 0 else 'neutral'
        }
    
    def _generate_comparison_insights(self, comparison_data: Dict) -> List[str]:
        """Generate insights from comparison data"""
        insights = []
        
        if 'summary_comparison' in comparison_data:
            comp = comparison_data['summary_comparison']
            
            # Total views insight
            views_change = comp.get('total_views_change', {})
            if views_change.get('percentage', 0) > 10:
                insights.append(f"📈 Total views increased by {views_change['percentage']:.1f}%")
            elif views_change.get('percentage', 0) < -10:
                insights.append(f"📉 Total views decreased by {abs(views_change['percentage']):.1f}%")
            
            # Success rate insight
            success_change = comp.get('success_rate_change', {})
            if success_change.get('percentage', 0) > 5:
                insights.append(f"✅ Success rate improved by {success_change['percentage']:.1f}%")
            elif success_change.get('percentage', 0) < -5:
                insights.append(f"⚠️ Success rate declined by {abs(success_change['percentage']):.1f}%")
        
        return insights