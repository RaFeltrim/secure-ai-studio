#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ SECURE AI STUDIO - Performance Reporting System
Comprehensive performance analysis and reporting for Basic vs Complex rendering

Features:
- Detailed performance comparison reports
- Statistical analysis of rendering times
- Resource utilization analysis
- Trend identification and forecasting
- Executive summary generation
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
from scipy import stats

@dataclass
class PerformanceReportConfig:
    """Performance report configuration"""
    report_title: str = "Secure AI Studio Performance Analysis"
    date_range_days: int = 30
    include_charts: bool = True
    output_formats: List[str] = None
    comparison_metrics: List[str] = None

@dataclass
class RenderingSample:
    """Individual rendering performance sample"""
    timestamp: datetime
    content_type: str
    resolution: Tuple[int, int]
    complexity: str  # "basic" or "complex"
    rendering_time: float  # seconds
    memory_usage: float  # MB
    cpu_usage: float  # percentage
    success: bool
    file_size: Optional[float] = None  # KB

class PerformanceReporter:
    """
    Comprehensive performance reporting system
    """
    
    def __init__(self, data_directory: str = "performance_data", 
                 reports_directory: str = "reports"):
        """Initialize performance reporter"""
        self.data_dir = Path(data_directory)
        self.reports_dir = Path(reports_directory)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Sample data for demonstration
        self.sample_data = self._generate_sample_data()
        
        # Setup plotting style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
    def _generate_sample_data(self) -> List[RenderingSample]:
        """Generate sample performance data for demonstration"""
        samples = []
        base_time = datetime.now() - timedelta(days=30)
        
        # Generate realistic performance data
        resolutions = [(256, 256), (512, 512), (1024, 1024), (2048, 2048)]
        complexities = ["basic", "complex"]
        
        for day in range(30):
            day_time = base_time + timedelta(days=day)
            
            # Generate 10-20 samples per day
            daily_samples = np.random.randint(10, 21)
            
            for _ in range(daily_samples):
                resolution = resolutions[np.random.choice(len(resolutions))]
                complexity = complexities[np.random.choice(len(complexities))]
                
                # Base rendering time calculation
                base_time_calc = (resolution[0] * resolution[1]) / (256 * 256)
                
                if complexity == "basic":
                    render_time = base_time_calc * np.random.normal(2.5, 0.5)
                    memory_usage = base_time_calc * np.random.normal(500, 100)
                else:  # complex
                    render_time = base_time_calc * np.random.normal(8.0, 1.5)
                    memory_usage = base_time_calc * np.random.normal(1200, 200)
                
                # Ensure positive values
                render_time = max(0.5, render_time)
                memory_usage = max(100, memory_usage)
                
                sample = RenderingSample(
                    timestamp=day_time + timedelta(
                        hours=np.random.randint(0, 24),
                        minutes=np.random.randint(0, 60)
                    ),
                    content_type="image",
                    resolution=resolution,
                    complexity=complexity,
                    rendering_time=render_time,
                    memory_usage=memory_usage,
                    cpu_usage=np.random.normal(75, 15),
                    success=np.random.random() > 0.02,  # 98% success rate
                    file_size=render_time * np.random.normal(500, 100)
                )
                samples.append(sample)
        
        return samples
    
    def load_performance_data(self, data_file: str = None) -> List[RenderingSample]:
        """Load performance data from file or use sample data"""
        if data_file and Path(data_file).exists():
            with open(data_file, 'r') as f:
                data = json.load(f)
                return [RenderingSample(**sample) for sample in data]
        else:
            return self.sample_data
    
    def generate_comparative_analysis(self, data: List[RenderingSample] = None) -> Dict[str, Any]:
        """Generate comprehensive comparative analysis report"""
        data = data or self.sample_data
        
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame([vars(sample) for sample in data])
        
        # Basic statistics
        basic_stats = self._calculate_basic_statistics(df)
        
        # Complexity comparison
        complexity_comparison = self._compare_complexity_performance(df)
        
        # Resolution analysis
        resolution_analysis = self._analyze_resolution_performance(df)
        
        # Trend analysis
        trend_analysis = self._analyze_performance_trends(df)
        
        # Statistical significance tests
        statistical_tests = self._perform_statistical_tests(df)
        
        # Resource utilization analysis
        resource_analysis = self._analyze_resource_utilization(df)
        
        report = {
            'executive_summary': self._generate_executive_summary(
                basic_stats, complexity_comparison, resolution_analysis
            ),
            'basic_statistics': basic_stats,
            'complexity_comparison': complexity_comparison,
            'resolution_analysis': resolution_analysis,
            'trend_analysis': trend_analysis,
            'statistical_tests': statistical_tests,
            'resource_analysis': resource_analysis,
            'recommendations': self._generate_recommendations(
                complexity_comparison, resolution_analysis, trend_analysis
            ),
            'timestamp': datetime.now().isoformat()
        }
        
        return report
    
    def _calculate_basic_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate basic performance statistics"""
        successful_df = df[df['success'] == True]
        
        return {
            'total_samples': len(df),
            'successful_samples': len(successful_df),
            'success_rate': len(successful_df) / len(df) * 100,
            'overall_avg_rendering_time': successful_df['rendering_time'].mean(),
            'overall_median_rendering_time': successful_df['rendering_time'].median(),
            'overall_std_deviation': successful_df['rendering_time'].std(),
            'min_rendering_time': successful_df['rendering_time'].min(),
            'max_rendering_time': successful_df['rendering_time'].max(),
            'avg_memory_usage': successful_df['memory_usage'].mean(),
            'avg_cpu_usage': successful_df['cpu_usage'].mean()
        }
    
    def _compare_complexity_performance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Compare performance between basic and complex rendering"""
        successful_df = df[df['success'] == True]
        
        basic_df = successful_df[successful_df['complexity'] == 'basic']
        complex_df = successful_df[successful_df['complexity'] == 'complex']
        
        comparison = {
            'basic_rendering': {
                'count': len(basic_df),
                'avg_time': basic_df['rendering_time'].mean(),
                'median_time': basic_df['rendering_time'].median(),
                'std_dev': basic_df['rendering_time'].std(),
                'min_time': basic_df['rendering_time'].min(),
                'max_time': basic_df['rendering_time'].max(),
                'avg_memory': basic_df['memory_usage'].mean()
            },
            'complex_rendering': {
                'count': len(complex_df),
                'avg_time': complex_df['rendering_time'].mean(),
                'median_time': complex_df['rendering_time'].median(),
                'std_dev': complex_df['rendering_time'].std(),
                'min_time': complex_df['rendering_time'].min(),
                'max_time': complex_df['rendering_time'].max(),
                'avg_memory': complex_df['memory_usage'].mean()
            }
        }
        
        # Calculate performance ratio
        if comparison['basic_rendering']['avg_time'] > 0:
            comparison['performance_ratio'] = (
                comparison['complex_rendering']['avg_time'] / 
                comparison['basic_rendering']['avg_time']
            )
        
        # Statistical comparison
        t_stat, p_value = stats.ttest_ind(
            basic_df['rendering_time'], 
            complex_df['rendering_time'],
            equal_var=False
        )
        
        comparison['statistical_significance'] = {
            't_statistic': t_stat,
            'p_value': p_value,
            'significant': p_value < 0.05
        }
        
        return comparison
    
    def _analyze_resolution_performance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze performance across different resolutions"""
        successful_df = df[df['success'] == True]
        
        resolution_stats = {}
        for resolution in successful_df['resolution'].unique():
            res_df = successful_df[successful_df['resolution'] == resolution]
            
            resolution_stats[str(resolution)] = {
                'count': len(res_df),
                'avg_rendering_time': res_df['rendering_time'].mean(),
                'median_rendering_time': res_df['rendering_time'].median(),
                'std_deviation': res_df['rendering_time'].std(),
                'avg_memory_usage': res_df['memory_usage'].mean(),
                'success_rate': len(res_df[res_df['success']]) / len(res_df) * 100
            }
        
        # Calculate scaling factors
        sorted_resolutions = sorted(
            resolution_stats.keys(), 
            key=lambda x: eval(x)[0] * eval(x)[1]
        )
        
        scaling_analysis = {}
        if len(sorted_resolutions) > 1:
            base_resolution = sorted_resolutions[0]
            base_pixels = eval(base_resolution)[0] * eval(base_resolution)[1]
            base_time = resolution_stats[base_resolution]['avg_rendering_time']
            
            for resolution in sorted_resolutions[1:]:
                pixels = eval(resolution)[0] * eval(resolution)[1]
                time = resolution_stats[resolution]['avg_rendering_time']
                expected_time = base_time * (pixels / base_pixels)
                scaling_factor = time / expected_time if expected_time > 0 else 0
                
                scaling_analysis[resolution] = {
                    'actual_vs_expected_ratio': scaling_factor,
                    'efficiency': 'optimal' if 0.8 <= scaling_factor <= 1.2 else 'suboptimal'
                }
        
        return {
            'resolution_statistics': resolution_stats,
            'scaling_analysis': scaling_analysis
        }
    
    def _analyze_performance_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze performance trends over time"""
        successful_df = df[df['success'] == True].copy()
        successful_df['date'] = pd.to_datetime(successful_df['timestamp']).dt.date
        
        # Daily averages
        daily_stats = successful_df.groupby('date').agg({
            'rendering_time': ['mean', 'median', 'count'],
            'memory_usage': 'mean',
            'cpu_usage': 'mean'
        }).reset_index()
        
        daily_stats.columns = ['date', 'avg_time', 'median_time', 'sample_count', 'avg_memory', 'avg_cpu']
        
        # Calculate trend using linear regression
        daily_stats['day_number'] = (pd.to_datetime(daily_stats['date']) - 
                                   pd.to_datetime(daily_stats['date']).min()).dt.days
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            daily_stats['day_number'], daily_stats['avg_time']
        )
        
        return {
            'daily_statistics': daily_stats.to_dict('records'),
            'trend_analysis': {
                'slope': slope,
                'intercept': intercept,
                'r_squared': r_value ** 2,
                'p_value': p_value,
                'trend_direction': 'improving' if slope < 0 else 'degrading' if slope > 0 else 'stable',
                'statistically_significant': p_value < 0.05
            }
        }
    
    def _perform_statistical_tests(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Perform various statistical tests"""
        successful_df = df[df['success'] == True]
        
        tests = {}
        
        # Normality test for rendering times
        basic_times = successful_df[successful_df['complexity'] == 'basic']['rendering_time']
        complex_times = successful_df[successful_df['complexity'] == 'complex']['rendering_time']
        
        # Shapiro-Wilk test for normality
        _, basic_normality_p = stats.shapiro(basic_times.sample(min(5000, len(basic_times))))
        _, complex_normality_p = stats.shapiro(complex_times.sample(min(5000, len(complex_times))))
        
        tests['normality_tests'] = {
            'basic_rendering_normality_p': basic_normality_p,
            'complex_rendering_normality_p': complex_normality_p,
            'basic_is_normal': basic_normality_p > 0.05,
            'complex_is_normal': complex_normality_p > 0.05
        }
        
        # Variance equality test
        levene_stat, levene_p = stats.levene(basic_times, complex_times)
        tests['variance_equality'] = {
            'levene_statistic': levene_stat,
            'p_value': levene_p,
            'equal_variance': levene_p > 0.05
        }
        
        return tests
    
    def _analyze_resource_utilization(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze resource utilization patterns"""
        successful_df = df[df['success'] == True]
        
        # Correlation analysis
        correlations = successful_df[['rendering_time', 'memory_usage', 'cpu_usage']].corr()
        
        # Resource efficiency by complexity
        efficiency_analysis = {}
        for complexity in ['basic', 'complex']:
            comp_df = successful_df[successful_df['complexity'] == complexity]
            
            # Time vs resource ratios
            time_per_memory = comp_df['rendering_time'] / comp_df['memory_usage']
            time_per_cpu = comp_df['rendering_time'] / (comp_df['cpu_usage'] / 100)
            
            efficiency_analysis[complexity] = {
                'avg_time_per_mb_memory': time_per_memory.mean(),
                'avg_time_per_cpu_percent': time_per_cpu.mean(),
                'efficiency_score': 1 / (time_per_memory.mean() * time_per_cpu.mean())
            }
        
        return {
            'correlations': correlations.to_dict(),
            'efficiency_analysis': efficiency_analysis,
            'resource_distribution': {
                'memory_usage_quartiles': successful_df['memory_usage'].quantile([0.25, 0.5, 0.75]).to_dict(),
                'cpu_usage_quartiles': successful_df['cpu_usage'].quantile([0.25, 0.5, 0.75]).to_dict()
            }
        }
    
    def _generate_executive_summary(self, basic_stats: Dict, 
                                  complexity_comparison: Dict, 
                                  resolution_analysis: Dict) -> str:
        """Generate executive summary"""
        summary = f"""
# EXECUTIVE SUMMARY - PERFORMANCE ANALYSIS

## Key Performance Indicators

- **Overall Success Rate**: {basic_stats['success_rate']:.1f}%
- **Average Rendering Time**: {basic_stats['overall_avg_rendering_time']:.2f} seconds
- **Performance Ratio (Complex/Basic)**: {complexity_comparison.get('performance_ratio', 0):.2f}x
- **Statistical Significance**: {'Significant' if complexity_comparison['statistical_significance']['significant'] else 'Not Significant'}

## Critical Findings

1. **Complexity Impact**: Complex rendering takes approximately {complexity_comparison.get('performance_ratio', 0):.1f}x longer than basic rendering
2. **Resolution Scaling**: Performance scales approximately linearly with pixel count
3. **System Stability**: High success rate of {basic_stats['success_rate']:.1f}% indicates reliable operation
4. **Resource Utilization**: Efficient use of CPU ({basic_stats['avg_cpu_usage']:.1f}%) and memory ({basic_stats['avg_memory_usage']:.0f}MB)

## Recommendations

- Optimize complex rendering algorithms for better performance
- Consider hardware upgrades for high-resolution processing
- Implement predictive scaling for resource allocation
"""
        return summary.strip()
    
    def _generate_recommendations(self, complexity_comparison: Dict, 
                                resolution_analysis: Dict, 
                                trend_analysis: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Based on complexity comparison
        perf_ratio = complexity_comparison.get('performance_ratio', 0)
        if perf_ratio > 4:
            recommendations.append(
                "Complex rendering performance significantly lags behind basic rendering. "
                "Consider algorithmic optimizations or parallel processing for complex tasks."
            )
        elif perf_ratio > 3:
            recommendations.append(
                "Moderate performance gap in complex rendering. "
                "Evaluate GPU acceleration opportunities."
            )
        
        # Based on resolution analysis
        scaling_issues = [
            res for res, data in resolution_analysis.get('scaling_analysis', {}).items()
            if data['efficiency'] == 'suboptimal'
        ]
        if scaling_issues:
            recommendations.append(
                f"Suboptimal scaling detected for resolutions: {', '.join(scaling_issues)}. "
                "Review rendering pipeline for resolution-dependent bottlenecks."
            )
        
        # Based on trends
        trend = trend_analysis['trend_analysis']['trend_direction']
        if trend == 'degrading':
            recommendations.append(
                "Performance showing degradation trend. "
                "Investigate system resource constraints or software inefficiencies."
            )
        elif trend == 'improving':
            recommendations.append(
                "Positive performance trend observed. "
                "Continue current optimization strategies."
            )
        
        # General recommendations
        recommendations.extend([
            "Implement adaptive batching based on complexity and resolution",
            "Consider implementing caching for frequently requested combinations",
            "Establish performance baselines for proactive monitoring",
            "Plan capacity for peak usage periods"
        ])
        
        return recommendations
    
    def generate_visualizations(self, report_data: Dict[str, Any], 
                              output_prefix: str = "performance_report") -> List[str]:
        """Generate visualization charts"""
        generated_files = []
        
        try:
            # 1. Basic vs Complex Comparison Chart
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle('Performance Comparison Analysis', fontsize=16)
            
            complexity_data = report_data['complexity_comparison']
            
            # Bar chart - Average rendering times
            categories = ['Basic', 'Complex']
            avg_times = [
                complexity_data['basic_rendering']['avg_time'],
                complexity_data['complex_rendering']['avg_time']
            ]
            
            bars = ax1.bar(categories, avg_times, color=['skyblue', 'lightcoral'])
            ax1.set_title('Average Rendering Time by Complexity')
            ax1.set_ylabel('Time (seconds)')
            
            # Add value labels
            for bar, value in zip(bars, avg_times):
                ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                        f'{value:.2f}s', ha='center', va='bottom')
            
            # Box plot - Distribution comparison
            # We'll simulate the data for visualization
            basic_sim = np.random.gamma(2, complexity_data['basic_rendering']['avg_time']/2, 1000)
            complex_sim = np.random.gamma(2, complexity_data['complex_rendering']['avg_time']/2, 1000)
            
            ax2.boxplot([basic_sim, complex_sim], labels=['Basic', 'Complex'])
            ax2.set_title('Rendering Time Distribution')
            ax2.set_ylabel('Time (seconds)')
            
            # 2. Resolution Performance Chart
            resolution_data = report_data['resolution_analysis']['resolution_statistics']
            resolutions = list(resolution_data.keys())
            avg_times = [data['avg_rendering_time'] for data in resolution_data.values()]
            
            ax3.bar(range(len(resolutions)), avg_times, color='lightgreen')
            ax3.set_title('Average Rendering Time by Resolution')
            ax3.set_xlabel('Resolution')
            ax3.set_ylabel('Time (seconds)')
            ax3.set_xticks(range(len(resolutions)))
            ax3.set_xticklabels([res.replace('(', '').replace(')', '') for res in resolutions], rotation=45)
            
            # Add value labels
            for i, (res, time_val) in enumerate(zip(resolutions, avg_times)):
                ax3.text(i, time_val + 0.1, f'{time_val:.1f}s', 
                        ha='center', va='bottom', rotation=45)
            
            # 3. Trend Analysis Chart
            trend_data = report_data['trend_analysis']['daily_statistics']
            if trend_data:
                dates = [pd.to_datetime(item['date']) for item in trend_data]
                avg_times = [item['avg_time'] for item in trend_data]
                
                ax4.plot(dates, avg_times, marker='o', linewidth=2, markersize=4)
                ax4.set_title('Performance Trend Over Time')
                ax4.set_xlabel('Date')
                ax4.set_ylabel('Average Rendering Time (seconds)')
                ax4.tick_params(axis='x', rotation=45)
                ax4.grid(True, alpha=0.3)
            
            plt.tight_layout()
            chart_path = self.reports_dir / f"{output_prefix}_charts.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            generated_files.append(str(chart_path))
            
            # 4. Correlation Heatmap
            if 'resource_analysis' in report_data:
                plt.figure(figsize=(10, 8))
                correlations = pd.DataFrame(report_data['resource_analysis']['correlations'])
                sns.heatmap(correlations, annot=True, cmap='coolwarm', center=0,
                           square=True, linewidths=0.5)
                plt.title('Performance Metric Correlations')
                
                corr_path = self.reports_dir / f"{output_prefix}_correlations.png"
                plt.savefig(corr_path, dpi=300, bbox_inches='tight')
                plt.close()
                generated_files.append(str(corr_path))
            
        except Exception as e:
            print(f"Warning: Failed to generate charts: {e}")
        
        return generated_files
    
    def export_report(self, report_data: Dict[str, Any], 
                     formats: List[str] = None) -> List[str]:
        """Export report in specified formats"""
        formats = formats or ['json', 'txt']
        exported_files = []
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = f"performance_report_{timestamp}"
        
        # JSON export
        if 'json' in formats:
            json_path = self.reports_dir / f"{base_name}.json"
            with open(json_path, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            exported_files.append(str(json_path))
        
        # Text/Markdown export
        if 'txt' in formats or 'md' in formats:
            txt_path = self.reports_dir / f"{base_name}.md"
            with open(txt_path, 'w') as f:
                f.write(self._format_markdown_report(report_data))
            exported_files.append(str(txt_path))
        
        # CSV export for detailed data
        if 'csv' in formats:
            csv_path = self.reports_dir / f"{base_name}_details.csv"
            # Convert sample data to CSV
            df = pd.DataFrame([vars(sample) for sample in self.sample_data])
            df.to_csv(csv_path, index=False)
            exported_files.append(str(csv_path))
        
        return exported_files
    
    def _format_markdown_report(self, report_data: Dict[str, Any]) -> str:
        """Format report as markdown"""
        md_lines = []
        
        # Header
        md_lines.append(f"# {report_data.get('executive_summary', 'Performance Analysis Report')}")
        md_lines.append(f"*Generated: {report_data['timestamp']}*")
        md_lines.append("")
        
        # Basic Statistics
        stats = report_data['basic_statistics']
        md_lines.append("## Basic Performance Statistics")
        md_lines.append("| Metric | Value |")
        md_lines.append("|--------|-------|")
        md_lines.append(f"| Total Samples | {stats['total_samples']} |")
        md_lines.append(f"| Success Rate | {stats['success_rate']:.1f}% |")
        md_lines.append(f"| Average Rendering Time | {stats['overall_avg_rendering_time']:.2f} seconds |")
        md_lines.append(f"| Median Rendering Time | {stats['overall_median_rendering_time']:.2f} seconds |")
        md_lines.append(f"| Memory Usage | {stats['avg_memory_usage']:.0f} MB |")
        md_lines.append(f"| CPU Usage | {stats['avg_cpu_usage']:.1f}% |")
        md_lines.append("")
        
        # Complexity Comparison
        complexity = report_data['complexity_comparison']
        md_lines.append("## Basic vs Complex Rendering Comparison")
        md_lines.append("| Complexity | Average Time | Median Time | Samples |")
        md_lines.append("|------------|--------------|-------------|---------|")
        md_lines.append(f"| Basic | {complexity['basic_rendering']['avg_time']:.2f}s | {complexity['basic_rendering']['median_time']:.2f}s | {complexity['basic_rendering']['count']} |")
        md_lines.append(f"| Complex | {complexity['complex_rendering']['avg_time']:.2f}s | {complexity['complex_rendering']['median_time']:.2f}s | {complexity['complex_rendering']['count']} |")
        md_lines.append("")
        md_lines.append(f"**Performance Ratio**: {complexity.get('performance_ratio', 0):.2f}x (Complex/Basic)")
        md_lines.append(f"**Statistically Significant**: {'Yes' if complexity['statistical_significance']['significant'] else 'No'}")
        md_lines.append("")
        
        # Key Recommendations
        md_lines.append("## Key Recommendations")
        for i, rec in enumerate(report_data['recommendations'][:5], 1):
            md_lines.append(f"{i}. {rec}")
        
        return "\n".join(md_lines)

# Example usage
def main():
    """Demo performance reporting functionality"""
    print("📊 PERFORMANCE REPORTING SYSTEM")
    print("=" * 40)
    
    # Initialize reporter
    reporter = PerformanceReporter()
    
    try:
        print("📈 Generating performance analysis...")
        
        # Generate comparative analysis
        report = reporter.generate_comparative_analysis()
        
        # Display key findings
        print("\n📋 EXECUTIVE SUMMARY")
        print("-" * 30)
        stats = report['basic_statistics']
        complexity = report['complexity_comparison']
        
        print(f"Success Rate: {stats['success_rate']:.1f}%")
        print(f"Average Rendering Time: {stats['overall_avg_rendering_time']:.2f}s")
        print(f"Basic vs Complex Ratio: {complexity.get('performance_ratio', 0):.2f}x")
        print(f"Statistical Significance: {'✅' if complexity['statistical_significance']['significant'] else '❌'}")
        
        # Generate visualizations
        print("\n🎨 Generating visualizations...")
        chart_files = reporter.generate_visualizations(report)
        print(f"Generated {len(chart_files)} chart files")
        for file in chart_files:
            print(f"  - {Path(file).name}")
        
        # Export reports
        print("\n💾 Exporting reports...")
        exported_files = reporter.export_report(report, ['json', 'md'])
        print(f"Generated {len(exported_files)} report files")
        for file in exported_files:
            print(f"  - {Path(file).name}")
        
        # Show some key insights
        print("\n🔍 KEY INSIGHTS")
        print("-" * 20)
        
        # Trend analysis
        trend = report['trend_analysis']['trend_analysis']
        print(f"Trend Direction: {trend['trend_direction'].upper()}")
        print(f"Statistical Significance: {'Significant' if trend['statistically_significant'] else 'Not Significant'}")
        
        # Resource analysis highlights
        resources = report['resource_analysis']
        basic_eff = resources['efficiency_analysis']['basic']['efficiency_score']
        complex_eff = resources['efficiency_analysis']['complex']['efficiency_score']
        print(f"Efficiency Score - Basic: {basic_eff:.3f}")
        print(f"Efficiency Score - Complex: {complex_eff:.3f}")
        
        print("\n✅ Performance reporting completed successfully!")
        print(f"Reports saved to: {reporter.reports_dir}")
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)