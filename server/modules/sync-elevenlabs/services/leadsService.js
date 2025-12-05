const Conversation = require('../models/Conversation');
const { Op } = require('sequelize');

class LeadsService {
  constructor() {}

  // Determinar si un lead es efectivo basado en los criterios de evaluación
  isEffectiveLead(conversation) {
    // Un lead es efectivo si:
    // 1. El resultado de evaluación es positivo
    // 2. La llamada fue exitosa
    // 3. Se recolectaron datos importantes
    
    const hasPositiveEvaluation = conversation.evaluation_criteria_result === 'true' || 
                                 conversation.evaluation_criteria_result === 'yes' ||
                                 conversation.evaluation_criteria_result === 'efectivo' ||
                                 conversation.evaluation_criteria_result === 'qualified';
    
    const hasSuccessfulCall = conversation.status === 'true' || 
                             conversation.status === 'completed' ||
                             conversation.status === 'successful';
    
    const hasImportantData = conversation.data_collection_ok === 'true' ||
                            conversation.data_collection_ok === 'yes' ||
                            (conversation.data_collection_edad && conversation.data_collection_number);
    
    return hasPositiveEvaluation || hasSuccessfulCall || hasImportantData;
  }

  // Extraer información del lead desde el transcript
  extractLeadInfoFromTranscript(transcript) {
    const leadInfo = {
      nombre: null,
      cedula: null,
      telefono: null,
      edad: null
    };

    if (!transcript) return leadInfo;

    let transcriptText = '';
    
    // Convertir transcript a texto plano
    if (typeof transcript === 'string') {
      transcriptText = transcript;
    } else if (Array.isArray(transcript)) {
      transcriptText = transcript.map(item => {
        if (typeof item === 'string') return item;
        if (item.text) return item.text;
        if (item.content) return item.content;
        return JSON.stringify(item);
      }).join(' ');
    } else if (typeof transcript === 'object') {
      transcriptText = JSON.stringify(transcript);
    }

    // Buscar patrones en el texto
    const text = transcriptText.toLowerCase();

    // Buscar nombre (patrones comunes)
    const nombrePatterns = [
      /mi nombre es ([a-záéíóúñ\s]+)/i,
      /me llamo ([a-záéíóúñ\s]+)/i,
      /soy ([a-záéíóúñ\s]+)/i,
      /nombre[:\s]+([a-záéíóúñ\s]+)/i
    ];

    for (const pattern of nombrePatterns) {
      const match = transcriptText.match(pattern);
      if (match && match[1]) {
        leadInfo.nombre = match[1].trim();
        break;
      }
    }

    // Buscar cédula
    const cedulaPatterns = [
      /cédula[:\s]+(\d{7,10})/i,
      /cedula[:\s]+(\d{7,10})/i,
      /documento[:\s]+(\d{7,10})/i,
      /identificación[:\s]+(\d{7,10})/i,
      /\b(\d{8,10})\b/g // Números de 8-10 dígitos
    ];

    for (const pattern of cedulaPatterns) {
      const match = transcriptText.match(pattern);
      if (match && match[1]) {
        leadInfo.cedula = match[1];
        break;
      }
    }

    // Buscar teléfono
    const telefonoPatterns = [
      /teléfono[:\s]+(\d{10,})/i,
      /telefono[:\s]+(\d{10,})/i,
      /celular[:\s]+(\d{10,})/i,
      /número[:\s]+(\d{10,})/i,
      /\b(\d{10,})\b/g
    ];

    for (const pattern of telefonoPatterns) {
      const match = transcriptText.match(pattern);
      if (match && match[1]) {
        leadInfo.telefono = match[1];
        break;
      }
    }

    // Buscar edad
    const edadPatterns = [
      /edad[:\s]+(\d{1,3})/i,
      /tengo[:\s]+(\d{1,3})[:\s]*años/i,
      /(\d{1,3})[:\s]*años/i
    ];

    for (const pattern of edadPatterns) {
      const match = transcriptText.match(pattern);
      if (match && match[1]) {
        const edad = parseInt(match[1]);
        if (edad >= 18 && edad <= 100) {
          leadInfo.edad = edad;
          break;
        }
      }
    }

    return leadInfo;
  }

  // Obtener todos los leads efectivos
  async getEffectiveLeads(agentId = null) {
    try {
      console.log('🎯 === ANÁLISIS DE LEADS EFECTIVOS ===');
      console.log('='.repeat(50));

      let whereClause = {};
      if (agentId) {
        whereClause.agent_id = agentId;
        console.log(`📋 Filtrando por agente: ${agentId}`);
      }

      // Obtener todas las conversaciones
      const conversations = await Conversation.findAll({
        where: whereClause,
        order: [['id', 'DESC']]
      });

      console.log(`📊 Total de conversaciones analizadas: ${conversations.length}`);

      const effectiveLeads = [];
      let processedCount = 0;

      for (const conversation of conversations) {
        processedCount++;
        
        // Mostrar progreso cada 10 conversaciones
        if (processedCount % 10 === 0) {
          console.log(`   📈 Progreso: ${processedCount}/${conversations.length} conversaciones analizadas`);
        }

        if (this.isEffectiveLead(conversation)) {
          // Extraer información del transcript
          const leadInfo = this.extractLeadInfoFromTranscript(conversation.transcript);
          
          const effectiveLead = {
            conversation_id: conversation.conversation_id,
            lead_number: conversation.lead_number,
            agent_id: conversation.agent_id,
            status: conversation.status,
            evaluation_result: conversation.evaluation_criteria_result,
            evaluation_rationale: conversation.evaluation_criteria_rationale,
            
            // Datos recolectados por el sistema
            edad_sistema: conversation.data_collection_edad,
            numero_sistema: conversation.data_collection_number,
            cliente_tipo: conversation.data_collection_client_type,
            resultado_llamada: conversation.data_collection_result_call,
            
            // Datos extraídos del transcript
            nombre_extraido: leadInfo.nombre,
            cedula_extraida: leadInfo.cedula,
            telefono_extraido: leadInfo.telefono,
            edad_extraida: leadInfo.edad,
            
            // Datos finales (prioridad: sistema > extraído)
            telefono_final: conversation.lead_number || conversation.data_collection_number || leadInfo.telefono,
            nombre_final: leadInfo.nombre,
            edad_final: conversation.data_collection_edad || leadInfo.edad,
            cedula_final: leadInfo.cedula
          };

          effectiveLeads.push(effectiveLead);
        }
      }

      console.log(`\n✅ Análisis completado`);
      console.log(`🎯 Leads efectivos encontrados: ${effectiveLeads.length}`);
      console.log(`📊 Tasa de efectividad: ${((effectiveLeads.length / conversations.length) * 100).toFixed(2)}%`);

      return effectiveLeads;
    } catch (error) {
      console.error('❌ Error analizando leads:', error.message);
      throw error;
    }
  }

  // Mostrar leads efectivos en consola con formato bonito
  async showEffectiveLeads(agentId = null) {
    try {
      const effectiveLeads = await this.getEffectiveLeads(agentId);

      if (effectiveLeads.length === 0) {
        console.log('\n📭 No se encontraron leads efectivos');
        return;
      }

      console.log('\n' + '='.repeat(80));
      console.log('🏆 LEADS EFECTIVOS ENCONTRADOS');
      console.log('='.repeat(80));

      effectiveLeads.forEach((lead, index) => {
        console.log(`\n${index + 1}. 💼 LEAD #${lead.conversation_id}`);
        console.log('─'.repeat(50));
        
        // Información personal
        console.log(`👤 Nombre: ${lead.nombre_final || '❌ No disponible'}`);
        console.log(`📱 Teléfono: ${lead.telefono_final || '❌ No disponible'}`);
        console.log(`🎂 Edad: ${lead.edad_final || '❌ No disponible'}`);
        console.log(`🆔 Cédula: ${lead.cedula_final || '❌ No disponible'}`);
        
        // Información de la conversación
        console.log(`📞 Estado: ${lead.status || 'N/A'}`);
        console.log(`✅ Evaluación: ${lead.evaluation_result || 'N/A'}`);
        console.log(`🤖 Agente: ${lead.agent_id || 'N/A'}`);
        
        // Información adicional si está disponible
        if (lead.evaluation_rationale) {
          console.log(`💭 Razón: ${lead.evaluation_rationale.substring(0, 100)}${lead.evaluation_rationale.length > 100 ? '...' : ''}`);
        }
        
        if (lead.cliente_tipo) {
          console.log(`🏷️  Tipo Cliente: ${lead.cliente_tipo}`);
        }
      });

      console.log('\n' + '='.repeat(80));
      console.log(`📊 RESUMEN: ${effectiveLeads.length} leads efectivos encontrados`);
      
      // Estadísticas adicionales
      const leadsConNombre = effectiveLeads.filter(l => l.nombre_final).length;
      const leadsConTelefono = effectiveLeads.filter(l => l.telefono_final).length;
      const leadsConEdad = effectiveLeads.filter(l => l.edad_final).length;
      const leadsConCedula = effectiveLeads.filter(l => l.cedula_final).length;
      
      console.log(`👤 Con nombre: ${leadsConNombre} (${((leadsConNombre/effectiveLeads.length)*100).toFixed(1)}%)`);
      console.log(`📱 Con teléfono: ${leadsConTelefono} (${((leadsConTelefono/effectiveLeads.length)*100).toFixed(1)}%)`);
      console.log(`🎂 Con edad: ${leadsConEdad} (${((leadsConEdad/effectiveLeads.length)*100).toFixed(1)}%)`);
      console.log(`🆔 Con cédula: ${leadsConCedula} (${((leadsConCedula/effectiveLeads.length)*100).toFixed(1)}%)`);
      console.log('='.repeat(80));

      return effectiveLeads;
    } catch (error) {
      console.error('❌ Error mostrando leads:', error.message);
      throw error;
    }
  }
}

module.exports = LeadsService;