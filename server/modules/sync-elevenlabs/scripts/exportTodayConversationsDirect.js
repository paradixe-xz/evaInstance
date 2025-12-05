require('dotenv').config();
const fs = require('fs');
const path = require('path');
const ElevenLabsService = require('../services/elevenlabsService');
const { Op } = require('sequelize');
const { stringify } = require('csv-stringify/sync');

// Configuración
const EXPORT_DIR = path.resolve(__dirname, '..', '..', 'exports', 'conversations');
const AGENT_ID = process.env.AGENT_ID || 'agent_5901k74sdh0eedetx5q2fx3np14c';

// Crear instancia del servicio
const elevenLabsService = new ElevenLabsService();

// Función para obtener el rango de fechas desde .env
function getDateRange() {
  // Obtener fechas desde las variables de entorno
  const startDate = new Date(process.env.SYNC_START_DATE || '2024-11-12 00:00:00');
  const endDate = new Date(process.env.SYNC_END_DATE || '2024-11-12 23:59:59');
  
  console.log('📅 Rango de fechas configurado:');
  console.log(`   - Inicio: ${startDate.toISOString()} (${startDate.toLocaleString()})`);
  console.log(`   - Fin:    ${endDate.toISOString()} (${endDate.toLocaleString()})`);
  
  return { 
    start: startDate, 
    end: endDate,
    startUnix: Math.floor(startDate.getTime() / 1000),
    endUnix: Math.floor(endDate.getTime() / 1000)
  };
}

// Función para extraer texto del transcript
function extractTranscript(transcript) {
  if (!transcript) return '';
  
  if (Array.isArray(transcript)) {
    return transcript.map(item => {
      if (typeof item === 'string') return item;
      if (item.text) return item.text;
      if (item.content) return item.content;
      return JSON.stringify(item);
    }).join(' ');
  }
  
  if (typeof transcript === 'object') {
    if (transcript.text) return transcript.text;
    if (transcript.content) return transcript.content;
    return JSON.stringify(transcript);
  }
  
  return String(transcript);
}

// Función para guardar el audio
async function saveAudio(conversationId, audioData, exportDir) {
  if (!audioData) return '';
  
  try {
    const audioDir = path.join(exportDir, 'audios');
    await fs.promises.mkdir(audioDir, { recursive: true });
    
    const audioPath = path.join(audioDir, `${conversationId}.mp3`);
    await fs.promises.writeFile(audioPath, audioData);
    return audioPath;
  } catch (error) {
    console.error(`Error guardando audio para ${conversationId}:`, error.message);
    return '';
  }
}

// Función principal
async function exportTodayConversations() {
  try {
    const { start, end, startUnix, endUnix } = getDateRange();
    console.log(`📅 Exportando conversaciones del rango ${start.toLocaleString()} al ${end.toLocaleString()}...`);
    
    // Crear directorio de exportación
    await fs.promises.mkdir(EXPORT_DIR, { recursive: true });
    
    console.log(`🔍 Buscando conversaciones entre ${start.toLocaleString()} y ${end.toLocaleString()}...`);
    
    console.log('🔍 Obteniendo las conversaciones más recientes...');
    // Obtener conversaciones dentro del rango de fechas
    console.log(`🔍 Buscando conversaciones desde timestamp ${startUnix} (${new Date(startUnix * 1000).toISOString()})`);
    const conversationsData = await elevenLabsService.getAllConversations(AGENT_ID, startUnix);
    let conversations = conversationsData.conversations || [];
    
    console.log(`✅ Se encontraron ${conversations.length} conversaciones recientes.`);
    
    console.log(`✅ Se encontraron ${conversations.length} conversaciones.`);
    
    if (conversations.length === 0) {
      console.log('No hay conversaciones para exportar.');
      return;
    }
    
    // Crear array para los datos CSV
    const csvData = [
      ['ID', 'Número', 'Estado', 'Fecha', 'Duración (s)', 'Transcripción', 'Audio']
    ];

    // Procesar cada conversación
    for (const [index, conv] of conversations.entries()) {
      try {
        console.log(`\n📝 Procesando conversación ${index + 1}/${conversations.length}: ${conv.conversation_id}`);

        // Obtener detalles completos de la conversación
        const details = await elevenLabsService.getConversationDetails(conv.conversation_id);

        // Extraer información relevante con manejo de errores
        const transcriptText = extractTranscript(details.transcript);
        
        // Manejo seguro de fechas
        let callDate = new Date();
        let dateIsValid = false;
        
        try {
          if (details.created_at) {
            // Si es un timestamp en segundos
            callDate = new Date(details.created_at * 1000);
            dateIsValid = !isNaN(callDate.getTime());
          }
        } catch (e) {
          console.log(`   ⚠️  Error en formato de fecha: ${details.created_at}`);
        }
        
        if (!dateIsValid) {
          // Usar la fecha actual si no hay fecha válida
          callDate = new Date();
          console.log(`   ℹ️  Usando fecha actual para conversación sin fecha válida`);
        }

        // Obtener audio si está disponible
        let audioPath = '';
        if (details.recording_url) {
          console.log('   🎧 Descargando audio...');
          try {
            const audioResponse = await fetch(details.recording_url);
            const audioData = await audioResponse.buffer();
            audioPath = await saveAudio(conv.conversation_id, audioData, EXPORT_DIR);
            console.log(`   ✅ Audio guardado en: ${audioPath}`);
          } catch (error) {
            console.error('   ❌ Error descargando audio:', error.message);
          }
        }

        // Agregar fila al CSV
        csvData.push([
          conv.conversation_id || 'N/A',
          details.metadata?.phone_call?.external_number || 'N/A',
          details.analysis?.call_successful || 'unknown',
          dateIsValid ? callDate.toISOString() : 'Fecha no disponible',
          details.duration_seconds || 0,
          transcriptText ? JSON.stringify(transcriptText).replace(/\n/g, ' ').replace(/\r/g, ' ') : 'Sin transcripción',
          audioPath || 'No disponible'
        ]);

        console.log(`   ✅ Procesada correctamente`);

      } catch (error) {
        console.error(`   ❌ Error procesando conversación ${conv.conversation_id}:`, error.message);
      }
    }

    // Crear archivo CSV
    const csvContent = stringify(csvData, {
      quoted: true,
      quotedEmpty: true,
      delimiter: ';'
    });

    const csvPath = path.join(EXPORT_DIR, `conversaciones_${start.toISOString().split('T')[0]}.csv`);
    await fs.promises.writeFile(csvPath, csvContent, 'utf8');

    console.log(`\n✅ Exportación completada: ${csvPath}`);
    
  } catch (error) {
    console.error('❌ Error en la exportación:', error);
  }
}

// Ejecutar
if (require.main === module) {
  exportTodayConversations().catch(console.error);
}

module.exports = { exportTodayConversations };
