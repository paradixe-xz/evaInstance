// API de Leads - Tous Software Corp
export interface LeadData {
  name: string;
  last_name: string;
  email: string;
  phone_number: string;
  media?: string;
  entervia?: string;
  product?: string;
  address?: string;
  city?: string;
  state?: string;
  zip?: string;
  zip4?: string;
  country?: string;
  comment?: string;
  addInfo?: {
    tscReference: string;
    data: Array<{
      tscReferenceCode: string;
      tscReferenceValue: string;
    }>;
  };
}

export interface LeadResponse {
  rescode: string;
  leadnum?: string;
}

export class LeadsApiClient {
  private readonly baseUrl = 'https://tsc-api-925835182876.us-east1.run.app/api/v1/1998010101';
  private readonly token = 'CVWM45F2ASA3O6SLDDFHP19JPULZ8FZL42PVKZU65ZHMRUPVSEFBK11Y5GPOXOA0';

  private getHeaders() {
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${this.token}`
    };
  }

  async createLead(leadData: LeadData): Promise<LeadResponse> {
    try {
      console.log('🔄 Creando lead:', leadData);
      
      const response = await fetch(`${this.baseUrl}/leads`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(leadData)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      console.log('✅ Lead creado:', result);
      return result;
    } catch (error) {
      console.error('❌ Error creando lead:', error);
      throw error;
    }
  }

  async updateLead(leadNum: string, updateData: Partial<LeadData>): Promise<LeadResponse> {
    try {
      console.log('🔄 Actualizando lead:', leadNum, updateData);
      
      const response = await fetch(`${this.baseUrl}/leads/${leadNum}`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(updateData)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      console.log('✅ Lead actualizado:', result);
      return result;
    } catch (error) {
      console.error('❌ Error actualizando lead:', error);
      throw error;
    }
  }
}

export const leadsApi = new LeadsApiClient();
