require('dotenv').config();
const fs = require('fs');
const path = require('path');
const { Sequelize, Op } = require('sequelize');
const Conversation = require('../models/Conversation');

// Configuración de la base de datos
const sequelize = new Sequelize({
  dialect: 'postgres',
  host: process.env.DB_HOST || 'localhost',
  port: process.env.DB_PORT || 5432,
  database: process.env.DB_NAME || 'elevenlabs_conversations',
  username: process.env.DB_USER || 'sync_user',
  password: process.env.DB_PASSWORD || 'postgreSQL23c',
  logging: false
});

// Función para exportar conversaciones de hoy
async function exportTodayConversations() {
  try {
    // Conectar a la base de datos
    await sequelize.authenticate();
    console.log('✅ Conexión a la base de datos establecida correctamente.');

    // Obtener las 50 conversaciones más recientes
    console.log('📅 Buscando las conversaciones más recientes...');

    const conversations = await Conversation.findAll({
      order: [['conversation_id', 'DESC']],
      limit: 50  // Limitar a las 50 conversaciones más recientes
    });
    
    console.log(`✅ Se encontraron ${conversations.length} conversaciones recientes.`);

    if (conversations.length === 0) {
      console.log('No hay conversaciones para exportar.');
      return;
    }

    // Crear directorio de exportación si no existe
    const exportDir = path.resolve(__dirname, '..', '..', 'exports');
    await fs.promises.mkdir(exportDir, { recursive: true });

    // Función para formatear la fecha en el nombre del archivo
    const formatDateForFilename = (date) => {
      return date.toISOString()
        .replace(/[:.]/g, '-')
        .replace('T', '_')
        .substring(0, 19);
    };

    // 1. Exportar a CSV
    const csvFileName = `conversations_${formatDateForFilename(today)}.csv`;
    const csvFilePath = path.join(exportDir, csvFileName);
    
    // Función para escapar valores CSV
    const escapeCsvValue = (value) => {
      if (value === null || value === undefined) return '';
      const str = String(value);
      if (typeof value === 'object') {
        try {
          return JSON.stringify(value)
            .replace(/"/g, '""')
            .replace(/\n/g, '\\n')
            .replace(/\r/g, '\\r');
        } catch (e) {
          return str.replace(/"/g, '""');
        }
      }
      return str.includes(',') || str.includes('"') || str.includes('\n') 
        ? `"${str.replace(/"/g, '""')}"` 
        : str;
    };

    // Definir las columnas del CSV
    const headers = [
      'id',
      'conversation_id',
      'agent_id',
      'lead_number',
      'status',
      'createdAt',
      'transcript_text',
      'evaluation_criteria_result',
      'evaluation_criteria_rationale'
    ];

    // Generar líneas del CSV
    const csvLines = [headers.join(',')];
    
    for (const conv of conversations) {
      const row = headers.map(header => {
        // Procesar el transcript para obtener texto plano
        if (header === 'transcript_text') {
          if (!conv.transcript) return '';
          
          if (Array.isArray(conv.transcript)) {
            return escapeCsvValue(conv.transcript
              .map(t => typeof t === 'string' ? t : (t.text || JSON.stringify(t)))
              .join(' ')
            );
          } else if (typeof conv.transcript === 'object') {
            return escapeCsvValue(JSON.stringify(conv.transcript, null, 2));
          } else {
            return escapeCsvValue(String(conv.transcript));
          }
        }
        
        // Para otros campos, usar el valor directamente
        return escapeCsvValue(conv[header]);
      });
      
      csvLines.push(row.join(','));
    }

    // Escribir archivo CSV
    await fs.promises.writeFile(csvFilePath, csvLines.join('\n'), 'utf8');
    console.log(`📊 Datos exportados a CSV: ${csvFilePath}`);

    // 2. Exportar a JSON
    const jsonFileName = `conversations_${formatDateForFilename(today)}.json`;
    const jsonFilePath = path.join(exportDir, jsonFileName);
    
    // Preparar datos para JSON
    const jsonData = conversations.map(conv => ({
      id: conv.id,
      conversation_id: conv.conversation_id,
      agent_id: conv.agent_id,
      lead_number: conv.lead_number,
      status: conv.status,
      createdAt: conv.createdAt,
      transcript: conv.transcript,
      evaluation_criteria_result: conv.evaluation_criteria_result,
      evaluation_criteria_rationale: conv.evaluation_criteria_rationale,
      // Incluir otros campos según sea necesario
    }));

    // Escribir archivo JSON
    await fs.promises.writeFile(jsonFilePath, JSON.stringify(jsonData, null, 2), 'utf8');
    console.log(`📋 Datos completos exportados a JSON: ${jsonFilePath}`);

    console.log('✅ Exportación completada exitosamente.');

  } catch (error) {
    console.error('❌ Error durante la exportación:', error);
  } finally {
    // Cerrar la conexión a la base de datos
    await sequelize.close();
  }
}

// Ejecutar la función principal
exportTodayConversations().catch(console.error);
