// API de Órdenes - Tous Software Corp
export interface OrderDirection {
  address?: string;
  state?: string;
  city?: string;
  zip?: string;
  zip4?: string;
  country?: string;
  urbanization?: string;
}

export interface OrderDetail {
  productCode?: string;
  packageCode?: string;
  qty?: number;
  total?: number;
  pricePerUnit?: number;
}

export interface OrderData {
  createBy: string;
  seller: string;
  sellerName?: string;
  company?: string;
  department?: string;
  ordenDate?: string; // YYYY-MM-DD format
  leadnum?: string;
  customerName?: string;
  customerLastname?: string;
  direction?: OrderDirection;
  phone1?: string;
  phone2?: string;
  comment?: string;
  payterm?: string;
  deliveryDate?: string; // YYYY-MM-DD format
  shipvia?: string;
  subTotal?: number;
  total?: number;
  saleTax?: number;
  taxes?: number;
  paid?: number;
  discount?: number;
  discountAmount?: number;
  detail?: OrderDetail[];
}

export interface OrderResponse {
  rescode: string;
  resmsg?: string;
  ordernum?: string;
}

export class OrdersApiClient {
  private readonly baseUrl = 'https://tsc-api-925835182876.us-east1.run.app/api/v1/1998010101';
  private readonly token = 'CVWM45F2ASA3O6SLDDFHP19JPULZ8FZL42PVKZU65ZHMRUPVSEFBK11Y5GPOXOA0';

  private getHeaders() {
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${this.token}`
    };
  }

  async createOrder(orderData: OrderData): Promise<OrderResponse> {
    try {
      console.log('🛒 Creando orden:', orderData);
      
      const response = await fetch(`${this.baseUrl}/order`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(orderData)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      console.log('✅ Orden creada:', result);
      return result;
    } catch (error) {
      console.error('❌ Error creando orden:', error);
      throw error;
    }
  }

  // Método helper para crear orden básica con valores por defecto
  createBasicOrder(
    customerName: string,
    customerLastname: string,
    phone: string,
    address?: string,
    city?: string,
    state?: string,
    zip?: string,
    leadnum?: string,
    productCode: string = 'API01',
    qty: number = 1,
    pricePerUnit: number = 100
  ): OrderData {
    const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
    const deliveryDate = new Date();
    deliveryDate.setDate(deliveryDate.getDate() + 7); // +7 días
    
    return {
      createBy: 'EVA_AI',
      seller: 'EVA_AI',
      sellerName: 'Eva AI Assistant',
      company: '90001',
      department: '90001',
      ordenDate: today,
      leadnum: leadnum,
      customerName: customerName,
      customerLastname: customerLastname,
      direction: {
        address: address || '',
        city: city || '',
        state: state || 'FL',
        zip: zip || '',
        zip4: '',
        country: 'US',
        urbanization: ''
      },
      phone1: phone,
      phone2: '',
      comment: 'Orden creada via Eva AI Chat',
      payterm: 'PREPAID',
      deliveryDate: deliveryDate.toISOString().split('T')[0],
      shipvia: 'USPS',
      subTotal: pricePerUnit * qty,
      total: pricePerUnit * qty,
      saleTax: 0,
      taxes: 0,
      paid: 0,
      discount: 0,
      discountAmount: 0,
      detail: [{
        productCode: productCode,
        packageCode: '',
        qty: qty,
        total: pricePerUnit * qty,
        pricePerUnit: pricePerUnit
      }]
    };
  }
}

export const ordersApi = new OrdersApiClient();
