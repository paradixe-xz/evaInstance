const ElevenLabsService = require('./elevenlabsService');
const Conversation = require('../models/Conversation');
const fs = require('fs');
const path = require('path');

class SyncService {
  constructor() {
    this.elevenLabsService = new ElevenLabsService();
  }

  async syncAllConversations(agentId = null, callStartAfterUnix = null) {
    try {
      console.log(`🚀 Iniciando sincronización de conversaciones${agentId ? ` para agente ${agentId}` : ''}${callStartAfterUnix ? ` desde ${new Date(callStartAfterUnix * 1000).toLocaleString()}` : ''}...`);
      
      // Obtener todas las conversaciones con paginación
      const conversationsData = await this.elevenLabsService.getAllConversations(agentId, callStartAfterUnix);
      const conversations = conversationsData.conversations || [];

      console.log(`\n📊 Datos de paginación obtenidos:`);
      console.log(`   Conversaciones encontradas: ${conversations.length}`);
      console.log(`   Páginas procesadas: ${conversationsData.total_pages}`);
      console.log(`   Cursors recibidos: ${conversationsData.cursors_received.length}`);

      if (process.env.EXPORT_CONVERSATIONS_CSV === 'true') {
        try {
          await this.exportConversationsToCsv(conversations, agentId, callStartAfterUnix);
        } catch (csvError) {
          console.error('⚠️  Error al exportar conversaciones a CSV:', csvError.message);
        }
      }

      const results = {
        total: conversations.length,
        synced: 0,
        errors: [],
        warnings: [],
        agent_id: agentId,
        total_pages: conversationsData.total_pages,
        cursors_received: conversationsData.cursors_received,
        pagination_log: conversationsData.pagination_log
      };

      console.log(`\n🔄 Iniciando sincronización de ${conversations.length} conversaciones...`);
      
      for (const conversation of conversations) {
        try {
          await this.syncConversation(conversation);
          results.synced++;
          
          // Mostrar progreso cada 5 conversaciones
          if (results.synced % 5 === 0 || results.synced === results.total) {
            console.log(`   📈 Progreso: ${results.synced}/${results.total} conversaciones sincronizadas`);
          }
        } catch (error) {
          console.error(`❌ Error sincronizando conversación ${conversation.conversation_id}:`, error.message);
          results.errors.push({
            conversationId: conversation.conversation_id,
            error: error.message
          });
        }
      }

      console.log('\n✅ Sincronización completada');
      return results;
    } catch (error) {
      console.error('❌ Error en sincronización:', error.message);
      throw error;
    }
  }

  // Función helper para procesar transcript
  processTranscript(transcript) {
    if (!transcript) {
      return null;
    }
    
    if (typeof transcript === 'string') {
      return transcript;
    }
    
    if (Array.isArray(transcript)) {
      return transcript.map(item => {
        if (typeof item === 'string') {
          return item;
        }
        if (typeof item === 'object' && item.text) {
          return item.text;
        }
        if (typeof item === 'object' && item.content) {
          return item.content;
        }
        return JSON.stringify(item);
      }).join(' ');
    }
    
    if (typeof transcript === 'object') {
      if (transcript.text) {
        return transcript.text;
      }
      if (transcript.content) {
        return transcript.content;
      }
      if (transcript.messages && Array.isArray(transcript.messages)) {
        return transcript.messages.map(msg => {
          if (typeof msg === 'string') return msg;
          if (msg.text) return msg.text;
          if (msg.content) return msg.content;
          return JSON.stringify(msg);
        }).join(' ');
      }
      return JSON.stringify(transcript);
    }
    
    return String(transcript);
  }

  async syncConversation(conversationData) {
    try {
      const existingConversation = await Conversation.findByPk(conversationData.conversation_id);
      
      let details = null;
      try {
        details = await this.elevenLabsService.getConversationDetails(conversationData.conversation_id);
      } catch (detailsError) {
        console.warn(`⚠️  No se pudieron obtener detalles para conversación ${conversationData.conversation_id}:`, detailsError.message);
        // Continuar con datos básicos si no se pueden obtener detalles
        details = {};
      }

      const conversationRecord = {
        id: conversationData.conversation_id,
        agent_id: conversationData.agent_id || details.agent_id,
        conversation_id: conversationData.conversation_id,
        status: details?.analysis?.call_successful,
        lead_number: details?.metadata?.phone_call?.external_number || details.user_id,
        evaluation_criteria_result: details?.analysis?.evaluation_criteria_results?.result,
        evaluation_criteria_rationale: details?.analysis?.evaluation_criteria_results?.rationale,
        data_collection_client_type: details?.analysis?.data_collection_results?.tc?.value,
        data_collection_meta: details?.analysis?.data_collection_results?.meta?.value,
        data_collection_emb: details?.analysis?.data_collection_results?.emb?.value,
        data_collection_result_call: details?.analysis?.data_collection_results?.res?.value,
        data_collection_cuota: details?.analysis?.data_collection_results?.cuota?.value,
        data_collection_edad: details?.analysis?.data_collection_results?.edad?.value,
        data_collection_ok: details?.analysis?.data_collection_results?.ok?.value,
        data_collection_number: details?.analysis?.data_collection_results?.number?.value,
        data_collection_neto: details?.analysis?.data_collection_results?.neto?.value,
        data_collection_canal: details?.analysis?.data_collection_results?.canal?.value,
        data_collection_mot: details?.analysis?.data_collection_results?.mot?.value,
        transcript: details.transcript ? (typeof details.transcript === 'string' ? JSON.parse(details.transcript) : details.transcript) : null
      };

      if (existingConversation) {
        await existingConversation.update(conversationRecord);
      } else {
        await Conversation.create(conversationRecord);
      }

      return conversationRecord;
    } catch (error) {
      console.error(`❌ Error procesando conversación ${conversationData.conversation_id}:`, error.message);
      throw error;
    }
  }

  async exportConversationsToCsv(conversations, agentId, callStartAfterUnix) {
    if (!Array.isArray(conversations) || conversations.length === 0) {
      console.log('ℹ️  No hay conversaciones para exportar a CSV.');
      return;
    }

    const exportDir = path.resolve(__dirname, '..', 'exports');
    await fs.promises.mkdir(exportDir, { recursive: true });

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const parts = ['conversations'];
    if (agentId) {
      parts.push(agentId);
    }
    if (callStartAfterUnix) {
      parts.push(`from-${callStartAfterUnix}`);
    }
    const fileName = `${parts.join('_')}_${timestamp}.csv`;
    const filePath = path.join(exportDir, fileName);

    // Definir los campos que queremos incluir en el CSV
    const headers = [
      'conversation_id',
      'agent_id',
      'lead_number',
      'status',
      'evaluation_criteria_result',
      'evaluation_criteria_rationale',
      'data_collection_client_type',
      'data_collection_meta',
      'data_collection_emb',
      'data_collection_result_call',
      'data_collection_cuota',
      'data_collection_edad',
      'data_collection_ok',
      'data_collection_number',
      'data_collection_neto',
      'data_collection_canal',
      'data_collection_mot',
      'transcript_text',
      'full_conversation_json'
    ];

    const escapeCsvValue = (value) => {
      if (value === null || value === undefined) {
        return '';
      }
      let normalized = value;
      if (typeof normalized === 'object') {
        try {
          normalized = JSON.stringify(normalized, null, 2)
            .replace(/\\"/g, '""')
            .replace(/\n/g, '\\n')
            .replace(/\r/g, '\\r');
        } catch (e) {
          normalized = String(normalized);
        }
      }
      const str = String(normalized);
      const needsQuotes = /[\",\n]/.test(str);
      const escaped = str.replace(/"/g, '""');
      return needsQuotes ? `"${escaped}"` : escaped;
    };

    const lines = [headers.join(',')];
    
    for (const conversation of conversations) {
      try {
        // Obtener los detalles completos de la conversación
        let details = {};
        try {
          details = await this.elevenLabsService.getConversationDetails(conversation.conversation_id || conversation.id);
        } catch (error) {
          console.warn(`⚠️  No se pudieron obtener detalles para conversación ${conversation.conversation_id || conversation.id}:`, error.message);
        }

        // Procesar el transcript para obtener texto plano
        let transcriptText = '';
        if (details.transcript) {
          if (Array.isArray(details.transcript)) {
            transcriptText = details.transcript.map(item => {
              if (typeof item === 'string') return item;
              if (item.text) return item.text;
              if (item.content) return item.content;
              return JSON.stringify(item);
            }).join(' ');
          } else if (typeof details.transcript === 'object') {
            transcriptText = JSON.stringify(details.transcript, null, 2);
          } else {
            transcriptText = details.transcript;
          }
        } else if (conversation.transcript) {
          transcriptText = Array.isArray(conversation.transcript) 
            ? conversation.transcript.map(t => t.text || JSON.stringify(t)).join(' ')
            : conversation.transcript;
        }

        // Crear la fila con los datos
        const row = [
          conversation.conversation_id || conversation.id,
          conversation.agent_id || details.agent_id || '',
          conversation.lead_number || details.metadata?.phone_call?.external_number || details.user_id || '',
          conversation.status || details.analysis?.call_successful || '',
          conversation.evaluation_criteria_result || details.analysis?.evaluation_criteria_results?.result || '',
          conversation.evaluation_criteria_rationale || details.analysis?.evaluation_criteria_results?.rationale || '',
          conversation.data_collection_client_type || details.analysis?.data_collection_results?.tc?.value || '',
          conversation.data_collection_meta || details.analysis?.data_collection_results?.meta?.value || '',
          conversation.data_collection_emb || details.analysis?.data_collection_results?.emb?.value || '',
          conversation.data_collection_result_call || details.analysis?.data_collection_results?.res?.value || '',
          conversation.data_collection_cuota || details.analysis?.data_collection_results?.cuota?.value || '',
          conversation.data_collection_edad || details.analysis?.data_collection_results?.edad?.value || '',
          conversation.data_collection_ok || details.analysis?.data_collection_results?.ok?.value || '',
          conversation.data_collection_number || details.analysis?.data_collection_results?.number?.value || '',
          conversation.data_collection_neto || details.analysis?.data_collection_results?.neto?.value || '',
          conversation.data_collection_canal || details.analysis?.data_collection_results?.canal?.value || '',
          conversation.data_collection_mot || details.analysis?.data_collection_results?.mot?.value || '',
          transcriptText,
          JSON.stringify(details, null, 2) // JSON completo de la conversación
        ];

        lines.push(row.map(cell => escapeCsvValue(cell)).join(','));
      } catch (error) {
        console.error(`❌ Error procesando conversación para CSV:`, error);
      }
    }

    // Escribir el archivo
    await fs.promises.writeFile(filePath, lines.join('\n'), 'utf8');
    console.log(`📁 Conversaciones exportadas a CSV: ${filePath}`);
    
    // Crear un archivo JSON con los datos completos
    try {
      const jsonFilePath = filePath.replace(/\.csv$/, '.json');
      const jsonData = conversations.map(conv => ({
        ...conv,
        // Incluir datos adicionales si están disponibles
        full_details: conv.full_details || {}
      }));
      
      await fs.promises.writeFile(jsonFilePath, JSON.stringify(jsonData, null, 2), 'utf8');
      console.log(`📁 Datos completos exportados a JSON: ${jsonFilePath}`);
    } catch (jsonError) {
      console.error('⚠️  Error al exportar a JSON:', jsonError.message);
    }
  }
}

module.exports = SyncService;