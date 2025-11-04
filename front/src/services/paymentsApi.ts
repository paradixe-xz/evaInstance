// API de Pagos - Tous Software Corp
export interface PaymentDirection {
  address: string;
  city: string;
  state: string;
  zip: string;
  zip4: string;
  country: string;
  urbanization?: string;
}

export interface PaymentData {
  processpayment: string; // "Y" para procesar
  seller: string;
  sellerName: string;
  company: string;
  department: string;
  ordernum: string;
  leadnum?: string;
  customerName: string;
  customerLastname: string;
  direction: PaymentDirection;
  phone1: string;
  phone2?: string;
  comment?: string;
  payterm: string; // "CC" para tarjeta de crédito
  paytype: string; // "CC" para tarjeta de crédito
  merchat: string; // "TSCTEST" para pruebas
  payment_amt: number;
  cardnumber: string;
  email: string;
  expdate: string; // MM/YY format
  cvv: string;
}

export interface PaymentResponse {
  rescode: string;
  receiptid?: string;
  ack?: string;
  avscode?: string;
  authcode?: string;
  cvv2match?: string;
  transactionid?: string;
  shortmsg?: string;
  longmsg?: string;
}

export class PaymentsApiClient {
  private readonly baseUrl = 'https://tsc-api-925835182876.us-east1.run.app/api/v1/1998010101';
  private readonly token = 'CVWM45F2ASA3O6SLDDFHP19JPULZ8FZL42PVKZU65ZHMRUPVSEFBK11Y5GPOXOA0';

  private getHeaders() {
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${this.token}`
    };
  }

  async processPayment(paymentData: PaymentData): Promise<PaymentResponse> {
    try {
      console.log('💳 Procesando pago:', paymentData);
      
      const response = await fetch(`${this.baseUrl}/payment`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(paymentData)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      console.log('✅ Pago procesado:', result);
      return result;
    } catch (error) {
      console.error('❌ Error procesando pago:', error);
      throw error;
    }
  }

  // Método helper para crear pago básico con valores por defecto
  createBasicPayment(
    orderNumber: string,
    customerName: string,
    customerLastname: string,
    phone: string,
    email: string,
    address: string,
    city: string,
    state: string,
    zip: string,
    amount: number,
    cardNumber: string,
    expDate: string,
    cvv: string,
    leadNumber?: string
  ): PaymentData {
    return {
      processpayment: 'Y',
      seller: 'EVA_AI',
      sellerName: 'Eva AI Assistant',
      company: '1998010101',
      department: '100',
      ordernum: orderNumber,
      leadnum: leadNumber,
      customerName: customerName,
      customerLastname: customerLastname,
      direction: {
        address: address,
        city: city,
        state: state,
        zip: zip,
        zip4: '0001',
        country: 'US',
        urbanization: ''
      },
      phone1: phone,
      phone2: '',
      comment: 'Pago procesado via Eva AI Chat',
      payterm: 'CC',
      paytype: 'CC',
      merchat: 'TSCTEST',
      payment_amt: amount,
      cardnumber: cardNumber,
      email: email,
      expdate: expDate,
      cvv: cvv
    };
  }

  // Validar número de tarjeta (algoritmo de Luhn básico)
  validateCardNumber(cardNumber: string): boolean {
    const cleanNumber = cardNumber.replace(/\s/g, '');
    if (!/^\d{13,19}$/.test(cleanNumber)) return false;
    
    let sum = 0;
    let isEven = false;
    
    for (let i = cleanNumber.length - 1; i >= 0; i--) {
      let digit = parseInt(cleanNumber[i]);
      
      if (isEven) {
        digit *= 2;
        if (digit > 9) digit -= 9;
      }
      
      sum += digit;
      isEven = !isEven;
    }
    
    return sum % 10 === 0;
  }

  // Validar fecha de expiración
  validateExpDate(expDate: string): boolean {
    const match = expDate.match(/^(\d{2})\/(\d{2})$/);
    if (!match) return false;
    
    const month = parseInt(match[1]);
    const year = parseInt(match[2]) + 2000;
    
    if (month < 1 || month > 12) return false;
    
    const now = new Date();
    const expiry = new Date(year, month - 1);
    
    return expiry > now;
  }

  // Validar CVV
  validateCVV(cvv: string): boolean {
    return /^\d{3,4}$/.test(cvv);
  }
}

export const paymentsApi = new PaymentsApiClient();
