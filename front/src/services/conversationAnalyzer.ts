import { type LeadData } from './leadsApi';
import { type OrderData } from './ordersApi';
import { type PaymentData } from './paymentsApi';

export interface ConversationContext {
  messages: Array<{ role: 'user' | 'assistant'; content: string; timestamp: Date }>;
  extractedData: Partial<LeadData>;
  extractedOrderData: Partial<OrderData>;
  extractedPaymentData: Partial<PaymentData>;
  detectedIntent: 'create_lead' | 'update_lead' | 'create_order' | 'process_payment' | 'general_chat' | 'gathering_info';
  confidence: number;
  missingFields: string[];
  leadNumber?: string;
  orderNumber?: string;
  paymentAmount?: number;
}

export class ConversationAnalyzer {
  private requiredFields: (keyof LeadData)[] = ['name', 'last_name', 'email', 'phone_number'];
  
  analyzeConversation(messages: Array<{ role: 'user' | 'assistant'; content: string; timestamp: Date }>): ConversationContext {
    const context: ConversationContext = {
      messages,
      extractedData: {},
      extractedOrderData: {},
      extractedPaymentData: {},
      detectedIntent: 'general_chat',
      confidence: 0,
      missingFields: [],
      leadNumber: undefined,
      orderNumber: undefined,
      paymentAmount: undefined
    };

    // Analizar toda la conversación
    const fullConversation = messages.map(m => m.content).join(' ');
    
    // Detectar intención
    context.detectedIntent = this.detectIntent(fullConversation);
    
    // Extraer datos si hay intención de lead
    if (context.detectedIntent === 'create_lead' || context.detectedIntent === 'update_lead') {
      context.extractedData = this.extractLeadData(fullConversation);
      context.missingFields = this.getMissingFields(context.extractedData);
      context.confidence = this.calculateConfidence(context.extractedData, context.detectedIntent);
      
      // Buscar número de lead para actualización
      if (context.detectedIntent === 'update_lead') {
        context.leadNumber = this.extractLeadNumber(fullConversation);
      }
    }
    
    // Extraer datos si hay intención de orden
    if (context.detectedIntent === 'create_order') {
      context.extractedOrderData = this.extractOrderData(fullConversation);
      context.confidence = this.calculateOrderConfidence(context.extractedOrderData);
    }
    
    // Extraer datos si hay intención de pago
    if (context.detectedIntent === 'process_payment') {
      context.extractedPaymentData = this.extractPaymentData(fullConversation);
      context.confidence = this.calculatePaymentConfidence(context.extractedPaymentData);
      context.paymentAmount = this.extractPaymentAmount(fullConversation);
    }

    return context;
  }

  private detectIntent(conversation: string): ConversationContext['detectedIntent'] {
    const lowerConv = conversation.toLowerCase();
    
    // Palabras clave para crear lead
    const createKeywords = [
      'crear lead', 'nuevo lead', 'registrar cliente', 'nuevo cliente',
      'crear contacto', 'agregar cliente', 'registrar lead',
      'quiero registrar', 'necesito crear', 'nuevo prospecto'
    ];
    
    // Palabras clave para actualizar lead
    const updateKeywords = [
      'actualizar lead', 'modificar lead', 'cambiar datos',
      'actualizar cliente', 'modificar cliente', 'editar lead',
      'lead número', 'lead #', 'actualizar información'
    ];
    
    // Palabras clave para crear orden
    const orderKeywords = [
      'crear orden', 'nueva orden', 'hacer pedido', 'quiero comprar',
      'realizar compra', 'hacer order', 'generar orden', 'procesar orden',
      'quiero ordenar', 'necesito comprar', 'hacer una compra',
      'crear order', 'nueva order', 'pedido', 'compra'
    ];
    
    // Palabras clave para procesar pago
    const paymentKeywords = [
      'procesar pago', 'hacer pago', 'pagar', 'payment', 'tarjeta',
      'tarjeta de crédito', 'credit card', 'pago con tarjeta',
      'quiero pagar', 'realizar pago', 'efectuar pago', 'cobrar',
      'charge', 'billing', 'facturar', 'mi tarjeta es'
    ];
    
    // Palabras clave para recopilar información
    const gatheringKeywords = [
      'mi nombre es', 'me llamo', 'soy', 'mi email es',
      'mi teléfono es', 'mi número es', 'vivo en',
      'mi dirección es', 'trabajo en', 'mi empresa es'
    ];

    if (updateKeywords.some(keyword => lowerConv.includes(keyword))) {
      return 'update_lead';
    }
    
    if (paymentKeywords.some(keyword => lowerConv.includes(keyword))) {
      return 'process_payment';
    }
    
    if (orderKeywords.some(keyword => lowerConv.includes(keyword))) {
      return 'create_order';
    }
    
    if (createKeywords.some(keyword => lowerConv.includes(keyword))) {
      return 'create_lead';
    }
    
    if (gatheringKeywords.some(keyword => lowerConv.includes(keyword))) {
      return 'gathering_info';
    }
    
    return 'general_chat';
  }

  private extractLeadData(conversation: string): Partial<LeadData> {
    const data: Partial<LeadData> = {};
    
    // Extraer nombre
    const namePatterns = [
      /mi nombre es ([a-záéíóúñ\s]+)/i,
      /me llamo ([a-záéíóúñ\s]+)/i,
      /soy ([a-záéíóúñ\s]+)/i,
      /nombre:\s*([a-záéíóúñ\s]+)/i
    ];
    
    for (const pattern of namePatterns) {
      const match = conversation.match(pattern);
      if (match) {
        const fullName = match[1].trim();
        const nameParts = fullName.split(' ');
        data.name = nameParts[0];
        if (nameParts.length > 1) {
          data.last_name = nameParts.slice(1).join(' ');
        }
        break;
      }
    }
    
    // Extraer email
    const emailPattern = /([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/;
    const emailMatch = conversation.match(emailPattern);
    if (emailMatch) {
      data.email = emailMatch[1];
    }
    
    // Extraer teléfono
    const phonePatterns = [
      /(?:teléfono|telefono|número|phone)[\s:]*([0-9\-\(\)\s]{10,})/i,
      /([0-9]{3}[\-\s]?[0-9]{3}[\-\s]?[0-9]{4})/,
      /(\([0-9]{3}\)\s?[0-9]{3}[\-\s]?[0-9]{4})/
    ];
    
    for (const pattern of phonePatterns) {
      const match = conversation.match(pattern);
      if (match) {
        data.phone_number = match[1].replace(/[\s\-\(\)]/g, '');
        break;
      }
    }
    
    // Extraer ciudad
    const cityPatterns = [
      /vivo en ([a-záéíóúñ\s]+)/i,
      /ciudad:\s*([a-záéíóúñ\s]+)/i,
      /de ([a-záéíóúñ\s]+)/i
    ];
    
    for (const pattern of cityPatterns) {
      const match = conversation.match(pattern);
      if (match) {
        data.city = match[1].trim();
        break;
      }
    }
    
    // Extraer empresa/producto
    const companyPatterns = [
      /trabajo en ([a-záéíóúñ\s]+)/i,
      /empresa:\s*([a-záéíóúñ\s]+)/i,
      /producto:\s*([a-záéíóúñ\s]+)/i
    ];
    
    for (const pattern of companyPatterns) {
      const match = conversation.match(pattern);
      if (match) {
        data.product = match[1].trim();
        break;
      }
    }

    // Configurar valores por defecto
    data.media = 'WEB';
    data.entervia = '9548092011';
    data.comment = 'Lead creado via Eva AI Chat';
    data.addInfo = {
      tscReference: 'DEFAULT',
      data: [
        { tscReferenceCode: 'TSCREF1', tscReferenceValue: 'EVA_AI' },
        { tscReferenceCode: 'TSCREF2', tscReferenceValue: 'CHAT_BOT' }
      ]
    };
    
    return data;
  }

  private extractOrderData(conversation: string): Partial<OrderData> {
    const data: Partial<OrderData> = {};
    
    // Extraer información del cliente (reutilizar lógica de leads)
    const leadData = this.extractLeadData(conversation);
    
    if (leadData.name) data.customerName = leadData.name;
    if (leadData.last_name) data.customerLastname = leadData.last_name;
    if (leadData.phone_number) data.phone1 = leadData.phone_number;
    
    // Extraer dirección específica para órdenes
    if (leadData.city || leadData.address) {
      data.direction = {
        address: leadData.address || '',
        city: leadData.city || '',
        state: 'FL', // Por defecto
        zip: '',
        zip4: '',
        country: 'US',
        urbanization: ''
      };
    }
    
    // Extraer información de productos
    const productPatterns = [
      /producto[\s:]*([a-zA-Z0-9\s]+)/i,
      /quiero comprar[\s:]*([a-zA-Z0-9\s]+)/i,
      /necesito[\s:]*([a-zA-Z0-9\s]+)/i,
      /código[\s:]*([a-zA-Z0-9]+)/i
    ];
    
    for (const pattern of productPatterns) {
      const match = conversation.match(pattern);
      if (match) {
        data.detail = [{
          productCode: match[1].trim().toUpperCase(),
          packageCode: '',
          qty: 1,
          total: 100,
          pricePerUnit: 100
        }];
        break;
      }
    }
    
    // Extraer cantidad
    const qtyPatterns = [
      /cantidad[\s:]*([0-9]+)/i,
      /([0-9]+)\s*unidades?/i,
      /([0-9]+)\s*piezas?/i
    ];
    
    for (const pattern of qtyPatterns) {
      const match = conversation.match(pattern);
      if (match && data.detail) {
        const qty = parseInt(match[1]);
        data.detail[0].qty = qty;
        data.detail[0].total = (data.detail[0].pricePerUnit || 100) * qty;
        break;
      }
    }
    
    // Configurar valores por defecto
    data.createBy = 'EVA_AI';
    data.seller = 'EVA_AI';
    data.sellerName = 'Eva AI Assistant';
    data.company = '90001';
    data.department = '90001';
    data.ordenDate = new Date().toISOString().split('T')[0];
    data.comment = 'Orden creada via Eva AI Chat';
    data.payterm = 'PREPAID';
    data.shipvia = 'USPS';
    
    // Calcular fechas
    const deliveryDate = new Date();
    deliveryDate.setDate(deliveryDate.getDate() + 7);
    data.deliveryDate = deliveryDate.toISOString().split('T')[0];
    
    // Calcular totales
    if (data.detail && data.detail.length > 0) {
      const total = data.detail.reduce((sum, item) => sum + (item.total || 0), 0);
      data.subTotal = total;
      data.total = total;
      data.saleTax = 0;
      data.taxes = 0;
      data.paid = 0;
      data.discount = 0;
      data.discountAmount = 0;
    }
    
    return data;
  }

  private calculateOrderConfidence(orderData: Partial<OrderData>): number {
    let score = 0;
    const maxScore = 4;
    
    // Verificar campos esenciales
    if (orderData.customerName) score++;
    if (orderData.customerLastname) score++;
    if (orderData.phone1) score++;
    if (orderData.detail && orderData.detail.length > 0) score++;
    
    return (score / maxScore) * 100;
  }

  private extractPaymentData(conversation: string): Partial<PaymentData> {
    const data: Partial<PaymentData> = {};
    
    // Extraer información del cliente (reutilizar lógica de leads)
    const leadData = this.extractLeadData(conversation);
    
    if (leadData.name) data.customerName = leadData.name;
    if (leadData.last_name) data.customerLastname = leadData.last_name;
    if (leadData.phone_number) data.phone1 = leadData.phone_number;
    if (leadData.email) data.email = leadData.email;
    
    // Extraer dirección para pagos
    if (leadData.city || leadData.address) {
      data.direction = {
        address: leadData.address || '',
        city: leadData.city || '',
        state: 'FL', // Por defecto
        zip: '',
        zip4: '0001',
        country: 'US',
        urbanization: ''
      };
    }
    
    // Extraer número de tarjeta
    const cardPatterns = [
      /tarjeta[\s:]*([0-9\s]{13,19})/i,
      /card[\s:]*([0-9\s]{13,19})/i,
      /número[\s:]*([0-9\s]{13,19})/i,
      /([0-9]{4}[\s-]?[0-9]{4}[\s-]?[0-9]{4}[\s-]?[0-9]{3,4})/
    ];
    
    for (const pattern of cardPatterns) {
      const match = conversation.match(pattern);
      if (match) {
        data.cardnumber = match[1].replace(/[\s-]/g, '');
        break;
      }
    }
    
    // Extraer fecha de expiración
    const expPatterns = [
      /exp[\s:]*([0-9]{2}\/[0-9]{2})/i,
      /vence[\s:]*([0-9]{2}\/[0-9]{2})/i,
      /([0-9]{2}\/[0-9]{2})/
    ];
    
    for (const pattern of expPatterns) {
      const match = conversation.match(pattern);
      if (match) {
        data.expdate = match[1];
        break;
      }
    }
    
    // Extraer CVV
    const cvvPatterns = [
      /cvv[\s:]*([0-9]{3,4})/i,
      /código[\s:]*([0-9]{3,4})/i,
      /seguridad[\s:]*([0-9]{3,4})/i
    ];
    
    for (const pattern of cvvPatterns) {
      const match = conversation.match(pattern);
      if (match) {
        data.cvv = match[1];
        break;
      }
    }
    
    // Extraer número de orden
    const orderPatterns = [
      /orden[\s#:]*([0-9]+)/i,
      /order[\s#:]*([0-9]+)/i,
      /pedido[\s#:]*([0-9]+)/i
    ];
    
    for (const pattern of orderPatterns) {
      const match = conversation.match(pattern);
      if (match) {
        data.ordernum = match[1];
        break;
      }
    }
    
    // Configurar valores por defecto
    data.processpayment = 'Y';
    data.seller = 'EVA_AI';
    data.sellerName = 'Eva AI Assistant';
    data.company = '1998010101';
    data.department = '100';
    data.comment = 'Pago procesado via Eva AI Chat';
    data.payterm = 'CC';
    data.paytype = 'CC';
    data.merchat = 'TSCTEST';
    
    return data;
  }

  private calculatePaymentConfidence(paymentData: Partial<PaymentData>): number {
    let score = 0;
    const maxScore = 7;
    
    // Verificar campos esenciales para pago
    if (paymentData.customerName) score++;
    if (paymentData.customerLastname) score++;
    if (paymentData.email) score++;
    if (paymentData.cardnumber) score++;
    if (paymentData.expdate) score++;
    if (paymentData.cvv) score++;
    if (paymentData.ordernum) score++;
    
    return (score / maxScore) * 100;
  }

  private extractPaymentAmount(conversation: string): number | undefined {
    const amountPatterns = [
      /monto[\s:]*\$?([0-9]+\.?[0-9]*)/i,
      /cantidad[\s:]*\$?([0-9]+\.?[0-9]*)/i,
      /total[\s:]*\$?([0-9]+\.?[0-9]*)/i,
      /\$([0-9]+\.?[0-9]*)/,
      /([0-9]+\.?[0-9]*)\s*dólares?/i,
      /([0-9]+\.?[0-9]*)\s*usd/i
    ];
    
    for (const pattern of amountPatterns) {
      const match = conversation.match(pattern);
      if (match) {
        return parseFloat(match[1]);
      }
    }
    
    return undefined;
  }

  private extractLeadNumber(conversation: string): string | undefined {
    const leadPatterns = [
      /lead\s*#?\s*([0-9]+)/i,
      /número\s*([0-9]+)/i,
      /lead\s*número\s*([0-9]+)/i
    ];
    
    for (const pattern of leadPatterns) {
      const match = conversation.match(pattern);
      if (match) {
        return match[1];
      }
    }
    
    return undefined;
  }

  private getMissingFields(data: Partial<LeadData>): string[] {
    const missing: string[] = [];
    
    for (const field of this.requiredFields) {
      if (!data[field]) {
        missing.push(field);
      }
    }
    
    return missing;
  }

  private calculateConfidence(data: Partial<LeadData>, intent: ConversationContext['detectedIntent']): number {
    if (intent === 'general_chat') return 0;
    
    const totalFields = this.requiredFields.length;
    const filledFields = this.requiredFields.filter(field => data[field]).length;
    
    return (filledFields / totalFields) * 100;
  }

  shouldCreateLead(context: ConversationContext): boolean {
    return (
      context.detectedIntent === 'create_lead' &&
      context.confidence >= 75 && // Al menos 75% de los campos requeridos
      context.missingFields.length === 0
    );
  }

  shouldUpdateLead(context: ConversationContext): boolean {
    return (
      context.detectedIntent === 'update_lead' &&
      context.leadNumber !== undefined &&
      Object.keys(context.extractedData).length > 0
    );
  }

  shouldCreateOrder(context: ConversationContext): boolean {
    return (
      context.detectedIntent === 'create_order' &&
      context.confidence >= 75 && // Al menos 75% de los campos requeridos
      context.extractedOrderData.customerName !== undefined &&
      context.extractedOrderData.customerLastname !== undefined &&
      context.extractedOrderData.phone1 !== undefined
    );
  }

  shouldProcessPayment(context: ConversationContext): boolean {
    return (
      context.detectedIntent === 'process_payment' &&
      context.confidence >= 85 && // Al menos 85% de los campos requeridos (más estricto para pagos)
      context.extractedPaymentData.customerName !== undefined &&
      context.extractedPaymentData.customerLastname !== undefined &&
      context.extractedPaymentData.email !== undefined &&
      context.extractedPaymentData.cardnumber !== undefined &&
      context.extractedPaymentData.expdate !== undefined &&
      context.extractedPaymentData.cvv !== undefined &&
      context.extractedPaymentData.ordernum !== undefined
    );
  }

  generateMissingFieldsPrompt(missingFields: string[]): string {
    const fieldNames: Record<string, string> = {
      name: 'nombre',
      last_name: 'apellido',
      email: 'correo electrónico',
      phone_number: 'número de teléfono'
    };

    const missingNames = missingFields.map(field => fieldNames[field] || field);
    
    if (missingNames.length === 1) {
      return `Para completar tu registro, necesito tu ${missingNames[0]}.`;
    } else if (missingNames.length === 2) {
      return `Para completar tu registro, necesito tu ${missingNames.join(' y ')}.`;
    } else {
      const last = missingNames.pop();
      return `Para completar tu registro, necesito tu ${missingNames.join(', ')} y ${last}.`;
    }
  }
}

export const conversationAnalyzer = new ConversationAnalyzer();
