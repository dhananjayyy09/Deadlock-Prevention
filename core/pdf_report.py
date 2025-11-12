"""
PDF Report Generator for Deadlock Detection Tool
Generates professional analysis reports with graphs and statistics
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import io
from typing import Dict, Any, Optional


class PDFReportGenerator:
    """Generate comprehensive PDF reports for deadlock analysis"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Create custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2563eb'),
            spaceAfter=12,
            spaceBefore=12
        ))
        
        self.styles.add(ParagraphStyle(
            name='Status',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#059669'),
            alignment=TA_CENTER,
            spaceAfter=20
        ))
    
    def generate_report(
        self,
        snapshot: Dict[str, Any],
        detection_result: Optional[Dict[str, Any]] = None,
        prediction_result: Optional[Dict[str, Any]] = None,
        ml_result: Optional[Dict[str, Any]] = None,
        analytics: Optional[Dict[str, Any]] = None,
        filename: str = "deadlock_report.pdf"
    ) -> str:
        """
        Generate comprehensive PDF report
        
        Args:
            snapshot: System snapshot data
            detection_result: WFG detection results
            prediction_result: Banker's algorithm results
            ml_result: ML prediction results
            analytics: Historical analytics data
            filename: Output filename
        
        Returns:
            Path to generated PDF file
        """
        # Create PDF document
        doc = SimpleDocTemplate(
            filename,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Container for PDF elements
        story = []
        
        # Add title page
        story.extend(self._create_title_page())
        
        # Add executive summary
        story.extend(self._create_executive_summary(
            snapshot, detection_result, prediction_result, ml_result
        ))
        
        # Add system overview
        story.append(PageBreak())
        story.extend(self._create_system_overview(snapshot))
        
        # Add detection results
        if detection_result:
            story.append(PageBreak())
            story.extend(self._create_detection_section(detection_result))
        
        # Add prediction results
        if prediction_result:
            story.append(PageBreak())
            story.extend(self._create_prediction_section(prediction_result))
        
        # Add ML results
        if ml_result:
            story.append(PageBreak())
            story.extend(self._create_ml_section(ml_result))
        
        # Add analytics
        if analytics:
            story.append(PageBreak())
            story.extend(self._create_analytics_section(analytics))
        
        # Add recommendations
        story.append(PageBreak())
        story.extend(self._create_recommendations(detection_result, prediction_result))
        
        # Build PDF
        doc.build(story)
        
        return filename
    
    def _create_title_page(self):
        """Create title page"""
        elements = []
        
        # Title
        title = Paragraph(
            "Deadlock Detection & Analysis Report",
            self.styles['CustomTitle']
        )
        elements.append(title)
        elements.append(Spacer(1, 0.5*inch))
        
        # Timestamp
        timestamp = Paragraph(
            f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
            self.styles['Normal']
        )
        elements.append(timestamp)
        elements.append(Spacer(1, 0.3*inch))
        
        # System info
        info_text = """
        <para align=center>
        <b>Automated Deadlock Detection System</b><br/>
        Version 1.0<br/>
        Advanced Analysis Report
        </para>
        """
        elements.append(Paragraph(info_text, self.styles['Normal']))
        elements.append(Spacer(1, 1*inch))
        
        return elements
    
    def _create_executive_summary(self, snapshot, detection, prediction, ml):
        """Create executive summary section"""
        elements = []
        
        elements.append(Paragraph("Executive Summary", self.styles['SectionHeading']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Status determination
        has_deadlock = detection and detection.get('has_deadlock', False)
        is_safe = prediction and prediction.get('safe', False)
        
        if has_deadlock:
            status_text = '<font color="#dc2626"><b>⚠ DEADLOCK DETECTED</b></font>'
            status_color = colors.HexColor('#fee2e2')
        elif not is_safe:
            status_text = '<font color="#f59e0b"><b>⚠ UNSAFE STATE</b></font>'
            status_color = colors.HexColor('#fef3c7')
        else:
            status_text = '<font color="#059669"><b>✓ SYSTEM SAFE</b></font>'
            status_color = colors.HexColor('#d1fae5')
        
        # Status box
        status_table = Table(
            [[Paragraph(status_text, self.styles['Normal'])]],
            colWidths=[6*inch]
        )
        status_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), status_color),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 12),
            ('BOX', (0, 0), (-1, -1), 2, colors.grey)
        ]))
        elements.append(status_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Key metrics
        num_processes = len(snapshot.get('processes', []))
        num_resources = len(snapshot.get('resources', {}))
        num_allocations = len([k for k, v in snapshot.get('allocation', {}).items() if v > 0])
        num_requests = len([k for k, v in snapshot.get('request', {}).items() if v > 0])
        
        metrics_data = [
            ['Metric', 'Value'],
            ['Total Processes', str(num_processes)],
            ['Total Resources', str(num_resources)],
            ['Active Allocations', str(num_allocations)],
            ['Pending Requests', str(num_requests)]
        ]
        
        if detection:
            metrics_data.append(['Detected Cycles', str(len(detection.get('cycles', [])))])
            metrics_data.append(['Detection Time', f"{detection.get('detection_time_ms', 0)}ms"])
        
        if ml:
            probability = ml.get('probability', 0) * 100
            metrics_data.append(['ML Risk Score', f"{probability:.1f}%"])
        
        metrics_table = Table(metrics_data, colWidths=[3*inch, 3*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(metrics_table)
        
        return elements
    
    def _create_system_overview(self, snapshot):
        """Create system overview section"""
        elements = []
        
        elements.append(Paragraph("System Overview", self.styles['SectionHeading']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Process table
        elements.append(Paragraph("<b>Processes</b>", self.styles['Normal']))
        elements.append(Spacer(1, 0.1*inch))
        
        process_data = [['PID', 'Name']]
        for proc in snapshot.get('processes', []):
            process_data.append([str(proc['pid']), proc.get('name', f"Process_{proc['pid']}")])
        
        process_table = Table(process_data, colWidths=[1*inch, 5*inch])
        process_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(process_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Resource table
        elements.append(Paragraph("<b>Resources</b>", self.styles['Normal']))
        elements.append(Spacer(1, 0.1*inch))
        
        resource_data = [['Resource ID', 'Total Instances']]
        for rid, res in snapshot.get('resources', {}).items():
            resource_data.append([rid, str(res['total'])])
        
        resource_table = Table(resource_data, colWidths=[3*inch, 3*inch])
        resource_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(resource_table)
        
        return elements
    
    def _create_detection_section(self, detection):
        """Create detection results section"""
        elements = []
        
        elements.append(Paragraph("Deadlock Detection Results", self.styles['SectionHeading']))
        elements.append(Spacer(1, 0.2*inch))
        
        has_deadlock = detection.get('has_deadlock', False)
        cycles = detection.get('cycles', [])
        
        if has_deadlock:
            result_text = f"""
            <font color="#dc2626"><b>Deadlock Detected!</b></font><br/>
            Found {len(cycles)} circular wait cycle(s) in the system.<br/>
            Detection Time: {detection.get('detection_time_ms', 0)}ms
            """
        else:
            result_text = """
            <font color="#059669"><b>No Deadlock Detected</b></font><br/>
            System is currently deadlock-free.
            """
        
        elements.append(Paragraph(result_text, self.styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Cycle details
        if cycles:
            elements.append(Paragraph("<b>Detected Cycles:</b>", self.styles['Normal']))
            elements.append(Spacer(1, 0.1*inch))
            
            for i, cycle in enumerate(cycles, 1):
                cycle_text = f"Cycle {i}: {' → '.join(map(str, cycle))} → {cycle[0]}"
                elements.append(Paragraph(f"• {cycle_text}", self.styles['Normal']))
        
        return elements
    
    def _create_prediction_section(self, prediction):
        """Create Banker's algorithm results"""
        elements = []
        
        elements.append(Paragraph("Safety Analysis (Banker's Algorithm)", self.styles['SectionHeading']))
        elements.append(Spacer(1, 0.2*inch))
        
        is_safe = prediction.get('safe', False)
        safe_sequence = prediction.get('safe_sequence', [])
        
        if is_safe:
            result_text = f"""
            <font color="#059669"><b>System is in SAFE state</b></font><br/>
            Safe execution sequence found: {' → '.join(map(str, safe_sequence))}
            """
        else:
            result_text = """
            <font color="#dc2626"><b>System is in UNSAFE state</b></font><br/>
            No safe sequence exists. System may deadlock.
            """
        
        elements.append(Paragraph(result_text, self.styles['Normal']))
        
        return elements
    
    def _create_ml_section(self, ml_result):
        """Create ML prediction section"""
        elements = []
        
        elements.append(Paragraph("Machine Learning Prediction", self.styles['SectionHeading']))
        elements.append(Spacer(1, 0.2*inch))
        
        probability = ml_result.get('probability', 0) * 100
        risk_level = ml_result.get('risk_level', 'UNKNOWN')
        
        ml_text = f"""
        <b>Deadlock Probability:</b> {probability:.1f}%<br/>
        <b>Risk Level:</b> {risk_level}
        """
        
        elements.append(Paragraph(ml_text, self.styles['Normal']))
        
        return elements
    
    def _create_analytics_section(self, analytics):
        """Create analytics section"""
        elements = []
        
        elements.append(Paragraph("Historical Analytics", self.styles['SectionHeading']))
        elements.append(Spacer(1, 0.2*inch))
        
        trends = analytics.get('trends', {})
        
        analytics_text = f"""
        <b>Total Deadlocks (7 days):</b> {trends.get('total_deadlocks', 0)}<br/>
        <b>Average Cycles:</b> {trends.get('avg_cycles', 0)}<br/>
        <b>Average Detection Time:</b> {trends.get('avg_detection_time_ms', 0)}ms
        """
        
        elements.append(Paragraph(analytics_text, self.styles['Normal']))
        
        return elements
    
    def _create_recommendations(self, detection, prediction):
        """Create recommendations section"""
        elements = []
        
        elements.append(Paragraph("Recommendations", self.styles['SectionHeading']))
        elements.append(Spacer(1, 0.2*inch))
        
        recommendations = []
        
        if detection and detection.get('has_deadlock'):
            recommendations.append("• Immediate action required: Apply recovery strategy")
            recommendations.append("• Consider process termination or resource preemption")
            recommendations.append("• Review resource allocation policies")
        elif prediction and not prediction.get('safe'):
            recommendations.append("• System in unsafe state - monitor closely")
            recommendations.append("• Defer new resource requests if possible")
            recommendations.append("• Consider implementing Banker's algorithm for prevention")
        else:
            recommendations.append("• System operating normally")
            recommendations.append("• Continue monitoring for potential issues")
            recommendations.append("• Regular audits recommended")
        
        recommendations.append("• Implement deadlock prevention strategies:")
        recommendations.append("  - Lock ordering")
        recommendations.append("  - Timeout mechanisms")
        recommendations.append("  - Resource quotas")
        
        for rec in recommendations:
            elements.append(Paragraph(rec, self.styles['Normal']))
            elements.append(Spacer(1, 0.05*inch))
        
        return elements
