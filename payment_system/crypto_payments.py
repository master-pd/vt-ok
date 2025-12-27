"""
Cryptocurrency Payment System
"""

import asyncio
import aiohttp
import json
from typing import Dict, Optional
from datetime import datetime
import hashlib
import hmac

class CryptoPayments:
    """Cryptocurrency payment processor"""
    
    def __init__(self):
        self.coinbase_api_key = None
        self.binance_api_key = None
        self.wallets = {}
        self.exchange_rates = {}
        
    async def setup(self):
        """Setup cryptocurrency payment system"""
        import os
        
        self.coinbase_api_key = os.getenv('COINBASE_API_KEY')
        self.binance_api_key = os.getenv('BINANCE_API_KEY')
        
        # Initialize wallets
        await self.initialize_wallets()
        
        # Load exchange rates
        await self.update_exchange_rates()
        
        print("💰 Cryptocurrency payment system initialized")
    
    async def initialize_wallets(self):
        """Initialize cryptocurrency wallets"""
        self.wallets = {
            'bitcoin': {
                'network': 'bitcoin',
                'min_confirmations': 3,
                'fee_rate': 0.0001,  # BTC
                'supported': True
            },
            'ethereum': {
                'network': 'ethereum',
                'min_confirmations': 12,
                'fee_rate': 0.001,  # ETH
                'supported': True
            },
            'tether': {
                'network': 'ethereum',  # ERC-20
                'min_confirmations': 12,
                'fee_rate': 10,  # USDT
                'supported': True
            },
            'litecoin': {
                'network': 'litecoin',
                'min_confirmations': 6,
                'fee_rate': 0.001,  # LTC
                'supported': True
            }
        }
    
    async def update_exchange_rates(self):
        """Update cryptocurrency exchange rates"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get rates from CoinGecko
                url = "https://api.coingecko.com/api/v3/simple/price"
                params = {
                    'ids': 'bitcoin,ethereum,tether,litecoin',
                    'vs_currencies': 'usd'
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.exchange_rates = data
                        
                        print("💱 Exchange rates updated")
                        return True
                    else:
                        print(f"❌ Failed to update exchange rates: {response.status}")
                        return False
                        
        except Exception as e:
            print(f"❌ Exchange rate update failed: {e}")
            return False
    
    async def create_payment(self, amount_usd: float, 
                           cryptocurrency: str) -> Dict:
        """Create cryptocurrency payment"""
        try:
            # Get current rate
            rate = await self.get_exchange_rate(cryptocurrency, 'usd')
            
            if rate <= 0:
                return {
                    'success': False,
                    'error': 'Invalid exchange rate'
                }
            
            # Calculate cryptocurrency amount
            crypto_amount = amount_usd / rate
            
            # Add network fee
            fee = self.calculate_network_fee(cryptocurrency)
            total_amount = crypto_amount + fee
            
            # Generate payment address
            payment_address = await self.generate_payment_address(cryptocurrency)
            
            # Generate QR code
            qr_code = await self.generate_qr_code(payment_address, total_amount, cryptocurrency)
            
            # Create payment record
            payment_id = f"crypto_{int(datetime.now().timestamp())}"
            
            payment_data = {
                'payment_id': payment_id,
                'cryptocurrency': cryptocurrency,
                'amount_usd': amount_usd,
                'amount_crypto': crypto_amount,
                'network_fee': fee,
                'total_amount': total_amount,
                'payment_address': payment_address,
                'exchange_rate': rate,
                'qr_code': qr_code,
                'expires_at': (datetime.now() + 
                              timedelta(minutes=30)).isoformat(),
                'status': 'pending',
                'created_at': datetime.now().isoformat()
            }
            
            # Store payment
            await self.store_payment(payment_data)
            
            return {
                'success': True,
                'payment_data': payment_data,
                'instructions': self.get_payment_instructions(cryptocurrency)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_exchange_rate(self, cryptocurrency: str, 
                               fiat_currency: str) -> float:
        """Get current exchange rate"""
        crypto_id = cryptocurrency.lower()
        
        if crypto_id in self.exchange_rates:
            return self.exchange_rates[crypto_id].get(fiat_currency.lower(), 0)
        
        # Fallback to CoinGecko
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.coingecko.com/api/v3/simple/price"
                params = {
                    'ids': crypto_id,
                    'vs_currencies': fiat_currency.lower()
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        rate = data.get(crypto_id, {}).get(fiat_currency.lower(), 0)
                        
                        # Update cache
                        if crypto_id not in self.exchange_rates:
                            self.exchange_rates[crypto_id] = {}
                        
                        self.exchange_rates[crypto_id][fiat_currency.lower()] = rate
                        
                        return rate
                    else:
                        return 0
                        
        except:
            return 0
    
    def calculate_network_fee(self, cryptocurrency: str) -> float:
        """Calculate network fee"""
        fees = {
            'bitcoin': 0.0001,
            'ethereum': 0.001,
            'tether': 10,
            'litecoin': 0.001
        }
        
        return fees.get(cryptocurrency.lower(), 0)
    
    async def generate_payment_address(self, cryptocurrency: str) -> str:
        """Generate payment address"""
        # In production, generate from wallet
        # This is simplified
        
        address_prefixes = {
            'bitcoin': ['1', '3', 'bc1'],
            'ethereum': '0x',
            'tether': '0x',
            'litecoin': ['L', 'M', 'ltc1']
        }
        
        prefix = address_prefixes.get(cryptocurrency.lower())
        
        if isinstance(prefix, list):
            prefix = random.choice(prefix)
        
        # Generate random address
        import random
        import string
        
        address_length = random.randint(26, 42)
        random_chars = ''.join(
            random.choices(string.ascii_letters + string.digits, k=address_length)
        )
        
        return prefix + random_chars
    
    async def generate_qr_code(self, address: str, amount: float, 
                              cryptocurrency: str) -> str:
        """Generate QR code for payment"""
        # In production, generate actual QR code
        # This returns a data URL
        
        qr_data = f"{cryptocurrency}:{address}?amount={amount}"
        
        # Simulate QR code generation
        qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={qr_data}"
        
        return qr_code_url
    
    async def store_payment(self, payment_data: Dict):
        """Store payment data"""
        # In production, store in database
        # This is simplified
        
        import os
        os.makedirs('payments/crypto', exist_ok=True)
        
        filename = f"payments/crypto/{payment_data['payment_id']}.json"
        
        with open(filename, 'w') as f:
            json.dump(payment_data, f, indent=2)
    
    def get_payment_instructions(self, cryptocurrency: str) -> List[str]:
        """Get payment instructions"""
        instructions = {
            'bitcoin': [
                "Send exact amount to the Bitcoin address provided",
                "Network confirmations required: 3",
                "Typical confirmation time: 10-30 minutes",
                "Make sure to include network fee",
                "Do not send from exchange wallets"
            ],
            'ethereum': [
                "Send exact amount to the Ethereum address provided",
                "Network confirmations required: 12",
                "Typical confirmation time: 2-5 minutes",
                "Make sure you have enough ETH for gas fees",
                "ERC-20 tokens accepted"
            ],
            'tether': [
                "Send exact amount of USDT to the address provided",
                "Network: Ethereum (ERC-20)",
                "Do not send via other networks (TRC-20, etc.)",
                "Make sure you have ETH for gas fees",
                "Network confirmations required: 12"
            ],
            'litecoin': [
                "Send exact amount to the Litecoin address provided",
                "Network confirmations required: 6",
                "Typical confirmation time: 2-5 minutes",
                "Faster and cheaper than Bitcoin",
                "SegWit addresses supported"
            ]
        }
        
        return instructions.get(cryptocurrency.lower(), [
            "Send exact amount to the address provided",
            "Include network fee if required",
            "Wait for confirmations",
            "Contact support if payment doesn't confirm within 1 hour"
        ])
    
    async def verify_payment(self, payment_id: str, 
                           cryptocurrency: str) -> Dict:
        """Verify cryptocurrency payment"""
        try:
            # Load payment data
            payment_data = await self.load_payment(payment_id)
            
            if not payment_data:
                return {
                    'success': False,
                    'error': 'Payment not found'
                }
            
            address = payment_data['payment_address']
            expected_amount = payment_data['total_amount']
            
            # Check blockchain for transaction
            transaction = await self.check_blockchain_transaction(
                cryptocurrency, address, expected_amount
            )
            
            if transaction['found']:
                confirmations = transaction['confirmations']
                min_confirmations = self.wallets[cryptocurrency.lower()]['min_confirmations']
                
                if confirmations >= min_confirmations:
                    status = 'confirmed'
                else:
                    status = 'processing'
                
                # Update payment status
                payment_data['status'] = status
                payment_data['transaction_id'] = transaction['txid']
                payment_data['confirmations'] = confirmations
                payment_data['verified_at'] = datetime.now().isoformat()
                
                await self.update_payment(payment_id, payment_data)
                
                return {
                    'success': True,
                    'status': status,
                    'confirmations': confirmations,
                    'transaction_id': transaction['txid'],
                    'payment_data': payment_data
                }
            else:
                # Check if payment expired
                expires_at = datetime.fromisoformat(payment_data['expires_at'])
                if datetime.now() > expires_at:
                    payment_data['status'] = 'expired'
                    await self.update_payment(payment_id, payment_data)
                    
                    return {
                        'success': False,
                        'status': 'expired',
                        'error': 'Payment expired'
                    }
                
                return {
                    'success': False,
                    'status': 'pending',
                    'error': 'Payment not found on blockchain'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def load_payment(self, payment_id: str) -> Optional[Dict]:
        """Load payment data"""
        import os
        
        filename = f"payments/crypto/{payment_id}.json"
        
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)
        
        return None
    
    async def update_payment(self, payment_id: str, payment_data: Dict):
        """Update payment data"""
        filename = f"payments/crypto/{payment_id}.json"
        
        with open(filename, 'w') as f:
            json.dump(payment_data, f, indent=2)
    
    async def check_blockchain_transaction(self, cryptocurrency: str, 
                                          address: str, amount: float) -> Dict:
        """Check blockchain for transaction"""
        # In production, use blockchain explorer APIs
        # This is simplified simulation
        
        explorers = {
            'bitcoin': 'https://blockchain.info',
            'ethereum': 'https://api.etherscan.io',
            'tether': 'https://api.etherscan.io',
            'litecoin': 'https://blockchair.com'
        }
        
        explorer = explorers.get(cryptocurrency.lower())
        
        if not explorer:
            return {'found': False, 'error': 'Unsupported cryptocurrency'}
        
        try:
            # Simulate API call
            await asyncio.sleep(0.5)
            
            # Random result for simulation
            if random.random() > 0.3:  # 70% chance of finding transaction
                confirmations = random.randint(0, 20)
                
                return {
                    'found': True,
                    'txid': f'tx{random.randint(1000000, 9999999)}',
                    'confirmations': confirmations,
                    'amount_received': amount,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {'found': False}
                
        except Exception as e:
            return {'found': False, 'error': str(e)}
    
    async def create_invoice(self, user_id: int, amount_usd: float, 
                            cryptocurrency: str = None) -> Dict:
        """Create cryptocurrency invoice"""
        if cryptocurrency is None:
            cryptocurrency = random.choice(['bitcoin', 'ethereum', 'tether'])
        
        payment = await self.create_payment(amount_usd, cryptocurrency)
        
        if not payment['success']:
            return payment
        
        payment_data = payment['payment_data']
        
        invoice = {
            'invoice_id': f"inv_{int(datetime.now().timestamp())}",
            'user_id': user_id,
            'amount_usd': amount_usd,
            'cryptocurrency': cryptocurrency,
            'payment_address': payment_data['payment_address'],
            'amount_crypto': payment_data['amount_crypto'],
            'qr_code': payment_data['qr_code'],
            'exchange_rate': payment_data['exchange_rate'],
            'expires_at': payment_data['expires_at'],
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'payment_id': payment_data['payment_id']
        }
        
        # Store invoice
        await self.store_invoice(invoice)
        
        return {
            'success': True,
            'invoice': invoice,
            'payment_instructions': payment['instructions']
        }
    
    async def store_invoice(self, invoice: Dict):
        """Store invoice"""
        import os
        os.makedirs('invoices', exist_ok=True)
        
        filename = f"invoices/{invoice['invoice_id']}.json"
        
        with open(filename, 'w') as f:
            json.dump(invoice, f, indent=2)
    
    async def get_invoice_status(self, invoice_id: str) -> Dict:
        """Get invoice status"""
        invoice = await self.load_invoice(invoice_id)
        
        if not invoice:
            return {'success': False, 'error': 'Invoice not found'}
        
        payment_id = invoice.get('payment_id')
        
        if payment_id:
            verification = await self.verify_payment(payment_id, invoice['cryptocurrency'])
            
            if verification['success']:
                # Update invoice status
                invoice['status'] = verification['status']
                invoice['verified_at'] = datetime.now().isoformat()
                
                if verification['status'] == 'confirmed':
                    invoice['transaction_id'] = verification['transaction_id']
                    invoice['confirmations'] = verification['confirmations']
                
                await self.update_invoice(invoice_id, invoice)
            
            return {
                'success': True,
                'invoice': invoice,
                'payment_status': verification
            }
        else:
            return {
                'success': False,
                'error': 'No payment associated with invoice'
            }
    
    async def load_invoice(self, invoice_id: str) -> Optional[Dict]:
        """Load invoice"""
        import os
        
        filename = f"invoices/{invoice_id}.json"
        
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)
        
        return None
    
    async def update_invoice(self, invoice_id: str, invoice: Dict):
        """Update invoice"""
        filename = f"invoices/{invoice_id}.json"
        
        with open(filename, 'w') as f:
            json.dump(invoice, f, indent=2)
    
    async def process_webhook(self, webhook_data: Dict) -> Dict:
        """Process cryptocurrency webhook"""
        try:
            # Verify webhook signature
            if not await self.verify_webhook_signature(webhook_data):
                return {'success': False, 'error': 'Invalid signature'}
            
            # Extract payment information
            payment_data = webhook_data.get('payment', {})
            
            # Update payment status
            payment_id = payment_data.get('payment_id')
            
            if payment_id:
                payment = await self.load_payment(payment_id)
                
                if payment:
                    payment['status'] = 'confirmed'
                    payment['webhook_received'] = True
                    payment['confirmed_at'] = datetime.now().isoformat()
                    
                    await self.update_payment(payment_id, payment)
                    
                    # Find associated invoice
                    invoice = await self.find_invoice_by_payment(payment_id)
                    
                    if invoice:
                        invoice['status'] = 'paid'
                        invoice['paid_at'] = datetime.now().isoformat()
                        
                        await self.update_invoice(invoice['invoice_id'], invoice)
                        
                        # Trigger payment processing
                        await self.process_payment_completion(invoice)
                    
                    return {
                        'success': True,
                        'payment_id': payment_id,
                        'status': 'processed'
                    }
            
            return {
                'success': False,
                'error': 'Payment not found'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def verify_webhook_signature(self, webhook_data: Dict) -> bool:
        """Verify webhook signature"""
        # In production, verify signature from payment processor
        # This is simplified
        
        signature = webhook_data.get('signature')
        payload = webhook_data.get('payload', {})
        
        if not signature or not payload:
            return False
        
        # Simple verification (in production, use HMAC)
        expected_signature = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    async def find_invoice_by_payment(self, payment_id: str) -> Optional[Dict]:
        """Find invoice by payment ID"""
        import os
        import json
        
        invoices_dir = 'invoices'
        
        if not os.path.exists(invoices_dir):
            return None
        
        for filename in os.listdir(invoices_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(invoices_dir, filename)
                
                with open(filepath, 'r') as f:
                    invoice = json.load(f)
                
                if invoice.get('payment_id') == payment_id:
                    return invoice
        
        return None
    
    async def process_payment_completion(self, invoice: Dict):
        """Process payment completion"""
        # Add user balance
        user_id = invoice['user_id']
        amount_usd = invoice['amount_usd']
        
        # In production, update user balance in database
        print(f"💰 Payment completed: User {user_id} added ${amount_usd}")
        
        # Send confirmation
        await self.send_payment_confirmation(invoice)
    
    async def send_payment_confirmation(self, invoice: Dict):
        """Send payment confirmation"""
        # In production, send email/notification
        print(f"📧 Payment confirmation sent for invoice {invoice['invoice_id']}")
    
    async def get_supported_cryptocurrencies(self) -> List[Dict]:
        """Get supported cryptocurrencies"""
        cryptocurrencies = []
        
        for crypto, data in self.wallets.items():
            if data['supported']:
                rate = await self.get_exchange_rate(crypto, 'usd')
                
                cryptocurrencies.append({
                    'name': crypto.capitalize(),
                    'symbol': crypto.upper()[:3],
                    'exchange_rate': rate,
                    'network_fee': data['fee_rate'],
                    'min_confirmations': data['min_confirmations'],
                    'icon': f"https://cryptoicons.org/api/icon/{crypto}/200"
                })
        
        return cryptocurrencies
    
    async def get_payment_history(self, user_id: int, 
                                 limit: int = 10) -> List[Dict]:
        """Get user payment history"""
        import os
        import json
        
        history = []
        invoices_dir = 'invoices'
        
        if not os.path.exists(invoices_dir):
            return history
        
        # Find user's invoices
        for filename in os.listdir(invoices_dir):
            if len(history) >= limit:
                break
            
            if filename.endswith('.json'):
                filepath = os.path.join(invoices_dir, filename)
                
                with open(filepath, 'r') as f:
                    invoice = json.load(f)
                
                if invoice.get('user_id') == user_id:
                    history.append(invoice)
        
        # Sort by date (newest first)
        history.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return history[:limit]