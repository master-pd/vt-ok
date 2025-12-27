"""
Invoice generation and management system
"""
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import json
from datetime import datetime
from typing import Dict, List, Optional
import os

class InvoiceSystem:
    def __init__(self, output_dir='invoices'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        self.styles = getSampleStyleSheet()
    
    def generate_invoice(self, invoice_data: Dict) -> str:
        """Generate PDF invoice"""
        invoice_number = invoice_data['invoice_number']
        filename = f"{self.output_dir}/invoice_{invoice_number}.pdf"
        
        doc = SimpleDocTemplate(
            filename,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        story = []
        
        # Title
        title_style = self.styles['Heading1']
        title = Paragraph(f"INVOICE #{invoice_number}", title_style)
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Invoice details
        details_style = self.styles['Normal']
        
        # From and To sections
        from_to_data = [
            ["From:", "To:"],
            ["VT ULTRA PRO", invoice_data['customer_name']],
            ["123 Business Street", invoice_data['customer_address']],
            ["City, State 12345", invoice_data['customer_city']],
            ["contact@vtultrapro.com", invoice_data['customer_email']],
            ["+1 (555) 123-4567", invoice_data.get('customer_phone', '')]
        ]
        
        from_to_table = Table(from_to_data, colWidths=[2.5*inch, 2.5*inch])
        from_to_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ]))
        
        story.append(from_to_table)
        story.append(Spacer(1, 24))
        
        # Invoice details table
        invoice_details = [
            ["Invoice Date", "Due Date", "Invoice #", "Payment Terms"],
            [invoice_data['invoice_date'], invoice_data['due_date'], 
             invoice_number, invoice_data.get('payment_terms', 'Net 30')]
        ]
        
        details_table = Table(invoice_details, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        details_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        
        story.append(details_table)
        story.append(Spacer(1, 24))
        
        # Items table
        items_data = [["Description", "Quantity", "Unit Price", "Amount"]]
        
        total_amount = 0
        for item in invoice_data['items']:
            amount = item['quantity'] * item['unit_price']
            total_amount += amount
            items_data.append([
                item['description'],
                str(item['quantity']),
                f"${item['unit_price']:.2f}",
                f"${amount:.2f}"
            ])
        
        # Add tax if applicable
        tax_rate = invoice_data.get('tax_rate', 0)
        tax_amount = total_amount * tax_rate / 100
        items_data.append(["", "", "Subtotal:", f"${total_amount:.2f}"])
        items_data.append(["", "", f"Tax ({tax_rate}%):", f"${tax_amount:.2f}"])
        
        # Total
        grand_total = total_amount + tax_amount
        items_data.append(["", "", "Total:", f"${grand_total:.2f}"])
        
        items_table = Table(items_data, colWidths=[3*inch, 1*inch, 1.5*inch, 1.5*inch])
        items_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('GRID', (0, 0), (-1, -4), 0.5, colors.grey),
            ('LINEABOVE', (0, -3), (-1, -3), 1, colors.black),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
            ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ]))
        
        story.append(items_table)
        story.append(Spacer(1, 36))
        
        # Notes
        if invoice_data.get('notes'):
            notes_style = self.styles['Normal']
            notes = Paragraph(f"Notes: {invoice_data['notes']}", notes_style)
            story.append(notes)
            story.append(Spacer(1, 12))
        
        # Payment instructions
        payment_info = invoice_data.get('payment_instructions', 
            "Please make payment to:\nAccount: 123456789\nBank: Example Bank\nRouting: 021000021")
        
        payment_style = self.styles['Normal']
        payment_text = Paragraph(f"Payment Instructions:<br/>{payment_info}", payment_style)
        story.append(payment_text)
        
        # Build PDF
        doc.build(story)
        return filename
    
    def create_invoice_data(self, customer_info: Dict, items: List[Dict], 
                          invoice_number: str = None) -> Dict:
        """Create invoice data structure"""
        if invoice_number is None:
            invoice_number = self._generate_invoice_number()
        
        invoice_date = datetime.now().strftime("%Y-%m-%d")
        due_date = (datetime.now() + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        
        # Calculate totals
        subtotal = sum(item['quantity'] * item['unit_price'] for item in items)
        tax_rate = customer_info.get('tax_rate', 0)
        tax_amount = subtotal * tax_rate / 100
        total_amount = subtotal + tax_amount
        
        invoice_data = {
            'invoice_number': invoice_number,
            'invoice_date': invoice_date,
            'due_date': due_date,
            'customer_name': customer_info.get('name', ''),
            'customer_address': customer_info.get('address', ''),
            'customer_city': customer_info.get('city', ''),
            'customer_email': customer_info.get('email', ''),
            'customer_phone': customer_info.get('phone', ''),
            'items': items,
            'subtotal': subtotal,
            'tax_rate': tax_rate,
            'tax_amount': tax_amount,
            'total_amount': total_amount,
            'currency': customer_info.get('currency', 'USD'),
            'payment_terms': customer_info.get('payment_terms', 'Net 30'),
            'notes': customer_info.get('notes', ''),
            'payment_instructions': customer_info.get('payment_instructions', ''),
            'created_at': datetime.now().isoformat()
        }
        
        return invoice_data
    
    def _generate_invoice_number(self) -> str:
        """Generate unique invoice number"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_part = os.urandom(2).hex()
        return f"INV-{timestamp}-{random_part.upper()}"
    
    def save_invoice_record(self, invoice_data: Dict):
        """Save invoice record to JSON database"""
        record_file = f"{self.output_dir}/invoices.json"
        
        # Load existing records
        if os.path.exists(record_file):
            with open(record_file, 'r') as f:
                records = json.load(f)
        else:
            records = []
        
        # Add new record
        records.append(invoice_data)
        
        # Save back
        with open(record_file, 'w') as f:
            json.dump(records, f, indent=2)
    
    def get_invoice(self, invoice_number: str) -> Optional[Dict]:
        """Get invoice data by number"""
        record_file = f"{self.output_dir}/invoices.json"
        
        if os.path.exists(record_file):
            with open(record_file, 'r') as f:
                records = json.load(f)
            
            for invoice in records:
                if invoice['invoice_number'] == invoice_number:
                    return invoice
        
        return None
    
    def list_invoices(self, customer_email: str = None, 
                     start_date: str = None, end_date: str = None) -> List[Dict]:
        """List invoices with optional filters"""
        record_file = f"{self.output_dir}/invoices.json"
        
        if not os.path.exists(record_file):
            return []
        
        with open(record_file, 'r') as f:
            records = json.load(f)
        
        filtered = records
        
        # Apply filters
        if customer_email:
            filtered = [inv for inv in filtered if inv['customer_email'] == customer_email]
        
        if start_date:
            filtered = [inv for inv in filtered if inv['invoice_date'] >= start_date]
        
        if end_date:
            filtered = [inv for inv in filtered if inv['invoice_date'] <= end_date]
        
        return filtered
    
    def mark_invoice_as_paid(self, invoice_number: str, 
                           payment_method: str, transaction_id: str) -> bool:
        """Mark invoice as paid"""
        record_file = f"{self.output_dir}/invoices.json"
        
        if not os.path.exists(record_file):
            return False
        
        with open(record_file, 'r') as f:
            records = json.load(f)
        
        found = False
        for invoice in records:
            if invoice['invoice_number'] == invoice_number:
                invoice['payment_status'] = 'paid'
                invoice['payment_method'] = payment_method
                invoice['transaction_id'] = transaction_id
                invoice['paid_at'] = datetime.now().isoformat()
                found = True
                break
        
        if found:
            with open(record_file, 'w') as f:
                json.dump(records, f, indent=2)
            
            # Generate receipt
            self._generate_receipt(invoice_number)
        
        return found
    
    def _generate_receipt(self, invoice_number: str):
        """Generate payment receipt"""
        invoice_data = self.get_invoice(invoice_number)
        if not invoice_data:
            return
        
        filename = f"{self.output_dir}/receipt_{invoice_number}.pdf"
        
        doc = SimpleDocTemplate(
            filename,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        story = []
        
        # Title
        title_style = self.styles['Heading1']
        title = Paragraph("PAYMENT RECEIPT", title_style)
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Receipt details
        normal_style = self.styles['Normal']
        
        details = [
            ["Receipt For:", f"Invoice #{invoice_number}"],
            ["Date:", datetime.now().strftime("%Y-%m-%d")],
            ["Customer:", invoice_data['customer_name']],
            ["Amount Paid:", f"${invoice_data['total_amount']:.2f}"],
            ["Payment Method:", invoice_data.get('payment_method', 'Unknown')],
            ["Transaction ID:", invoice_data.get('transaction_id', '')],
            ["Status:", "PAID"]
        ]
        
        details_table = Table(details, colWidths=[2*inch, 3*inch])
        details_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ]))
        
        story.append(details_table)
        story.append(Spacer(1, 24))
        
        # Thank you message
        thank_you = Paragraph(
            "Thank you for your payment!<br/><br/>"
            "This receipt confirms that your payment has been received and processed successfully.",
            normal_style
        )
        story.append(thank_you)
        
        doc.build(story)
    
    def get_invoice_analytics(self, period: str = 'monthly') -> Dict:
        """Get invoice analytics"""
        records = self.list_invoices()
        
        if not records:
            return {
                'total_invoices': 0,
                'total_amount': 0,
                'paid_invoices': 0,
                'pending_invoices': 0,
                'average_invoice_amount': 0
            }
        
        total_invoices = len(records)
        total_amount = sum(inv.get('total_amount', 0) for inv in records)
        paid_invoices = len([inv for inv in records if inv.get('payment_status') == 'paid'])
        pending_invoices = total_invoices - paid_invoices
        
        return {
            'total_invoices': total_invoices,
            'total_amount': total_amount,
            'paid_invoices': paid_invoices,
            'pending_invoices': pending_invoices,
            'average_invoice_amount': total_amount / total_invoices if total_invoices > 0 else 0,
            'collection_rate': (paid_invoices / total_invoices * 100) if total_invoices > 0 else 0
        }
    
    def send_payment_reminder(self, invoice_number: str) -> bool:
        """Send payment reminder for invoice"""
        invoice_data = self.get_invoice(invoice_number)
        if not invoice_data:
            return False
        
        # Check if already paid
        if invoice_data.get('payment_status') == 'paid':
            return False
        
        # Calculate days overdue
        due_date = datetime.fromisoformat(invoice_data['due_date'])
        days_overdue = (datetime.now() - due_date).days
        
        if days_overdue > 0:
            reminder_data = {
                'invoice_number': invoice_number,
                'customer_email': invoice_data['customer_email'],
                'customer_name': invoice_data['customer_name'],
                'amount_due': invoice_data['total_amount'],
                'due_date': invoice_data['due_date'],
                'days_overdue': days_overdue,
                'late_fee': invoice_data.get('late_fee', 0),
                'total_with_late_fee': invoice_data['total_amount'] + invoice_data.get('late_fee', 0),
                'reminder_sent_at': datetime.now().isoformat()
            }
            
            # Save reminder record
            reminder_file = f"{self.output_dir}/reminders.json"
            if os.path.exists(reminder_file):
                with open(reminder_file, 'r') as f:
                    reminders = json.load(f)
            else:
                reminders = []
            
            reminders.append(reminder_data)
            
            with open(reminder_file, 'w') as f:
                json.dump(reminders, f, indent=2)
            
            return True
        
        return False