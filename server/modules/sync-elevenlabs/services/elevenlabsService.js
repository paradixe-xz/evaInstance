const axios = require('axios');
require('dotenv').config();

class ElevenLabsService {
  constructor() {
    this.apiKey = process.env.ELEVENLABS_API_KEY;
    this.baseURL = 'https://api.elevenlabs.io/v1';
    this.client = axios.create({
      baseURL: this.baseURL,
      headers: {
        'xi-api-key': this.apiKey,
        'Content-Type': 'application/json'
      },
      timeout: 30000, // 30 segundos de timeout
      maxRedirects: 5
    });
  }

  // Función helper para reintentos
  async retryRequest(requestFn, maxRetries = 3, delay = 1000) {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await requestFn();
      } catch (error) {
        console.warn(`⚠️  Intento ${attempt}/${maxRetries} falló:`, error.message);
        
        if (attempt === maxRetries) {
          throw error;
        }
        
        // Esperar antes del siguiente intento (backoff exponencial)
        const waitTime = delay * Math.pow(2, attempt - 1);
        console.log(`⏳ Esperando ${waitTime}ms antes del siguiente intento...`);
        await new Promise(resolve => setTimeout(resolve, waitTime));
      }
    }
  }

  async getConversations(cursor = null, agentId = null, callStartAfterUnix = null) {
    const requestFn = async () => {
      const params = {};
      if (cursor) {
        params.cursor = cursor;
      }
      if (agentId) {
        params.agent_id = agentId;
      }
      if (callStartAfterUnix) {
        params.call_start_after_unix = callStartAfterUnix;
      }

      const response = await this.client.get('/convai/conversations', { params });
      return response.data;
    };

    try {
      return await this.retryRequest(requestFn, 3, 2000);
    } catch (error) {
      console.error('❌ Error fetching conversations después de reintentos:', error.response?.data || error.message);
      throw error;
    }
  }

  async getAllConversations(agentId = null, callStartAfterUnix = null) {
    try {
      console.log(`🔄 Obteniendo todas las conversaciones${agentId ? ` para agente ${agentId}` : ''}${callStartAfterUnix ? ` desde ${new Date(callStartAfterUnix * 1000).toLocaleString()}` : ''}...`);
      
      let allConversations = [];
      let cursor = null;
      let hasMore = true;
      let pageCount = 0;
      const cursorsReceived = [];
      const paginationLog = [];

      while (hasMore) {
        pageCount++;
        console.log(`\n📄 Página ${pageCount}${cursor ? ` (usando cursor: ${cursor.substring(0, 30)}...)` : ' (primera página)'}`);
        
        try {
          const response = await this.getConversations(cursor, agentId, callStartAfterUnix);
          
          // Log detallado de la respuesta
          console.log(`   ✓ Conversaciones en esta página: ${response.conversations ? response.conversations.length : 0}`);
          console.log(`   ✓ has_more: ${response.has_more}`);
          console.log(`   ✓ cursor recibido: ${response.next_cursor ? response.next_cursor.substring(0, 30) + '...' : 'null'}`);
          
          // Guardar información de paginación
          const pageInfo = {
            page: pageCount,
            conversations_count: response.conversations ? response.conversations.length : 0,
            has_more: response.has_more,
            cursor_sent: cursor ? cursor.substring(0, 30) + '...' : null,
            cursor_received: response.next_cursor ? response.next_cursor.substring(0, 30) + '...' : null,
            full_cursor_received: response.next_cursor
          };
          paginationLog.push(pageInfo);
          
          if (response.next_cursor) {
            cursorsReceived.push({
              page: pageCount,
              cursor: response.next_cursor,
              preview: response.next_cursor.substring(0, 50) + '...'
            });
          }
          
          if (response.conversations && response.conversations.length > 0) {
            allConversations = allConversations.concat(response.conversations);
            console.log(`   ✓ Total acumulado: ${allConversations.length} conversaciones`);
          }
          
          // Verificar condición de parada
          hasMore = response.has_more === true;
          cursor = response.next_cursor;
          
          if (hasMore && !cursor) {
            console.warn('⚠️  API indica has_more=true pero no proporcionó cursor. Deteniendo paginación.');
            break;
          }
          
          if (!hasMore) {
            console.log(`✅ Paginación completada: has_more = false`);
          }

          // Pequeña pausa entre páginas para evitar rate limiting
          if (hasMore) {
            console.log('⏳ Pausa de 1 segundo entre páginas...');
            await new Promise(resolve => setTimeout(resolve, 1000));
          }

        } catch (pageError) {
          console.error(`❌ Error en página ${pageCount}:`, pageError.message);
          
          // Si es un error de conexión, intentar continuar con la siguiente página
          if (pageError.code === 'ECONNRESET' || pageError.code === 'ETIMEDOUT') {
            console.log('🔄 Error de conexión, intentando continuar...');
            
            // Si tenemos un cursor, intentar continuar
            if (cursor) {
              console.log('⏳ Esperando 5 segundos antes de continuar...');
              await new Promise(resolve => setTimeout(resolve, 5000));
              continue;
            } else {
              // Si no tenemos cursor, no podemos continuar
              break;
            }
          } else {
            // Para otros errores, detener la paginación
            throw pageError;
          }
        }
      }

      console.log(`\n🎯 Resumen de paginación:`);
      console.log(`   Total de páginas procesadas: ${pageCount}`);
      console.log(`   Total de conversaciones obtenidas: ${allConversations.length}`);
      console.log(`   Cursors recibidos: ${cursorsReceived.length}`);
      
      return {
        conversations: allConversations,
        total_pages: pageCount,
        total_conversations: allConversations.length,
        cursors_received: cursorsReceived,
        pagination_log: paginationLog
      };
    } catch (error) {
      console.error('❌ Error fetching all conversations:', error.response?.data || error.message);
      throw error;
    }
  }

  async getConversationDetails(conversationId) {
    const requestFn = async () => {
      const response = await this.client.get(`/convai/conversations/${conversationId}`);
      return response.data;
    };

    try {
      return await this.retryRequest(requestFn, 3, 1500);
    } catch (error) {
      console.error(`❌ Error fetching conversation ${conversationId} después de reintentos:`, error.response?.data || error.message);
      throw error;
    }
  }

  async getConversationAudio(conversationId) {
    const requestFn = async () => {
      const response = await this.client.get(`/convai/conversations/${conversationId}/audio`, {
        responseType: 'arraybuffer'
      });
      return response.data;
    };

    try {
      return await this.retryRequest(requestFn, 2, 2000);
    } catch (error) {
      console.error(`❌ Error fetching audio for conversation ${conversationId} después de reintentos:`, error.response?.data || error.message);
      throw error;
    }
  }

  async downloadAudio(url) {
    const requestFn = async () => {
      const response = await axios.get(url, {
        responseType: 'arraybuffer',
        headers: {
          'xi-api-key': this.apiKey
        },
        timeout: 30000
      });
      return response.data;
    };

    try {
      return await this.retryRequest(requestFn, 2, 2000);
    } catch (error) {
      console.error('❌ Error downloading audio después de reintentos:', error.message);
      throw error;
    }
  }
}

module.exports = ElevenLabsService;