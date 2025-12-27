"""
Payment Gateway - Handle all payments
"""

import stripe
from cryptocurrency import Wallet
import paypalrestsdk
from typing import Dict, Optional
import asyncio
from datetime import datetime

class PaymentGateway:
    """Unified payment gateway"""
    
    def __init__(self):
        self.stripe = stripe
        self.stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        
        # PayPal
        paypalrestsdk.configure({
            'mode': os.getenv('PAYPAL_MODE', 'sandbox'),
            'client_id': os.getenv('PAYPAL_CLIENT_ID'),
            'client_secret': os.getenv('PAYPAL_SECRET')
        })
        
        # Crypto wallets
        self.btc_wallet = Wallet('bitcoin')
        self.eth_wallet = Wallet('ethereum')
        self.usdt_wallet = Wallet('tether')
        
    async def create_payment(self, user_id: int, amount: float, 
                           method: str, currency: str = 'USD') -> Dict:
        """Create payment"""
        payment_id = f"pay_{datetime.now().timestamp()}_{user_id}"
        
        if method == 'stripe':
            return await self.stripe_payment(amount, currency, payment_id)
        elif method == 'paypal':
            return await self.paypal_payment(amount, currency, payment_id)
        elif method == 'bitcoin':
            return await self.crypto_payment(amount, 'BTC', payment_id)
        elif method == 'ethereum':
            return await self.crypto_payment(amount, 'ETH', payment_id)
        elif method == 'usdt':
            return await self.crypto_payment(amount, 'USDT', payment_id)
        else:
            raise ValueError(f"Unknown payment method: {method}")
    
    async def stripe_payment(self, amount: float, currency: str, 
                           payment_id: str) -> Dict:
        """Process Stripe payment"""
        try:
            # Create payment intent
            intent = self.stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency=currency.lower(),
                metadata={'payment_id': payment_id},
                automatic_payment_methods={
                    'enabled': True,
                    'allow_redirects': 'never'
                }
            )
            
            return {
                'success': True,
                'payment_id': payment_id,
                'client_secret': intent.client_secret,
                'amount': amount,
                'currency': currency,
                'method': 'stripe',
                'redirect_url': None
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def paypal_payment(self, amount: float, currency: str, 
                           payment_id: str) -> Dict:
        """Process PayPal payment"""
        try:
            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"
                },
                "redirect_urls": {
                    "return_url": f"{os.getenv('WEBAPP_URL')}/payment/success",
                    "cancel_url": f"{os.getenv('WEBAPP_URL')}/payment/cancel"
                },
                "transactions": [{
                    "amount": {
                        "total": str(amount),
                        "currency": currency
                    },
                    "description": f"VT Bot Payment - {payment_id}"
                }]
            })
            
            if payment.create():
                # Get approval URL
                for link in payment.links:
                    if link.rel == "approval_url":
                        approval_url = link.href
                        break
                
                return {
                    'success': True,
                    'payment_id': payment_id,
                    'paypal_id': payment.id,
                    'amount': amount,
                    'currency': currency,
                    'method': 'paypal',
                    'redirect_url': approval_url
                }
            else:
                return {
                    'success': False,
                    'error': payment.error
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def crypto_payment(self, amount: float, coin: str, 
                           payment_id: str) -> Dict:
        """Process cryptocurrency payment"""
        try:
            # Generate payment address
            if coin == 'BTC':
                address = self.btc_wallet.get_new_address()
                wallet = self.btc_wallet
            elif coin == 'ETH':
                address = self.eth_wallet.get_new_address()
                wallet = self.eth_wallet
            elif coin == 'USDT':
                address = self.usdt_wallet.get_new_address()
                wallet = self.usdt_wallet
            else:
                raise ValueError(f"Unsupported coin: {coin}")
            
            # Get current price
            rate = await self.get_crypto_rate(coin, 'USD')
            crypto_amount = amount / rate
            
            return {
                'success': True,
                'payment_id': payment_id,
                'address': address,
                'amount': crypto_amount,
                'coin': coin,
                'usd_amount': amount,
                'method': 'crypto',
                'qr_code': wallet.get_qr_code(address, crypto_amount)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_crypto_rate(self, coin: str, currency: str) -> float:
        """Get cryptocurrency exchange rate"""
        # Implement with CoinGecko or similar API
        import requests
        url = f"https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': coin.lower(),
            'vs_currencies': currency.lower()
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        return data[coin.lower()][currency.lower()]
    
    async def verify_payment(self, payment_id: str, method: str) -> bool:
        """Verify payment status"""
        if method == 'stripe':
            return await self.verify_stripe(payment_id)
        elif method == 'paypal':
            return await self.verify_paypal(payment_id)
        elif method in ['bitcoin', 'ethereum', 'usdt']:
            return await self.verify_crypto(payment_id, method)
        else:
            return False
    
    async def verify_stripe(self, payment_id: str) -> bool:
        """Verify Stripe payment"""
        try:
            payment_intents = self.stripe.PaymentIntent.list(
                limit=1,
                metadata={'payment_id': payment_id}
            )
            
            if payment_intents.data:
                intent = payment_intents.data[0]
                return intent.status == 'succeeded'
            
            return False
        except:
            return False
    
    async def refund_payment(self, payment_id: str, method: str, 
                           amount: float = None) -> bool:
        """Refund payment"""
        # Implementation for refunds
        pass